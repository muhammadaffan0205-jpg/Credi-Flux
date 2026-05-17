# backend/app.py
import os
import re
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from core.db_connection import init_schema, close_db
from managers.auth_manager import AuthManager
from managers.group_manager import GroupManager
from managers.expense_manager import ExpenseManager
from managers.settlement_manager import SettlementManager
from managers.transaction_manager import TransactionManager
from managers.debt_manager import DebtManager
from managers.payment_confirmation_manager import PaymentConfirmationManager
from managers.payment_reminder_manager import PaymentReminderManager
from managers.group_debt_manager import GroupDebtManager
from repositories.user_repo import UserRepo
from repositories.settlement_repo import SettlementRepo
from repositories.debt_repo import DebtRepo
from repositories.group_repo import GroupRepo
from utils.balance_utils import (
    get_global_balance_summary,
    get_group_balance_summary,
    get_optimized_amount_owed,
    get_optimized_amount_to_collect,
)
from utils.encryption import encrypt, decrypt

app = Flask(__name__, static_folder='../frontend', static_url_path='')
CORS(app)
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'CrediFluxSuperSecretKey2025!LongEnough32Chars')
jwt = JWTManager(app)

def _format_debt_request(r: dict) -> dict:
    debtor = r['debtor_username']
    creditor = r['creditor_username']
    amount = float(r['amount'])
    requester = r.get('requested_by_username') or debtor
    return {
        'id': r['id'],
        'kind': 'direct',
        'debtorUsername': debtor,
        'creditorUsername': creditor,
        'requestedByUsername': requester,
        'amount': amount,
        'message': f"{requester} sent a debt request: {debtor} owes {creditor} Rs. {amount} (double-click to accept)",
    }

def _format_group_debt_request(r: dict) -> dict:
    debtor = r['debtor_username']
    creditor = r['creditor_username']
    amount = float(r['amount'])
    requester = r.get('requested_by_username') or debtor
    group_name = r.get('group_name', 'Group')
    return {
        'id': r['id'],
        'kind': 'group',
        'groupId': r['group_id'],
        'groupName': group_name,
        'debtorUsername': debtor,
        'creditorUsername': creditor,
        'requestedByUsername': requester,
        'amount': amount,
        'message': (
            f"{requester} sent a group debt in {group_name}: "
            f"{debtor} owes {creditor} Rs. {amount} (double-click to accept)"
        ),
    }

def _compute_net_with_peer(user, peer_username: str) -> float:
    """Positive = user owes peer; negative = peer owes user."""
    peer = UserRepo.get_by_username(peer_username)
    if not peer:
        return 0.0
    owed = sum(float(d['amount']) for d in DebtRepo.list_accepted_owed_by(user.user_id) if d['to_user_id'] == peer.user_id)
    owed_to_me = sum(float(d['amount']) for d in DebtRepo.list_accepted_owed_to(user.user_id) if d['from_user_id'] == peer.user_id)
    for s in SettlementRepo.get_for_user(user.username):
        if s.creditor_name == peer_username:
            owed += float(s.amount)
    for s in SettlementRepo.get_owed_to_user(user.username):
        if s.debtor_name == peer_username:
            owed_to_me += float(s.amount)
    return round(owed - owed_to_me, 2)

def _build_optimized_obligations(user) -> tuple:
    """Pay/collect rows from global min-cash-flow (same as optimized debt graph)."""
    settlements = get_global_balance_summary(user)
    pay_actions = []
    collect_actions = []
    for debtor, creditor, amount in settlements:
        if debtor == user.username:
            cred = UserRepo.get_by_username(creditor)
            pay_actions.append({
                'kind': 'global',
                'creditorUsername': creditor,
                'amount': amount,
                'creditorPayNumber': cred.pay_number if cred else '',
                'sourceLabel': 'Optimized',
                'netPayment': True,
            })
        if creditor == user.username:
            collect_actions.append({
                'kind': 'global',
                'debtorUsername': debtor,
                'amount': amount,
                'sourceLabel': 'Optimized',
                'netPayment': True,
            })
    return pay_actions, collect_actions

def get_current_user():
    user_id = get_jwt_identity()
    if user_id is None:
        return None
    try:
        uid = int(user_id)
    except (TypeError, ValueError):
        return None
    return UserRepo.get_by_id(uid)

# Serve frontend
@app.route('/')
def index():
    return send_from_directory('../frontend', 'index.html')

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('../frontend', path)

# ---------- Auth ----------
@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    full_name = data.get('fullName')
    username = data.get('username')
    phone_encrypted = data.get('phone')
    password = data.get('password')
    phone = decrypt(phone_encrypted)
    if not all([full_name, username, phone, password]):
        return jsonify({'success': False, 'message': 'All fields required'}), 400
    if not re.match(r'^[0-9]{10,13}$', phone):
        return jsonify({'success': False, 'message': 'Invalid phone number'}), 400
    success, result = AuthManager.register(full_name, username, phone, password)
    print(f"[DEBUG] Registration result: success={success}, result={result}")  # <-- ADD THIS
    if success:
        # PyJWT requires JWT "sub" to be a string; identity must not be a bare int.
        access_token = create_access_token(identity=str(result.user_id))
        user_dict = result.__dict__
        user_dict['phone'] = encrypt(user_dict['phone'])
        if user_dict.get('easypaisa_num'):
            user_dict['easypaisa_num'] = encrypt(user_dict['easypaisa_num'])
        return jsonify({'success': True, 'token': access_token, 'user': user_dict})
    return jsonify({'success': False, 'message': result}), 400

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    success, result = AuthManager.login(username, password)
    if success:
        access_token = create_access_token(identity=str(result.user_id))
        user_dict = result.__dict__
        user_dict['phone'] = encrypt(user_dict['phone'])
        if user_dict.get('easypaisa_num'):
            user_dict['easypaisa_num'] = encrypt(user_dict['easypaisa_num'])
        return jsonify({'success': True, 'token': access_token, 'user': user_dict})
    return jsonify({'success': False, 'message': result}), 401

# ---------- Dashboard ----------
@app.route('/api/dashboard', methods=['GET'])
@jwt_required()
def dashboard():
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'message': 'User not found'}), 404
    settlements = get_global_balance_summary(user)
    formatted_settlements = [{'debtor': d, 'creditor': c, 'amount': a} for d, c, a in settlements]

    pay_actions, collect_actions = _build_optimized_obligations(user)
    payment_due_alerts = PaymentReminderManager.get_due_alerts_for_debtor(user.user_id)

    confirmations = PaymentConfirmationManager.get_pending_for_user(user.user_id)
    direct_requests = DebtManager.get_pending_requests(user.user_id)
    group_requests = GroupDebtManager.get_pending_for_user(user.user_id)
    debt_requests = (
        [_format_debt_request(r) for r in direct_requests]
        + [_format_group_debt_request(r) for r in group_requests]
    )
    recent_trans = TransactionManager.get_history(user.user_id, limit=5)
    total_owed = sum(a for d, c, a in settlements if d == user.username)
    total_to_collect = sum(a for d, c, a in settlements if c == user.username)
    return jsonify({
        'totalOwed': total_owed,
        'totalToCollect': total_to_collect,
        'settlements': formatted_settlements,
        'payActions': pay_actions,
        'collectActions': collect_actions,
        'paymentDueAlerts': payment_due_alerts,
        'paymentConfirmations': [{'id': c['id'], 'debtorName': c['debtor_name'], 'amount': float(c['amount'])} for c in confirmations],
        'debtRequests': debt_requests,
        'recentTransactions': [{'date': t.txn_date.strftime('%Y-%m-%d'), 'description': t.description, 'amount': t.amount, 'paidTo': t.paid_to} for t in recent_trans]
    })

# ---------- Groups ----------
@app.route('/api/groups', methods=['GET', 'POST'])
@jwt_required()
def groups():
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'message': 'User not found'}), 404
    if request.method == 'GET':
        groups = GroupManager.get_user_groups(user.user_id)
        return jsonify([{'id': g.group_id, 'name': g.group_name, 'memberCount': g.member_count} for g in groups])
    else:
        data = request.json or {}
        name = (data.get('name') or '').strip()
        if not name:
            return jsonify({'success': False, 'message': 'Group name required'}), 400
        group, err = GroupManager.create(name, user.user_id)
        if group:
            return jsonify({'success': True, 'group': {'id': group.group_id, 'name': group.group_name}})
        return jsonify({'success': False, 'message': err or 'Failed to create group'}), 500

@app.route('/api/groups/<int:groupId>/members', methods=['GET', 'POST'])
@jwt_required()
def group_members(groupId):
    if request.method == 'GET':
        # Get members list
        people = GroupManager.get_people(groupId)
        return jsonify([{'person_id': p.person_id, 'display_name': p.display_name, 'user_id': p.user_id} for p in people])
    else:
        # Add member
        data = request.json
        display_name = data.get('displayName')
        if not display_name:
            return jsonify({'success': False, 'message': 'Name required'}), 400
        success, msg = GroupManager.add_member(groupId, display_name)
        return jsonify({'success': success, 'message': msg})

@app.route('/api/groups/<int:groupId>/detail', methods=['GET'])
@jwt_required()
def group_detail(groupId):
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'message': 'User not found'}), 404
    member_ids = {p.user_id for p in GroupRepo.get_people(groupId)}
    if user.user_id not in member_ids:
        return jsonify({'success': False, 'message': 'Not a member of this group'}), 403
    settlements = get_group_balance_summary(groupId)
    members = []
    for p in GroupRepo.get_people(groupId):
        linked = UserRepo.get_by_id(p.user_id) if p.user_id else None
        members.append({
            'personId': p.person_id,
            'displayName': p.display_name,
            'userId': p.user_id,
            'username': linked.username if linked else None,
            'canReceiveRequest': bool(p.user_id),
        })
    return jsonify({
        'members': members,
        'settlements': [{'debtor': d, 'creditor': c, 'amount': a} for d, c, a in settlements],
    })

@app.route('/api/groups/<int:groupId>/debt/request', methods=['POST'])
@jwt_required()
def group_debt_request(groupId):
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'message': 'User not found'}), 404
    data = request.json or {}
    try:
        amount = float(data.get('amount'))
    except (TypeError, ValueError):
        return jsonify({'success': False, 'message': 'Invalid amount'}), 400
    member_user_id = data.get('memberUserId')
    direction = data.get('direction')
    if not member_user_id or amount <= 0:
        return jsonify({'success': False, 'message': 'Member and amount required'}), 400
    if not direction in ('owe', 'owed'):
        return jsonify({'success': False, 'message': 'Choose I owe them or They owe me'}), 400
    try:
        member_user_id = int(member_user_id)
    except (TypeError, ValueError):
        return jsonify({'success': False, 'message': 'Invalid member'}), 400
    success, msg = GroupDebtManager.create_request(
        groupId, user.user_id, member_user_id, amount, direction
    )
    return jsonify({'success': success, 'message': msg})

@app.route('/api/expenses', methods=['POST'])
@jwt_required()
def add_expense():
    data = request.json
    group_id = data.get('groupId')
    description = data.get('description')
    amount = data.get('amount')
    payer_names = data.get('payerNames')
    if not all([group_id, description, amount, payer_names]):
        return jsonify({'success': False, 'message': 'Missing fields'}), 400
    success, msg = ExpenseManager.add(group_id, description, str(amount), payer_names)
    return jsonify({'success': success, 'message': msg})

@app.route('/api/settlements', methods=['GET'])
@jwt_required()
def get_all_settlements():
    """Combined direct + group payment obligations (same data as dashboard payActions)."""
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'message': 'User not found'}), 404
    settlements = get_global_balance_summary(user)
    pay_actions, collect_actions = _build_optimized_obligations(user)
    total_owed = sum(a for d, c, a in settlements if d == user.username)
    total_to_collect = sum(a for d, c, a in settlements if c == user.username)
    return jsonify({
        'payActions': pay_actions,
        'collectActions': collect_actions,
        'totalOwed': total_owed,
        'totalToCollect': total_to_collect,
    })

@app.route('/api/settlements/<int:groupId>', methods=['GET'])
@jwt_required()
def get_settlements(groupId):
    rows = SettlementRepo.get_for_group(groupId)
    pending = [s for s in rows if not s.is_paid]
    out = []
    for s in pending:
        cred_u = UserRepo.get_by_username(s.creditor_name)
        out.append({
            'settlementId': s.settlement_id,
            'debtor': s.debtor_name,
            'creditor': s.creditor_name,
            'amount': float(s.amount),
            'groupId': s.group_id,
            'creditorPayNumber': cred_u.pay_number if cred_u else '',
        })
    return jsonify(out)

# ---------- Direct Debts ----------
@app.route('/api/debt/request', methods=['POST'])
@jwt_required()
def request_debt():
    user = get_current_user()
    data = request.json
    phone_encrypted = data.get('phone')
    amount = data.get('amount')
    direction = data.get('direction')
    phone = decrypt(phone_encrypted)
    if not phone or not amount:
        return jsonify({'success': False, 'message': 'Phone and amount required'}), 400
    try:
        amount = float(amount)
    except:
        return jsonify({'success': False, 'message': 'Invalid amount'}), 400
    if direction not in ('owe', 'owed'):
        return jsonify({'success': False, 'message': 'Choose I owe them or They owe me'}), 400
    success, msg = DebtManager.create_debt_request(user.user_id, phone, amount, direction)
    return jsonify({'success': success, 'message': msg})

@app.route('/api/debt/accept', methods=['POST'])
@jwt_required()
def accept_debt():
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'message': 'User not found'}), 404
    data = request.json
    request_id = data.get('requestId')
    kind = data.get('kind', 'direct')
    if not request_id:
        return jsonify({'success': False, 'message': 'Request ID required'}), 400
    if kind == 'group':
        success, msg = GroupDebtManager.accept_request(request_id, user.user_id)
        return jsonify({'success': success, 'message': msg})
    success = DebtManager.accept_request(request_id, user.user_id)
    return jsonify({'success': success})

# ---------- Payment Confirmations ----------
@app.route('/api/payment/confirm', methods=['POST'])
@jwt_required()
def confirm_payment():
    user = get_current_user()
    data = request.json
    confirmation_id = data.get('confirmationId')
    if not confirmation_id:
        return jsonify({'success': False, 'message': 'Confirmation ID required'}), 400
    success = PaymentConfirmationManager.confirm_payment(confirmation_id, user.user_id)
    return jsonify({'success': success})

@app.route('/api/payment/request', methods=['POST'])
@jwt_required()
def request_payment_confirmation():
    """Debtor notifies creditor they sent EasyPaisa; creates pending payment_confirmations row."""
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'message': 'User not found'}), 404
    data = request.json or {}
    creditor_username = data.get('creditorUsername')
    direct_debt_id = data.get('directDebtId')
    settlement_id = data.get('settlementId')
    try:
        amount = float(data.get('amount'))
    except (TypeError, ValueError):
        return jsonify({'success': False, 'message': 'Invalid amount'}), 400

    if not creditor_username or amount <= 0:
        return jsonify({'success': False, 'message': 'Creditor and amount required'}), 400

    creditor = UserRepo.get_by_username(creditor_username)
    if not creditor:
        return jsonify({'success': False, 'message': 'Creditor not found'}), 404

    sid = None
    did = None
    net_payment = data.get('netPayment')

    if net_payment:
        net = get_optimized_amount_owed(user, creditor.username)
        if net <= 0:
            return jsonify({'success': False, 'message': 'You do not owe this person anything'}), 400
        if abs(net - amount) > 0.02:
            return jsonify({'success': False, 'message': f'Optimized amount should be Rs. {net}'}), 400
    elif direct_debt_id is not None:
        debt = DebtRepo.get_by_id(int(direct_debt_id))
        if not debt or debt.get('status') != 'accepted':
            return jsonify({'success': False, 'message': 'Invalid direct debt'}), 400
        if debt['from_user_id'] != user.user_id or debt['to_user_id'] != creditor.user_id:
            return jsonify({'success': False, 'message': 'Debt does not match this payment'}), 400
        if abs(float(debt['amount']) - amount) > 0.02:
            return jsonify({'success': False, 'message': 'Amount does not match debt'}), 400
        did = int(direct_debt_id)
    elif settlement_id is not None:
        st = SettlementRepo.get_by_id(int(settlement_id))
        if not st or st.is_paid:
            return jsonify({'success': False, 'message': 'Invalid settlement'}), 400
        if st.debtor_name != user.username or st.creditor_name != creditor.username:
            return jsonify({'success': False, 'message': 'Settlement does not match'}), 400
        if abs(float(st.amount) - amount) > 0.02:
            return jsonify({'success': False, 'message': 'Amount does not match settlement'}), 400
        sid = int(settlement_id)
    else:
        return jsonify({'success': False, 'message': 'netPayment, directDebtId, or settlementId required'}), 400

    new_id = PaymentConfirmationManager.request_payment(user.user_id, creditor.user_id, amount, sid, did)
    if new_id:
        PaymentReminderManager.dismiss_after_payment(user.user_id, creditor.user_id, did, sid)
        return jsonify({'success': True, 'confirmationId': new_id})
    return jsonify({'success': False, 'message': 'Could not create confirmation'}), 500

@app.route('/api/payment/remind', methods=['POST'])
@jwt_required()
def send_payment_reminder():
    """Creditor requests payment from debtor; shows in debtor's Upcoming Due Dates."""
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'message': 'User not found'}), 404
    data = request.json or {}
    debtor_username = data.get('debtorUsername')
    try:
        amount = float(data.get('amount'))
    except (TypeError, ValueError):
        return jsonify({'success': False, 'message': 'Invalid amount'}), 400
    if not debtor_username or amount <= 0:
        return jsonify({'success': False, 'message': 'Debtor and amount required'}), 400
    net_payment = data.get('netPayment')
    if net_payment:
        net = get_optimized_amount_to_collect(user, debtor_username)
        if net <= 0:
            return jsonify({'success': False, 'message': 'This person does not owe you anything'}), 400
        if abs(net - amount) > 0.02:
            return jsonify({'success': False, 'message': f'Optimized amount should be Rs. {net}'}), 400
    success, msg = PaymentReminderManager.send_reminder(
        user.user_id,
        debtor_username,
        amount,
        data.get('directDebtId'),
        data.get('settlementId'),
        net_payment=bool(net_payment),
    )
    return jsonify({'success': success, 'message': msg})

# ---------- Transactions ----------
@app.route('/api/transactions', methods=['GET'])
@jwt_required()
def transactions():
    user = get_current_user()
    trans = TransactionManager.get_history(user.user_id, limit=200)
    return jsonify([{
        'date': t.txn_date.strftime('%Y-%m-%d'),
        'description': t.description,
        'group': t.group_id,
        'amount': t.amount,
        'paidTo': t.paid_to
    } for t in trans])

# ---------- Profile ----------
@app.route('/api/profile', methods=['GET'])
@jwt_required()
def profile():
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'message': 'User not found'}), 404
    payload = {
        'user_id': user.user_id,
        'full_name': user.full_name,
        'username': user.username,
        'phone': encrypt(user.phone),
        'easypaisa_num': encrypt(user.easypaisa_num) if user.easypaisa_num else None,
        'wallet_balance': float(user.wallet_balance),
    }
    if user.created_at:
        payload['created_at'] = user.created_at.isoformat()
    return jsonify(payload)

@app.route('/api/user/easypaisa', methods=['PUT'])
@jwt_required()
def update_easypaisa():
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'message': 'User not found'}), 404
    data = request.json
    ep_encrypted = data.get('easypaisaNum')
    ep_num = decrypt(ep_encrypted)
    if not ep_num:
        return jsonify({'success': False, 'message': 'Number required'}), 400
    success, msg = AuthManager.update_easypaisa(user.user_id, ep_num)
    return jsonify({'success': success, 'message': msg})

if __name__ == '__main__':
    init_schema()
    try:
        app.run(debug=True, host='0.0.0.0', port=5000)
    finally:
        close_db()