const API_URL = "http://localhost:8000";
const paymentModal = new bootstrap.Modal(document.getElementById('paymentModal'));

// --- 1. LOAD NHÀ & DOANH THU ---
async function loadProperties() {
    try {
        const res = await fetch(`${API_URL}/properties/`);
        const data = await res.json();
        const listBody = document.getElementById("propertyList");
        const selectBox = document.getElementById("contractPropId");
        
        listBody.innerHTML = "";
        selectBox.innerHTML = '<option value="">-- Chọn phòng --</option>';

        data.forEach(prop => {
            let badge = prop.status === 'available' 
                ? '<span class="badge bg-success">Trống</span>' 
                : '<span class="badge bg-secondary">Đã thuê</span>';
            
            listBody.innerHTML += `
                <tr>
                    <td><strong>${prop.name}</strong><br><small class="text-muted">${prop.address}</small></td>
                    <td class="text-primary fw-bold">${prop.price.toLocaleString()}</td>
                    <td>${badge}</td>
                </tr>
            `;

            if (prop.status === 'available') {
                selectBox.innerHTML += `<option value="${prop.id}">${prop.name} - ${prop.price}đ</option>`;
            }
        });
    } catch (e) { console.error(e); }
}

// --- 2. LOAD HỢP ĐỒNG ---
async function loadContracts() {
    try {
        const res = await fetch(`${API_URL}/contracts/`);
        const data = await res.json();
        const list = document.getElementById("contractList");
        list.innerHTML = "";
        
        // Biến tính tổng doanh thu
        let totalSystemRevenue = 0;

        // Dùng for...of để có thể await bên trong (lấy payment của từng HĐ)
        for (const c of data) {
            // Lấy tổng tiền đã đóng của hợp đồng này để cộng vào doanh thu tổng
            const payments = await getPayments(c.id);
            const paidAmount = payments.reduce((sum, p) => sum + p.amount, 0);
            totalSystemRevenue += paidAmount;

            list.innerHTML += `
                <li class="list-group-item list-group-item-action contract-item" onclick="openPaymentModal(${c.id})">
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <strong>HĐ #${c.id}</strong> <small class="text-muted">(Phòng ID: ${c.property_id})</small><br>
                            <small>Đã thu: <span class="text-success fw-bold">${paidAmount.toLocaleString()}đ</span></small>
                        </div>
                        <span class="badge bg-primary rounded-pill">Thu tiền</span>
                    </div>
                </li>
            `;
        }

        // Cập nhật lên Dashboard
        document.getElementById("totalRevenue").innerText = totalSystemRevenue.toLocaleString() + " đ";

    } catch (e) { console.error(e); }
}

// Hàm phụ: Lấy list payment của 1 hợp đồng
async function getPayments(contractId) {
    try {
        const res = await fetch(`${API_URL}/contracts/${contractId}/payments`);
        return await res.json();
    } catch { return []; }
}

// --- 3. MODAL THANH TOÁN ---
async function openPaymentModal(contractId) {
    document.getElementById('modalContractId').innerText = contractId;
    document.getElementById('payContractId').value = contractId;
    document.getElementById('payDate').valueAsDate = new Date();
    
    // Load lịch sử chi tiết
    const payments = await getPayments(contractId);
    const historyBody = document.getElementById('paymentHistoryList');
    historyBody.innerHTML = "";

    let totalPaid = 0;

    if(payments.length === 0) {
        historyBody.innerHTML = "<tr><td colspan='4' class='text-center text-muted'>Chưa có giao dịch</td></tr>";
    } else {
        payments.forEach(p => {
            totalPaid += p.amount;
            historyBody.innerHTML += `
                <tr>
                    <td>${p.payment_date}</td>
                    <td>${p.note || '-'}</td>
                    <td class="text-success fw-bold">+${p.amount.toLocaleString()}</td>
                    <td>✅</td>
                </tr>
            `;
        });
    }
    
    document.getElementById('totalPaidDisplay').innerText = `Tổng đã đóng: ${totalPaid.toLocaleString()}đ`;
    paymentModal.show();
}

// --- 4. XỬ LÝ FORM SUBMIT ---
// Thu tiền
document.getElementById("paymentForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const contractId = document.getElementById("payContractId").value;
    const payload = {
        contract_id: parseInt(contractId),
        amount: parseFloat(document.getElementById("payAmount").value),
        payment_date: document.getElementById("payDate").value,
        note: document.getElementById("payNote").value
    };

    const res = await fetch(`${API_URL}/payments/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
    });

    if (res.ok) {
        alert("Đã thu tiền thành công!");
        document.getElementById("payAmount").value = "";
        openPaymentModal(contractId); // Reload lại modal để thấy dòng mới
        loadContracts(); // Reload lại dashboard để cập nhật tổng doanh thu
    } else {
        alert("Lỗi server");
    }
});

// Thêm nhà
document.getElementById("propertyForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const payload = {
        name: document.getElementById("propName").value,
        address: document.getElementById("propAddress").value,
        price: parseFloat(document.getElementById("propPrice").value),
        description: "Mô tả"
    };
    await fetch(`${API_URL}/properties/?owner_id=1`, {
        method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload)
    });
    alert("Thêm nhà thành công!");
    loadProperties();
    document.getElementById("propertyForm").reset();
});

// Ký hợp đồng
document.getElementById("contractForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const payload = {
        property_id: parseInt(document.getElementById("contractPropId").value),
        tenant_email: document.getElementById("contractEmail").value,
        start_date: document.getElementById("startDate").value,
        end_date: document.getElementById("endDate").value,
        deposit_amount: parseFloat(document.getElementById("deposit").value) || 0
    };
    
    const res = await fetch(`${API_URL}/contracts/`, {
        method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload)
    });

    if (res.ok) {
        alert("Ký hợp đồng thành công!");
        loadProperties();
        loadContracts();
        document.getElementById("contractForm").reset();
    } else {
        const err = await res.json();
        alert("Lỗi: " + (err.detail || JSON.stringify(err)));
    }
});

// Mock Data
async function createMockUser() {
    await fetch(`${API_URL}/users/`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ username: "admin", email: "chu@tro.com", password: "123", full_name: "Chủ Trọ" }) });
    alert("Sent Admin Request");
}
async function createTenant() {
    await fetch(`${API_URL}/users/`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ username: "khach", email: "khach@thue.com", password: "123", full_name: "Khách Thuê" }) });
    alert("Sent Tenant Request");
}

// INIT
loadProperties();
loadContracts();