const API_URL = "https://rental-management-project.onrender.com";
let paymentModal;

// Format tiền VNĐ
const fmtMoney = (amount) => new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(amount);

// Toast notification
function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `<div style="display: flex; align-items: center; gap: 12px;"><span>${type === 'success' ? '✅' : '❌'}</span><span>${message}</span></div>`;
    document.getElementById('toastContainer').appendChild(toast);
    setTimeout(() => toast.remove(), 4000);
}

// ============================================================
// 1. QUẢN LÝ TÀI SẢN
// ============================================================
async function loadProperties() {
    try {
        const filterCat = document.getElementById("filterCategory")?.value || "";
        const res = await fetch(`${API_URL}/properties/`);
        if (!res.ok) return showToast("Lỗi kết nối Backend", "error");

        const data = await res.json();
        const listBody = document.getElementById("propertyList");
        const selectBox = document.getElementById("contractPropId");
        
        listBody.innerHTML = "";
        selectBox.innerHTML = `<option value="">-- Chọn tài sản --</option>`;

        const filteredData = Array.isArray(data) ? data.filter(p => !filterCat || p.category === filterCat) : [];
        document.getElementById("totalProperties").innerText = filteredData.length;

        if (filteredData.length === 0) {
            listBody.innerHTML = `<tr><td colspan="5" class="text-center text-muted py-4">Chưa có tài sản nào</td></tr>`;
        } else {
            filteredData.forEach(prop => {
                const imgHtml = prop.image_url 
                    ? `<img src="${prop.image_url}" class="property-img" onerror="this.src='https://via.placeholder.com/60?text=Img'">`
                    : `<div class="icon-lg">${prop.category === "vehicle" ? "🚗" : prop.category === "item" ? "📦" : "🏠"}</div>`;
                
                const badge = prop.status === "available" 
                    ? `<span class="badge badge-success">Sẵn sàng</span>` 
                    : `<span class="badge badge-secondary">Đang thuê</span>`;

                listBody.innerHTML += `
                    <tr>
                        <td>${imgHtml}</td>
                        <td><div style="font-weight: 600;">${prop.name}</div><div style="font-size: 12px; color: #6b7280;">${prop.address}</div></td>
                        <td class="text-end" style="color: #667eea; font-weight: 600;">${fmtMoney(prop.price)}</td>
                        <td class="text-center">${badge}</td>
                        <td class="text-center"><button class="btn btn-sm btn-danger" onclick="deleteProperty(${prop.id})"><i class="fas fa-trash"></i></button></td>
                    </tr>`;

                if (prop.status === "available") {
                    selectBox.innerHTML += `<option value="${prop.id}" data-price="${prop.price}">${prop.name} - ${fmtMoney(prop.price)}/ngày</option>`;
                }
            });
        }
    } catch (err) { console.error(err); showToast("Lỗi tải dữ liệu", "error"); }
}

document.getElementById("propertyForm")?.addEventListener("submit", async e => {
    e.preventDefault();
    const payload = {
        name: document.getElementById("propName").value,
        address: document.getElementById("propAddress").value,
        price: Number(document.getElementById("propPrice").value),
        category: document.getElementById("propCategory").value,
        image_url: document.getElementById("propImage").value || null
    };
    try {
        const res = await fetch(`${API_URL}/properties/`, {
            method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload)
        });
        if (res.ok) { showToast("✅ Đã thêm tài sản mới!"); e.target.reset(); loadProperties(); }
        else showToast("Lỗi thêm tài sản", "error");
    } catch (err) { console.error(err); }
});

async function deleteProperty(id) {
    if (!confirm("Xóa tài sản này?")) return;
    try {
        const res = await fetch(`${API_URL}/properties/${id}`, { method: "DELETE" });
        if (res.ok) { showToast("✅ Đã xóa tài sản"); loadProperties(); loadContracts(); }
    } catch (err) { console.error(err); }
}

// ============================================================
// 2. QUẢN LÝ HỢP ĐỒNG
// ============================================================
function calculateTotal() {
    const propSelect = document.getElementById("contractPropId");
    const option = propSelect?.options[propSelect.selectedIndex];
    const price = Number(option?.dataset.price || 0);
    const start = document.getElementById("startDate")?.value;
    const end = document.getElementById("endDate")?.value;
    const rentalType = document.querySelector('input[name="rentalType"]:checked')?.value || "daily";
    const display = document.getElementById("previewTotal");

    if (!price || !start || !end) return display ? display.innerText = "0 đ" : null;

    const days = Math.ceil((new Date(end) - new Date(start)) / (1000 * 60 * 60 * 24));
    if (days <= 0) return display ? display.innerText = "Ngày không hợp lệ" : null;

    let total = rentalType === "daily" ? days * price : Math.max(1, Math.ceil((days + 15) / 30)) * price;
    if (display) display.innerText = fmtMoney(total);
}

async function loadContracts() {
    try {
        const res = await fetch(`${API_URL}/contracts/`);
        if (!res.ok) return;
        const data = await res.json();
        const list = document.getElementById("contractList");
        list.innerHTML = "";
        let totalRevenue = 0;

        if (!Array.isArray(data) || data.length === 0) {
            list.innerHTML = `<div class="text-center text-muted py-4">📋 Chưa có hợp đồng nào</div>`;
        } else {
            for (const c of data) {
                let paid = 0;
                try {
                    const payRes = await fetch(`${API_URL}/contracts/${c.id}/payments`);
                    if (payRes.ok) paid = (await payRes.json()).reduce((s, p) => s + p.amount, 0);
                } catch (e) {}
                
                totalRevenue += paid;
                const percent = Math.min(100, (paid / (c.total_price || 1)) * 100);
                
                // ✅ HIỂN THỊ EMAIL KHÁCH
                const tenantEmail = c.tenant ? c.tenant.email : 'Không có email';

                list.innerHTML += `
                    <div class="contract-item" onclick="openPaymentModal(${c.id}, '${c.status}')">
                        <div class="contract-item-header">
                            <div class="contract-item-title">HĐ #${c.id}</div>
                            <span class="badge badge-success">${c.status}</span>
                        </div>
                        
                        <div style="font-size: 13px; color: #4b5563; margin-bottom: 8px; font-weight: 500;">
                            <i class="fas fa-user-circle" style="color: #667eea;"></i> ${tenantEmail}
                        </div>

                        <div class="contract-item-dates"><i class="fas fa-calendar"></i> ${c.start_date} → ${c.end_date}</div>
                        <div class="contract-item-row"><span class="contract-item-label">Tổng tiền:</span><span class="contract-item-value">${fmtMoney(c.total_price)}</span></div>
                        <div class="contract-item-row"><span class="contract-item-label">Đã thu:</span><span class="contract-item-value" style="color: #10b981;">${fmtMoney(paid)}</span></div>
                        <div class="progress"><div class="progress-bar" style="background-color: ${paid >= c.total_price ? '#10b981' : '#f59e0b'}; width: ${percent}%"></div></div>
                        <div style="display: flex; gap: 6px;">
                            <button class="btn btn-primary w-100 btn-sm" onclick="openPaymentModal(${c.id}, '${c.status}'); event.stopPropagation();"><i class="fas fa-plus"></i> Nộp</button>
                            <button class="btn btn-info w-100 btn-sm" onclick="downloadContractPDF(${c.id}); event.stopPropagation();"><i class="fas fa-download"></i> PDF</button>
                        </div>
                    </div>`;
            }
        }
        document.getElementById("totalContracts").innerText = data.length;
        document.getElementById("totalRevenue").innerText = fmtMoney(totalRevenue);
    } catch (err) { console.error(err); }
}

document.getElementById("contractForm")?.addEventListener("submit", async e => {
    e.preventDefault();
    const payload = {
        property_id: Number(document.getElementById("contractPropId").value),
        tenant_email: document.getElementById("contractEmail").value,
        start_date: document.getElementById("startDate").value,
        end_date: document.getElementById("endDate").value,
        deposit: Number(document.getElementById("deposit").value) || 0,
        rental_type: document.querySelector('input[name="rentalType"]:checked').value
    };
    try {
        const res = await fetch(`${API_URL}/contracts/`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
        if (res.ok) { showToast("✅ Ký hợp đồng thành công!"); e.target.reset(); loadProperties(); loadContracts(); }
        else { const err = await res.json(); showToast("❌ " + (err.detail || "Lỗi"), "error"); }
    } catch (err) { console.error(err); }
});

function downloadContractPDF(id) { window.open(`${API_URL}/contracts/${id}/download`, '_blank'); }

// ============================================================
// 3. MODAL THANH TOÁN & HƯ HỎNG
// ============================================================
function initPaymentModal() {
    const el = document.getElementById("paymentModal");
    if (el) paymentModal = new bootstrap.Modal(el);
}

async function openPaymentModal(cid, status) {
    document.getElementById("modalContractIdDisplay").innerText = "#" + cid;
    document.getElementById("payContractId").value = cid;
    document.getElementById("modalContractStatus").innerText = status;
    document.getElementById("payDate").valueAsDate = new Date();
    document.getElementById("damageDate").valueAsDate = new Date();

    let totalPrice = 0, paid = 0;
    try {
        const cRes = await fetch(`${API_URL}/contracts/`);
        const contracts = await cRes.json();
        const contract = contracts.find(c => c.id === cid);
        if (contract) totalPrice = contract.total_price;
        
        const pRes = await fetch(`${API_URL}/contracts/${cid}/payments`);
        const payments = await pRes.json();
        const tbody = document.getElementById("paymentHistoryList");
        tbody.innerHTML = "";
        
        if (payments.length === 0) tbody.innerHTML = "<tr><td colspan='4' class='text-center text-muted'>Chưa có giao dịch</td></tr>";
        else {
            paid = payments.reduce((s, p) => s + p.amount, 0);
            payments.forEach(p => {
                tbody.innerHTML += `<tr><td><small>${p.payment_date}</small></td><td><small>${p.note || '-'}</small></td><td class="text-end text-success">+${fmtMoney(p.amount)}</td><td class="text-center"><button class="btn btn-sm btn-danger" onclick="deletePayment(${p.id}, ${cid})"><i class="fas fa-trash"></i></button></td></tr>`;
            });
        }
    } catch (e) {}

    const remaining = Math.max(0, totalPrice - paid);
    document.getElementById('totalPriceDisplay').innerText = fmtMoney(totalPrice);
    document.getElementById('paidDisplay').innerText = fmtMoney(paid);
    document.getElementById('remainingDisplay').innerText = fmtMoney(remaining);
    
    const statusMsg = document.getElementById('paymentStatus');
    const payInput = document.getElementById('payAmount');
    if (remaining === 0) {
        statusMsg.innerHTML = '✅ Đã thanh toán đủ!'; statusMsg.style.background = '#d1fae5'; statusMsg.style.color = '#065f46';
        payInput.value = '';
    } else {
        statusMsg.innerHTML = `💡 Còn thiếu <strong>${fmtMoney(remaining)}</strong>`; statusMsg.style.background = '#fef08a'; statusMsg.style.color = '#854d0e';
        payInput.value = remaining;
    }

    loadDamages(cid);
    if (paymentModal) paymentModal.show();
}

document.getElementById("paymentForm")?.addEventListener("submit", async e => {
    e.preventDefault();
    const cid = document.getElementById("payContractId").value;
    const payload = {
        contract_id: Number(cid),
        amount: Number(document.getElementById("payAmount").value),
        payment_date: document.getElementById("payDate").value,
        note: document.getElementById("payNote").value
    };
    try {
        const res = await fetch(`${API_URL}/payments/`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
        if (res.ok) { showToast("✅ Đã thanh toán"); document.getElementById("payAmount").value = ""; openPaymentModal(cid); loadContracts(); }
    } catch (e) { showToast("Lỗi thanh toán", "error"); }
});

async function deletePayment(pid, cid) {
    if (!confirm("Xóa thanh toán này?")) return;
    await fetch(`${API_URL}/payments/${pid}`, { method: "DELETE" });
    openPaymentModal(cid); loadContracts();
}

// --- DAMAGE LOGIC ---
async function loadDamages(cid) {
    const list = document.getElementById('damageList');
    list.innerHTML = '';
    try {
        const res = await fetch(`${API_URL}/contracts/${cid}/damages`);
        const damages = await res.json();
        if (damages.length === 0) return list.innerHTML = '<div class="text-center text-muted py-3">✅ Không có hư hỏng</div>';
        
        damages.forEach(d => {
            const color = d.status === 'pending' ? '#f59e0b' : '#10b981';
            list.innerHTML += `
                <div style="background: white; border-left: 4px solid ${color}; padding: 10px; margin-bottom: 8px; border-radius: 4px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                    <div class="d-flex justify-content-between"><strong>${d.description}</strong><span style="color:${color}; font-weight:bold; font-size:11px;">${d.status.toUpperCase()}</span></div>
                    <div class="d-flex justify-content-between text-muted" style="font-size:12px;"><span>${d.reported_date}</span><span class="text-danger fw-bold">-${fmtMoney(d.repair_cost)}</span></div>
                    <div class="mt-2 d-flex gap-2">
                        ${d.status === 'pending' ? `<button class="btn btn-sm btn-outline-success py-0" onclick="markRepaired(${d.id}, ${cid})">Đã sửa</button>` : ''}
                        <button class="btn btn-sm btn-outline-danger py-0" onclick="deleteDamage(${d.id}, ${cid})">Xóa</button>
                    </div>
                </div>`;
        });
    } catch (e) {}
}

document.getElementById('damageForm')?.addEventListener('submit', async e => {
    e.preventDefault();
    const cid = parseInt(document.getElementById('payContractId').value);
    
    // Lấy property_id từ contract (cần fetch contract trước)
    let propId = 0;
    const cRes = await fetch(`${API_URL}/contracts/`);
    const contracts = await cRes.json();
    const contract = contracts.find(c => c.id === cid);
    if(contract) propId = contract.property_id;

    const payload = {
        contract_id: cid,
        property_id: propId,
        description: document.getElementById('damageDesc').value,
        severity: document.getElementById('damageSeverity').value,
        repair_cost: Number(document.getElementById('repairCost').value),
        reported_date: document.getElementById('damageDate').value
    };

    const res = await fetch(`${API_URL}/damage-reports/`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
    if (res.ok) { showToast('✅ Đã báo cáo'); e.target.reset(); loadDamages(cid); }
});

async function markRepaired(did, cid) {
    await fetch(`${API_URL}/damage-reports/${did}/mark-repaired`, { method: 'PATCH' });
    loadDamages(cid);
}

async function deleteDamage(did, cid) {
    if(!confirm('Xóa báo cáo này?')) return;
    await fetch(`${API_URL}/damage-reports/${did}`, { method: 'DELETE' });
    loadDamages(cid);
}

// START
window.addEventListener('DOMContentLoaded', () => {
    initPaymentModal();
    loadProperties();
    loadContracts();
    setInterval(loadContracts, 30000);
});
