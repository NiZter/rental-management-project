const API_URL = "http://localhost:8000";
const paymentModal = new bootstrap.Modal(document.getElementById('paymentModal'));

// --- 1. QUẢN LÝ TÀI SẢN ---
async function loadProperties() {
    try {
        const filterCat = document.getElementById("filterCategory").value;
        let url = `${API_URL}/properties/`;
        if (filterCat) url += `?category=${filterCat}`;

        const res = await fetch(url);
        const data = await res.json();
        
        const listBody = document.getElementById("propertyList");
        const selectBox = document.getElementById("contractPropId");
        
        listBody.innerHTML = "";
        selectBox.innerHTML = '<option value="" data-price="0">-- Chọn tài sản --</option>';

        data.forEach(prop => {
            let icon = prop.category === 'vehicle' ? '🚗' : (prop.category === 'item' ? '📷' : '🏠');
            let badge = prop.status === 'available' ? '<span class="badge bg-success">Sẵn sàng</span>' : '<span class="badge bg-secondary">Đang thuê</span>';
            
            listBody.innerHTML += `
                <tr>
                    <td class="fs-5 text-center">${icon}</td>
                    <td><strong>${prop.name}</strong><br><small class="text-muted">${prop.address}</small></td>
                    <td class="text-primary fw-bold">${prop.price.toLocaleString()}</td>
                    <td>${badge}</td>
                </tr>
            `;

            // Lưu giá tiền vào attribute data-price để JS lấy tính toán
            selectBox.innerHTML += `<option value="${prop.id}" data-price="${prop.price}">[${icon}] ${prop.name} - ${prop.price}</option>`;
        });
    } catch (e) { console.error(e); }
}

document.getElementById("propertyForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const payload = {
        name: document.getElementById("propName").value,
        address: document.getElementById("propAddress").value,
        price: parseFloat(document.getElementById("propPrice").value),
        category: document.getElementById("propCategory").value,
        description: "Mô tả mẫu"
    };
    await fetch(`${API_URL}/properties/?owner_id=1`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
    alert("Thêm thành công!");
    loadProperties();
    document.getElementById("propertyForm").reset();
});

// --- 2. TÍNH TIỀN TỰ ĐỘNG (LOGIC MỚI) ---
function calculateTotal() {
    // 1. Lấy giá từ dropdown
    const selectBox = document.getElementById("contractPropId");
    const selectedOption = selectBox.options[selectBox.selectedIndex];
    const price = parseFloat(selectedOption.getAttribute("data-price")) || 0;

    // 2. Lấy ngày
    const startStr = document.getElementById("startDate").value;
    const endStr = document.getElementById("endDate").value;

    if (!startStr || !endStr || price === 0) {
        document.getElementById("previewTotal").innerText = "0 đ";
        return;
    }

    const startDate = new Date(startStr);
    const endDate = new Date(endStr);
    
    // Tính số ngày chênh lệch
    const diffTime = Math.abs(endDate - startDate);
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24)); 

    if (diffDays <= 0) {
        document.getElementById("previewTotal").innerText = "Lỗi ngày";
        return;
    }

    // 3. Tính tiền theo loại thuê
    let total = 0;
    const isMonthly = document.getElementById("typeMonthly").checked;

    if (isMonthly) {
        // Giả sử 1 tháng = 30 ngày (Logic đơn giản)
        const months = diffDays / 30;
        total = months * price;
    } else {
        total = diffDays * price;
    }

    document.getElementById("previewTotal").innerText = total.toLocaleString() + " đ";
}

// --- 3. QUẢN LÝ HỢP ĐỒNG ---
async function loadContracts() {
    try {
        const res = await fetch(`${API_URL}/contracts/`);
        const data = await res.json();
        const list = document.getElementById("contractList");
        list.innerHTML = "";
        let totalRev = 0;

        for (const c of data) {
            const payments = await getPayments(c.id);
            const paid = payments.reduce((sum, p) => sum + p.amount, 0);
            totalRev += paid;

            list.innerHTML += `
                <li class="list-group-item list-group-item-action contract-item" onclick="openPaymentModal(${c.id})">
                    <div class="d-flex justify-content-between">
                        <div>
                            <strong>HĐ #${c.id}</strong> <small>(ID Tài sản: ${c.property_id})</small><br>
                            <small>Tổng giá trị: <span class="text-danger fw-bold">${c.total_price.toLocaleString()}đ</span></small>
                        </div>
                        <span class="badge bg-primary rounded-pill">Đã thu: ${paid.toLocaleString()}</span>
                    </div>
                </li>
            `;
        }
        document.getElementById("totalRevenue").innerText = totalRev.toLocaleString() + " đ";
    } catch (e) {}
}

document.getElementById("contractForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const rentalType = document.querySelector('input[name="rentalType"]:checked').value;
    
    const payload = {
        property_id: parseInt(document.getElementById("contractPropId").value),
        tenant_email: document.getElementById("contractEmail").value,
        start_date: document.getElementById("startDate").value,
        end_date: document.getElementById("endDate").value,
        deposit_amount: parseFloat(document.getElementById("deposit").value) || 0,
        rental_type: rentalType // Gửi thêm loại thuê
    };

    const res = await fetch(`${API_URL}/contracts/`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
    
    if (res.ok) {
        alert("✅ Ký hợp đồng thành công!");
        loadProperties(); loadContracts();
        document.getElementById("contractForm").reset();
        document.getElementById("previewTotal").innerText = "0 đ";
    } else {
        const err = await res.json();
        alert("❌ Lỗi: " + (err.detail || "Trùng lịch hoặc lỗi dữ liệu"));
    }
});

// --- 4. THANH TOÁN & INIT ---
async function getPayments(cid) {
    try { const res = await fetch(`${API_URL}/contracts/${cid}/payments`); return await res.json(); } catch { return []; }
}

async function openPaymentModal(cid) {
    document.getElementById('modalContractId').innerText = cid;
    document.getElementById('payContractId').value = cid;
    document.getElementById('payDate').valueAsDate = new Date();
    
    const payments = await getPayments(cid);
    const history = document.getElementById('paymentHistoryList');
    history.innerHTML = "";
    payments.forEach(p => {
        history.innerHTML += `<tr><td>${p.payment_date}</td><td>${p.note||'-'}</td><td class="text-success">+${p.amount.toLocaleString()}</td></tr>`;
    });
    paymentModal.show();
}

document.getElementById("paymentForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const cid = document.getElementById("payContractId").value;
    const payload = {
        contract_id: parseInt(cid),
        amount: parseFloat(document.getElementById("payAmount").value),
        payment_date: document.getElementById("payDate").value,
        note: document.getElementById("payNote").value
    };
    await fetch(`${API_URL}/payments/`, { method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(payload)});
    alert("Thu tiền thành công!");
    openPaymentModal(cid); loadContracts();
});

async function createMockUser() { await fetch(`${API_URL}/users/`, {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({username:"admin", email:"chu@tro.com", password:"123", full_name:"Admin"})}); alert("Tạo Admin OK"); }
async function createTenant() { await fetch(`${API_URL}/users/`, {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({username:"khach", email:"khach@thue.com", password:"123", full_name:"Khách"})}); alert("Tạo Khách OK"); }

loadProperties();
loadContracts();