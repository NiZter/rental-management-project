const API_URL = "http://localhost:8000";
const paymentModal = new bootstrap.Modal(document.getElementById("paymentModal"));

// ==================================================
// 1. TÀI SẢN (PROPERTY)
// ==================================================
async function loadProperties() {
    try {
        const filterCat = document.getElementById("filterCategory").value || "";
        const res = await fetch(`${API_URL}/properties/`);
        
        if (!res.ok) {
            console.error("Lỗi tải tài sản:", res.status);
            return;
        }

        const data = await res.json();
        
        const listBody = document.getElementById("propertyList");
        const selectBox = document.getElementById("contractPropId");
        listBody.innerHTML = "";
        
        // Reset dropdown nhưng giữ option mặc định
        selectBox.innerHTML = `<option value="">-- Chọn tài sản --</option>`;

        if (Array.isArray(data)) {
            data.filter(p => !filterCat || p.category === filterCat).forEach(p => {
                const icon = p.category === "vehicle" ? "🚗" : p.category === "item" ? "📦" : "🏠";
                const badge = p.status === "available" ? `<span class="badge bg-success">Sẵn sàng</span>` : `<span class="badge bg-secondary">Đang thuê</span>`;
                
                listBody.innerHTML += `
                    <tr>
                        <td class="text-center fs-5">${icon}</td>
                        <td><strong>${p.name}</strong><br><small class="text-muted">${p.address}</small></td>
                        <td class="fw-bold text-primary">${p.price.toLocaleString()}</td>
                        <td>${badge}</td>
                    </tr>`;
                
                if (p.status === "available") {
                    selectBox.innerHTML += `<option value="${p.id}" data-price="${p.price}">[${icon}] ${p.name}</option>`;
                }
            });
        }
    } catch (e) { 
        console.error("Không thể kết nối Backend:", e);
    }
}

document.getElementById("propertyForm")?.addEventListener("submit", async e => {
    e.preventDefault();
    const payload = {
        name: document.getElementById("propName").value,
        address: document.getElementById("propAddress").value,
        price: Number(document.getElementById("propPrice").value),
        category: document.getElementById("propCategory").value,
        owner_id: 1
    };
    try {
        await fetch(`${API_URL}/properties/`, { method: "POST", headers: {"Content-Type":"application/json"}, body: JSON.stringify(payload)});
        alert("✅ Đã thêm tài sản"); 
        e.target.reset(); 
        loadProperties();
    } catch (err) {
        alert("❌ Lỗi kết nối server");
    }
});

// ==================================================
// 2. TÍNH TIỀN (PREVIEW)
// ==================================================
function calculateTotal() {
    const propSelect = document.getElementById("contractPropId");
    const option = propSelect.options[propSelect.selectedIndex];
    const price = Number(option?.dataset.price || 0);
    const start = new Date(document.getElementById("startDate").value);
    const end = new Date(document.getElementById("endDate").value);
    
    if (!price || isNaN(start.getTime()) || isNaN(end.getTime())) {
        document.getElementById("previewTotal").innerText = "0 đ"; return;
    }
    
    const days = Math.ceil((end - start) / (86400000));
    if (days <= 0) {
        document.getElementById("previewTotal").innerText = "Ngày không hợp lệ";
        return;
    }

    const type = document.querySelector('input[name="rentalType"]:checked').value;
    let total = type === "daily" ? days * price : Math.max(1, Math.ceil((days + 15) / 30)) * price;
    
    document.getElementById("previewTotal").innerText = total.toLocaleString() + " đ";
}

// ==================================================
// 3. HỢP ĐỒNG (CONTRACTS) - ĐÃ FIX LỖI HIỂN THỊ
// ==================================================
async function loadContracts() {
    try {
        const res = await fetch(`${API_URL}/contracts/`);
        
        // Nếu Server lỗi (500) hoặc chưa chạy -> Báo lỗi
        if (!res.ok) {
            document.getElementById("contractList").innerHTML = `<li class="list-group-item text-danger">⚠️ Lỗi Backend: ${res.statusText}</li>`;
            return;
        }

        const data = await res.json();
        const list = document.getElementById("contractList");
        list.innerHTML = "";
        let totalRev = 0;

        // KIỂM TRA QUAN TRỌNG: Data phải là mảng mới chạy loop
        if (!Array.isArray(data)) {
            console.error("Dữ liệu hợp đồng không phải là mảng:", data);
            return;
        }

        if (data.length === 0) {
            list.innerHTML = `<li class="list-group-item text-muted text-center">Chưa có hợp đồng nào</li>`;
            document.getElementById("totalRevenue").innerText = "0 đ";
            return;
        }

        for (const c of data) {
            // Lấy thanh toán an toàn hơn
            let paid = 0;
            try {
                const payRes = await fetch(`${API_URL}/contracts/${c.id}/payments`);
                if (payRes.ok) {
                    const payments = await payRes.json();
                    if (Array.isArray(payments)) {
                        paid = payments.reduce((s, p) => s + p.amount, 0);
                    }
                }
            } catch (err) { console.error("Lỗi tải thanh toán:", err); }

            totalRev += paid;

            list.innerHTML += `
                <li class="list-group-item">
                    <div class="d-flex justify-content-between align-items-center" onclick="openPaymentModal(${c.id})" style="cursor:pointer">
                        <div>
                            <strong>HĐ #${c.id}</strong> <span class="badge bg-info text-dark">${c.status || 'active'}</span><br>
                            <small>Tổng: <b class="text-danger">${(c.total_price || 0).toLocaleString()}</b> | Cọc: ${(c.deposit || 0).toLocaleString()}</small>
                        </div>
                        <div class="text-end">
                            <span class="badge bg-success mb-1">Đã thu: ${paid.toLocaleString()}</span><br>
                        </div>
                    </div>
                    <div class="mt-1 text-end">
                        <button class="btn btn-outline-secondary btn-sm py-0" onclick="downloadContract(${c.id}, event)">
                            <i class="fa-solid fa-print"></i> Tải Hợp Đồng
                        </button>
                    </div>
                </li>`;
        }
        document.getElementById("totalRevenue").innerText = totalRev.toLocaleString() + " đ";
    } catch (e) { 
        console.error("Lỗi tải hợp đồng:", e);
        document.getElementById("contractList").innerHTML = `<li class="list-group-item text-danger">⚠️ Mất kết nối server</li>`;
    }
}

async function downloadContract(id, event) {
    if(event) event.stopPropagation(); // Ngăn mở modal thanh toán
    window.open(`${API_URL}/contracts/${id}/download`, '_blank');
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
        const res = await fetch(`${API_URL}/contracts/`, { method: "POST", headers: {"Content-Type":"application/json"}, body: JSON.stringify(payload)});
        
        if (!res.ok) {
            const err = await res.json();
            alert("❌ " + (err.detail || "Lỗi tạo hợp đồng")); 
            return;
        }

        const newContract = await res.json();
        alert("✅ Ký hợp đồng thành công!");
        
        // Tự động tải hợp đồng về luôn
        downloadContract(newContract.id);

        e.target.reset(); 
        document.getElementById("previewTotal").innerText = "0 đ";
        loadProperties(); 
        loadContracts();
    } catch (err) {
        alert("❌ Lỗi kết nối: " + err.message);
    }
});

// ==================================================
// 4. THANH TOÁN (PAYMENTS)
// ==================================================
async function openPaymentModal(cid) {
    document.getElementById("modalContractId").innerText = cid;
    document.getElementById("payContractId").value = cid;
    document.getElementById("payDate").valueAsDate = new Date();
    
    try {
        const res = await fetch(`${API_URL}/contracts/${cid}/payments`);
        const history = document.getElementById("paymentHistoryList");
        history.innerHTML = "";
        
        if (res.ok) {
            const payments = await res.json();
            if (Array.isArray(payments)) {
                payments.forEach(p => {
                    history.innerHTML += `<tr><td>${p.payment_date}</td><td>${p.note||'-'}</td><td class="text-success">+${p.amount.toLocaleString()}</td></tr>`;
                });
            }
        }
    } catch (err) { console.error(err); }
    
    paymentModal.show();
}

document.getElementById("paymentForm")?.addEventListener("submit", async e => {
    e.preventDefault();
    const payload = {
        contract_id: Number(document.getElementById("payContractId").value),
        amount: Number(document.getElementById("payAmount").value),
        payment_date: document.getElementById("payDate").value,
        note: document.getElementById("payNote").value
    };
    try {
        await fetch(`${API_URL}/payments/`, { method: "POST", headers: {"Content-Type":"application/json"}, body: JSON.stringify(payload)});
        alert("✅ Thu tiền thành công");
        openPaymentModal(payload.contract_id); 
        loadContracts();
    } catch (err) { alert("Lỗi thanh toán"); }
});

// ==================================================
// 5. MOCK DATA (Dùng để tạo dữ liệu mẫu khi mới reset DB)
// ==================================================
async function createMockAdmin() {
    try {
        await fetch(`${API_URL}/users/`, { method: "POST", headers: {"Content-Type":"application/json"}, body: JSON.stringify({username:"admin", email:"admin@rental.com", password:"123", full_name:"Admin"})});
        alert("Đã tạo Admin thành công (hoặc đã tồn tại)");
    } catch (e) { alert("Lỗi kết nối"); }
}
async function createTenant() {
    try {
        await fetch(`${API_URL}/users/`, { method: "POST", headers: {"Content-Type":"application/json"}, body: JSON.stringify({username:"khach", email:"khach@gmail.com", password:"123", full_name:"Khách Demo"})});
        alert("Đã tạo Khách thành công");
    } catch (e) { alert("Lỗi kết nối"); }
}

// Khởi chạy
loadProperties();
loadContracts();