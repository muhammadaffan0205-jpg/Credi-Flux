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
from repositories.user_repo import UserRepo
from utils.balance_utils import get_global_balance_summary
from utils.encryption import encrypt, decrypt

app = Flask(__name__, static_folder='../frontend', static_url_path='')
CORS(app)
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'CrediFluxSuperSecretKey2025!LongEnough32Chars')
jwt = JWTManager(app)

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
        access_token = create_access_token(identity=result.user_id)
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
        access_token = create_access_token(identity=result.user_id)
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
    confirmations = PaymentConfirmationManager.get_pending_for_user(user.user_id)
    debt_requests = DebtManager.get_pending_requests(user.user_id)
    recent_trans = TransactionManager.get_history(user.user_id, limit=5)
    total_owed = sum(a for d, c, a in settlements if d == user.username)
    total_to_collect = sum(a for d, c, a in settlements if c == user.username)
    return jsonify({
        'totalOwed': total_owed,
        'totalToCollect': total_to_collect,
        'settlements': formatted_settlements,
        'paymentConfirmations': [{'id': c['id'], 'debtorName': c['debtor_name'], 'amount': float(c['amount'])} for c in confirmations],
        'debtRequests': [{'id': r['id'], 'fromUsername': r['from_username'], 'amount': float(r['amount'])} for r in debt_requests],
        'recentTransactions': [{'date': t.txn_date.strftime('%Y-%m-%d'), 'description': t.description, 'amount': t.amount, 'paidTo': t.paid_to} for t in recent_trans]
    })

# ---------- Groups ----------
@app.route('/api/groups', methods=['GET', 'POST'])
@jwt_required()
def groups():
    user = get_current_user()
    if request.method == 'GET':
        groups = GroupManager.get_user_groups(user.user_id)
        return jsonify([{'id': g.group_id, 'name': g.group_name, 'memberCount': g.member_count} for g in groups])
    else:
        data = request.json
        name = data.get('name')
        if not name:
            return jsonify({'success': False, 'message': 'Group name required'}), 400
        group = GroupManager.create(name, user.user_id)
        if group:
            return jsonify({'success': True, 'group': {'id': group.group_id, 'name': group.group_name}})
        return jsonify({'success': False, 'message': 'Failed to create group'}), 500

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

@app.route('/api/settlements/<int:groupId>', methods=['GET'])
@jwt_required()
def get_settlements(groupId):
    settlements = ExpenseManager.get_balance_summary(groupId)
    return jsonify([{'debtor': d, 'creditor': c, 'amount': a} for d, c, a in settlements])

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
    if direction == 'owe':
        success, msg = DebtManager.request_debt(user.user_id, phone, amount)
    else:
        other = UserRepo.get_by_phone(phone)
        if not other:
            return jsonify({'success': False, 'message': 'User not found'}), 404
        success, msg = DebtManager.request_debt(other.user_id, user.phone, amount)
    return jsonify({'success': success, 'message': msg})

@app.route('/api/debt/accept', methods=['POST'])
@jwt_required()
def accept_debt():
    data = request.json
    request_id = data.get('requestId')
    if not request_id:
        return jsonify({'success': False, 'message': 'Request ID required'}), 400
    success = DebtManager.accept_request(request_id)
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
    user_dict = user.__dict__
    user_dict['phone'] = encrypt(user_dict['phone'])
    if user_dict.get('easypaisa_num'):
        user_dict['easypaisa_num'] = encrypt(user_dict['easypaisa_num'])
    return jsonify(user_dict)

@app.route('/api/user/easypaisa', methods=['PUT'])
@jwt_required()
def update_easypaisa():
    user = get_current_user()
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