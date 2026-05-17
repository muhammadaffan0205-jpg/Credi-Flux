// crediflux_web/frontend/js/app.js
const API_BASE = 'http://localhost:5000/api';

// ---------- Caesar cipher (ROT13) ----------
const key = 'abcdefghijklmnopqrstuvwxyz';

function enc_substitution(n, plaintext) {
    let result = '';
    for (let l of plaintext.toLowerCase()) {
        let i = key.indexOf(l);
        if (i !== -1) {
            result += key[(i + n) % 26];
        } else {
            result += l;
        }
    }
    return result;
}

function dec_substitution(n, ciphertext) {
    let result = '';
    for (let l of ciphertext) {
        let i = key.indexOf(l);
        if (i !== -1) {
            result += key[(i - n + 26) % 26];
        } else {
            result += l;
        }
    }
    return result;
}

const SHIFT = 13;
function encrypt(text) { return enc_substitution(SHIFT, text); }
function decrypt(text) { return dec_substitution(SHIFT, text); }

// ---------- Auth helpers ----------
function getToken() {
    return localStorage.getItem('access_token');
}
function setToken(token) {
    localStorage.setItem('access_token', token);
}
function clearToken() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user');
}
function getCurrentUser() {
    const userStr = localStorage.getItem('user');
    return userStr ? JSON.parse(userStr) : null;
}

// ---------- API calls (all sensitive fields encrypted/decrypted) ----------
const API = {
    async login(username, password) {
        const res = await fetch(`${API_BASE}/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });
        const data = await res.json();
        if (data.success) {
            // Decrypt user fields that are encrypted
            if (data.user.phone) data.user.phone = decrypt(data.user.phone);
            if (data.user.easypaisa_num) data.user.easypaisa_num = decrypt(data.user.easypaisa_num);
            setToken(data.token);
            localStorage.setItem('user', JSON.stringify(data.user));
        }
        return data;
    },

    async register(fullName, username, phone, password) {
        const encryptedPhone = encrypt(phone);
        const res = await fetch(`${API_BASE}/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ fullName, username, phone: encryptedPhone, password })
        });
        const data = await res.json();
        if (data.success && data.user) {
            if (data.user.phone) data.user.phone = decrypt(data.user.phone);
            if (data.user.easypaisa_num) data.user.easypaisa_num = decrypt(data.user.easypaisa_num);
        }
        return data;
    },

    async getDashboardData() {
        const res = await fetch(`${API_BASE}/dashboard`, {
            headers: { 'Authorization': `Bearer ${getToken()}` }
        });
        const data = await res.json();
        // No sensitive fields in dashboard (only usernames and amounts)
        return data;
    },

    async getSettlementsData() {
        const res = await fetch(`${API_BASE}/settlements`, {
            headers: { 'Authorization': `Bearer ${getToken()}` }
        });
        return await res.json();
    },

    async createGroup(name) {
        const res = await fetch(`${API_BASE}/groups`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${getToken()}`
            },
            body: JSON.stringify({ name })
        });
        const data = await res.json().catch(() => ({}));
        if (!res.ok && !data.message) {
            data.success = false;
            data.message = `Could not create group (${res.status})`;
        }
        return data;
    },

    async getGroups() {
        const res = await fetch(`${API_BASE}/groups`, {
            headers: { 'Authorization': `Bearer ${getToken()}` }
        });
        return await res.json();
    },

    async addMember(groupId, displayName) {
        const res = await fetch(`${API_BASE}/groups/${groupId}/members`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${getToken()}`
            },
            body: JSON.stringify({ displayName })
        });
        return await res.json();
    },

    async addExpense(groupId, description, amount, payerNames) {
        const res = await fetch(`${API_BASE}/expenses`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${getToken()}`
            },
            body: JSON.stringify({ groupId, description, amount, payerNames })
        });
        return await res.json();
    },

    async getSettlements(groupId) {
        const res = await fetch(`${API_BASE}/settlements/${groupId}`, {
            headers: { 'Authorization': `Bearer ${getToken()}` }
        });
        return await res.json();
    },

    async requestDebt(phone, amount, direction) {
        const encryptedPhone = encrypt(phone);
        const res = await fetch(`${API_BASE}/debt/request`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${getToken()}`
            },
            body: JSON.stringify({ phone: encryptedPhone, amount, direction })
        });
        return await res.json();
    },

    async acceptDebtRequest(requestId, kind = 'direct') {
        const res = await fetch(`${API_BASE}/debt/accept`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${getToken()}`
            },
            body: JSON.stringify({ requestId, kind })
        });
        return await res.json();
    },

    async getGroupDetail(groupId) {
        const res = await fetch(`${API_BASE}/groups/${groupId}/detail`, {
            headers: { 'Authorization': `Bearer ${getToken()}` }
        });
        return await res.json();
    },

    async requestGroupDebt(groupId, memberUserId, amount, direction) {
        const res = await fetch(`${API_BASE}/groups/${groupId}/debt/request`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${getToken()}`
            },
            body: JSON.stringify({ memberUserId, amount, direction })
        });
        return await res.json();
    },

    async confirmPayment(confirmationId) {
        const res = await fetch(`${API_BASE}/payment/confirm`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${getToken()}`
            },
            body: JSON.stringify({ confirmationId })
        });
        return await res.json();
    },

    async requestPaymentConfirmation(ctx) {
        const res = await fetch(`${API_BASE}/payment/request`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${getToken()}`
            },
            body: JSON.stringify({
                creditorUsername: ctx.creditorUsername,
                amount: ctx.amount,
                directDebtId: ctx.directDebtId,
                settlementId: ctx.settlementId,
                netPayment: ctx.netPayment || false,
            }),
        });
        return await res.json();
    },

    async sendPaymentReminder(ctx) {
        const res = await fetch(`${API_BASE}/payment/remind`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${getToken()}`
            },
            body: JSON.stringify({
                debtorUsername: ctx.debtorUsername,
                amount: ctx.amount,
                directDebtId: ctx.directDebtId,
                settlementId: ctx.settlementId,
                netPayment: ctx.netPayment || false,
            }),
        });
        return await res.json();
    },

    async updateEasyPaisa(number) {
        const encrypted = encrypt(number);
        const res = await fetch(`${API_BASE}/user/easypaisa`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${getToken()}`
            },
            body: JSON.stringify({ easypaisaNum: encrypted })
        });
        const data = await res.json().catch(() => ({}));
        if (!res.ok) {
            return {
                success: false,
                message: data.message || data.msg || `Update failed (${res.status})`
            };
        }
        return data;
    },

    async getTransactions() {
        const res = await fetch(`${API_BASE}/transactions`, {
            headers: { 'Authorization': `Bearer ${getToken()}` }
        });
        return await res.json();
    },

    async getProfile() {
        const res = await fetch(`${API_BASE}/profile`, {
            headers: { 'Authorization': `Bearer ${getToken()}` }
        });
        const data = await res.json().catch(() => ({}));
        if (!res.ok) {
            if (res.status === 401) {
                clearToken();
                window.location.href = 'index.html';
            }
            return data;
        }
        if (data.phone) data.phone = decrypt(data.phone);
        if (data.easypaisa_num) data.easypaisa_num = decrypt(data.easypaisa_num);
        return data;
    }
};

// ---------- Shared payments table (dashboard + settlements) ----------
function renderObligationsTable(tbody, payList, collectList, openPayModalFn, onRequestFn) {
    tbody.innerHTML = '';
    (payList || []).forEach(pa => {
        const row = tbody.insertRow();
        const peerLabel = pa.sourceLabel
            ? `${pa.creditorUsername} (${pa.sourceLabel})`
            : pa.creditorUsername;
        row.insertCell(0).innerText = peerLabel;
        row.insertCell(1).innerText = `Rs. ${pa.amount}`;
        const actionCell = row.insertCell(2);
        const btn = document.createElement('button');
        btn.textContent = 'Pay Now';
        btn.className = 'btn-sm btn-green';
        btn.onclick = () => openPayModalFn(
            pa.creditorUsername,
            pa.amount,
            pa.creditorPayNumber || '',
            {
                directDebtId: pa.directDebtId,
                settlementId: pa.settlementId,
                netPayment: pa.netPayment || false,
            }
        );
        actionCell.appendChild(btn);
    });
    (collectList || []).forEach(ca => {
        const row = tbody.insertRow();
        const peerLabel = ca.sourceLabel
            ? `${ca.debtorUsername} (${ca.sourceLabel})`
            : ca.debtorUsername;
        row.insertCell(0).innerText = peerLabel;
        row.insertCell(1).innerText = `Rs. ${ca.amount}`;
        const actionCell = row.insertCell(2);
        const btn = document.createElement('button');
        btn.textContent = 'Request';
        btn.className = 'btn-sm btn-amber';
        btn.onclick = async () => {
            const res = await onRequestFn({
                debtorUsername: ca.debtorUsername,
                amount: ca.amount,
                directDebtId: ca.directDebtId,
                settlementId: ca.settlementId,
                netPayment: ca.netPayment || false,
            });
            alert(res.message || (res.success ? 'Request sent.' : 'Could not send request.'));
        };
        actionCell.appendChild(btn);
    });
}

// ---------- Draw debt graph (node + arrow) ----------
function drawDebtGraph(canvasId, settlements, currentUsername) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const width = canvas.clientWidth;
    const height = canvas.clientHeight;
    canvas.width = width;
    canvas.height = height;
    ctx.clearRect(0, 0, width, height);
    if (!settlements.length) {
        ctx.fillStyle = '#8B949E';
        ctx.font = '14px "Segoe UI"';
        ctx.fillText('No debts — all settled!', width / 2 - 80, height / 2);
        return;
    }
    const names = new Set();
    settlements.forEach(s => { names.add(s.debtor); names.add(s.creditor); });
    const nameList = Array.from(names);
    const n = nameList.length;
    const centerX = width / 2, centerY = height / 2;
    const radius = Math.min(width, height) * 0.35;
    const positions = {};
    nameList.forEach((name, i) => {
        const angle = (2 * Math.PI * i / n) - Math.PI / 2;
        positions[name] = { x: centerX + radius * Math.cos(angle), y: centerY + radius * Math.sin(angle) };
    });
    const nodeRadius = 26;
    const colours = ['#3FB950', '#58A6FF', '#E3B341', '#FF7B72', '#D2A8FF', '#79C0FF', '#00C896', '#F0883E'];
    settlements.forEach(s => {
        const from = positions[s.debtor];
        const to = positions[s.creditor];
        if (!from || !to) return;
        const dx = to.x - from.x, dy = to.y - from.y;
        const dist = Math.hypot(dx, dy);
        if (dist < 0.1) return;
        const ux = dx / dist, uy = dy / dist;
        const startX = from.x + ux * nodeRadius;
        const startY = from.y + uy * nodeRadius;
        const endX = to.x - ux * nodeRadius;
        const endY = to.y - uy * nodeRadius;
        ctx.beginPath();
        ctx.moveTo(startX, startY);
        ctx.lineTo(endX, endY);
        ctx.strokeStyle = '#00C896';
        ctx.lineWidth = 2;
        ctx.stroke();
        const angle = Math.atan2(dy, dx);
        const arrowSize = 10;
        ctx.beginPath();
        ctx.moveTo(endX, endY);
        ctx.lineTo(endX - arrowSize * Math.cos(angle - Math.PI / 6), endY - arrowSize * Math.sin(angle - Math.PI / 6));
        ctx.lineTo(endX - arrowSize * Math.cos(angle + Math.PI / 6), endY - arrowSize * Math.sin(angle + Math.PI / 6));
        ctx.fillStyle = '#00C896';
        ctx.fill();
        const midX = (startX + endX) / 2, midY = (startY + endY) / 2;
        ctx.font = 'bold 10px "Segoe UI"';
        ctx.fillStyle = '#E3B341';
        ctx.fillText(`Rs.${s.amount}`, midX + uy * 10, midY + ux * 10);
    });
    nameList.forEach(name => {
        const pos = positions[name];
        const colour = colours[nameList.indexOf(name) % colours.length];
        ctx.beginPath();
        ctx.arc(pos.x, pos.y, nodeRadius, 0, 2 * Math.PI);
        ctx.fillStyle = colour;
        ctx.fill();
        ctx.strokeStyle = '#161B22';
        ctx.lineWidth = 2;
        ctx.stroke();
        if (name === currentUsername) {
            ctx.beginPath();
            ctx.arc(pos.x, pos.y, nodeRadius + 2, 0, 2 * Math.PI);
            ctx.strokeStyle = '#FFFFFF';
            ctx.lineWidth = 2;
            ctx.stroke();
        }
        ctx.fillStyle = '#FFFFFF';
        ctx.font = 'bold 14px "Segoe UI"';
        const label = (name === currentUsername) ? 'You' : name.charAt(0).toUpperCase();
        ctx.fillText(label, pos.x - 7, pos.y + 5);
        ctx.font = '10px "Segoe UI"';
        ctx.fillStyle = '#E6EDF3';
        const displayName = (name === currentUsername) ? 'You' : name;
        ctx.fillText(displayName, pos.x - 20, pos.y + nodeRadius + 12);
    });
}