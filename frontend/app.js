const API_URL = "http://localhost:8000";
// Khởi tạo Modal của Bootstrap
const paymentModal = new bootstrap.Modal(document.getElementById('paymentModal'));

// ==========================================
// 1. QUẢN LÝ TÀI SẢN (PROPERTIES)
// ==========================================

// Hàm load danh sách tài sản (Có hỗ trợ lọc theo Category)
async function loadProperties() {
    try {
        // Lấy giá trị từ dropdown bộ lọc
        const filterCat = document.getElementById("filterCategory") ? document.getElementById("filterCategory").value : "";
        
        let url = `${API_URL}/properties/`;
        if (filterCat) url += `?category=${filterCat}`; // Thêm tham số lọc vào URL

        const res = await fetch(url);
        const data = await res.json();
        
        const listBody = document.getElementById("propertyList");
        const selectBox = document.getElementById("contractPropId");
        
        // Reset giao diện
        listBody.innerHTML = "";
        selectBox.innerHTML = '<option value="">-- Chọn tài sản --</option>';

        data.forEach(prop => {
            // Chọn icon hiển thị dựa trên category
            let icon = '🏠';
            if (prop.category === 'vehicle') icon = '🚗';
            if (prop.category === 'item') icon = '📷';

            // Tạo badge trạng thái
            let badge = prop.status === 'available' 
                ? '<span class="badge bg-success">Sẵn sàng</span>' 
                : '<span class="badge bg-secondary">Đang thuê</span>';
            
            // Render ra bảng
            listBody.innerHTML += `
                <tr>
                    <td class="fs-5 text-center">${icon}</td>
                    <td>
                        <strong>${prop.name}</strong>
                        <br><small class="text-muted">${prop.address}</small>
                    </td>
                    <td class="text-primary fw-bold">${prop.price.toLocaleString()}</td>
                    <td>${badge}</td>
                </tr>
            `;

            // Đổ dữ liệu vào dropdown tạo hợp đồng (chỉ lấy tài sản còn trống)
            if (prop.status === 'available') {
                selectBox.innerHTML += `<option value="${prop.id}">[${icon}] ${prop.name} - ${prop.price}đ</option>`;
            }
        });
    } catch (e) { 
        console.error("Lỗi load tài sản:", e); 
    }
}

// Xử lý Form Thêm Tài Sản Mới
document.getElementById("propertyForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    
    // Lấy dữ liệu từ form
    const payload = {
        name: document.getElementById("propName").value,
        address: document.getElementById("propAddress").value,
        price: parseFloat(document.getElementById("propPrice").value),
        category: document.getElementById("propCategory").value, // Quan trọng: Gửi thêm loại tài sản
        description: "Mô tả mẫu từ frontend"
    };

    try {
        // Gọi API tạo property (Mặc định owner_id = 1)
        const res = await fetch(`${API_URL}/properties/?owner_id=1`, {
            method: "POST", 
            headers: { "Content-Type": "application/json" }, 
            body: JSON.stringify(payload)
        });
        
        if (res.ok) {
            alert("✅ Thêm tài sản thành công!");
            loadProperties(); // Load lại danh sách
            document.getElementById("propertyForm").reset();
        } else {
            const err = await res.json();
            alert("❌ Lỗi: " + (err.detail || "Không thể thêm tài sản"));
        }
    } catch (error) {
        console.error(error);
        alert("Lỗi kết nối server!");
    }
});

// ==========================================
// 2. QUẢN LÝ HỢP ĐỒNG & DOANH THU
// ==========================================

// Hàm load danh sách hợp đồng và tính tổng doanh thu
async function loadContracts() {
    try {
        const res = await fetch(`${API_URL}/contracts/`);
        const data = await res.json();
        
        const list = document.getElementById("contractList");
        list.innerHTML = "";
        
        let totalSystemRevenue = 0; // Biến tổng doanh thu toàn hệ thống

        // Dùng vòng lặp for...of để có thể dùng await bên trong (lấy payment của từng HĐ)
        for (const c of data) {
            // Lấy lịch sử thanh toán để tính tổng tiền đã đóng
            const payments = await getPayments(c.id);
            const paidAmount = payments.reduce((sum, p) => sum + p.amount, 0);
            
            // Cộng dồn vào tổng doanh thu hệ thống
            totalSystemRevenue += paidAmount;

            // Render item hợp đồng
            list.innerHTML += `
                <li class="list-group-item list-group-item-action contract-item" onclick="openPaymentModal(${c.id})">
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <strong>HĐ #${c.id}</strong> <small class="text-muted">(Tài sản ID: ${c.property_id})</small><br>
                            <small>Đã thu: <span class="text-success fw-bold">${paidAmount.toLocaleString()}đ</span></small>
                        </div>
                        <span class="badge bg-primary rounded-pill">Thu tiền</span>
                    </div>
                </li>
            `;
        }

        // Cập nhật con số tổng doanh thu lên Dashboard (nếu có element đó)
        const revenueEl = document.getElementById("totalRevenue");
        if (revenueEl) {
            revenueEl.innerText = totalSystemRevenue.toLocaleString() + " đ";
        }

    } catch (e) { 
        console.error("Lỗi load hợp đồng:", e); 
    }
}

// Xử lý Form Ký Hợp Đồng
document.getElementById("contractForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    
    const propId = document.getElementById("contractPropId").value;
    const email = document.getElementById("contractEmail").value;
    const start = document.getElementById("startDate").value;
    const end = document.getElementById("endDate").value;
    const deposit = document.getElementById("deposit").value;

    if (!propId) { alert("Vui lòng chọn tài sản!"); return; }

    const payload = {
        property_id: parseInt(propId),
        tenant_email: email,
        start_date: start,
        end_date: end,
        deposit_amount: parseFloat(deposit) || 0 // Lưu ý: map với deposit_amount trong Schema
    };
    
    try {
        const res = await fetch(`${API_URL}/contracts/`, {
            method: "POST", 
            headers: { "Content-Type": "application/json" }, 
            body: JSON.stringify(payload)
        });

        if (res.ok) {
            alert("✅ Ký hợp đồng thành công!");
            loadProperties(); // Reload để tài sản chuyển trạng thái 'Đang thuê'
            loadContracts();  // Reload để hiện hợp đồng mới
            document.getElementById("contractForm").reset();
        } else {
            const err = await res.json();
            alert("❌ Lỗi: " + (err.detail || JSON.stringify(err)));
        }
    } catch (error) {
        alert("Lỗi kết nối server!");
    }
});

// ==========================================
// 3. QUẢN LÝ THANH TOÁN (PAYMENTS)
// ==========================================

// Hàm helper: Lấy danh sách payment của 1 hợp đồng
async function getPayments(contractId) {
    try {
        const res = await fetch(`${API_URL}/contracts/${contractId}/payments`);
        if (!res.ok) return [];
        return await res.json();
    } catch { return []; }
}

// Hàm mở Modal Thanh toán
async function openPaymentModal(contractId) {
    // Set thông tin vào Modal
    document.getElementById('modalContractId').innerText = contractId;
    document.getElementById('payContractId').value = contractId;
    document.getElementById('payDate').valueAsDate = new Date(); // Mặc định là hôm nay
    
    // Load lịch sử thanh toán chi tiết
    const payments = await getPayments(contractId);
    const historyBody = document.getElementById('paymentHistoryList');
    historyBody.innerHTML = "";

    let totalPaid = 0;

    if(payments.length === 0) {
        historyBody.innerHTML = "<tr><td colspan='4' class='text-center text-muted'>Chưa có giao dịch nào</td></tr>";
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
    
    // Hiển thị tổng tiền đã đóng trong Modal
    document.getElementById('totalPaidDisplay').innerText = `Tổng: ${totalPaid.toLocaleString()}đ`;
    
    // Hiện Modal
    paymentModal.show();
}

// Xử lý Form Thu Tiền (Trong Modal)
document.getElementById("paymentForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const contractId = document.getElementById("payContractId").value;
    
    const payload = {
        contract_id: parseInt(contractId),
        amount: parseFloat(document.getElementById("payAmount").value),
        payment_date: document.getElementById("payDate").value,
        note: document.getElementById("payNote").value
    };

    try {
        const res = await fetch(`${API_URL}/payments/`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        if (res.ok) {
            alert("💰 Thu tiền thành công!");
            
            // Reset form nhập
            document.getElementById("payAmount").value = "";
            document.getElementById("payNote").value = "";
            
            // Reload dữ liệu
            openPaymentModal(contractId); // Load lại bảng lịch sử trong modal
            loadContracts(); // Load lại dashboard tổng doanh thu bên ngoài
        } else {
            const err = await res.json();
            alert("Lỗi: " + (err.detail || "Không thể thu tiền"));
        }
    } catch (err) { console.error(err); }
});

// ==========================================
// 4. MOCK DATA (DỮ LIỆU MẪU)
// ==========================================

async function createMockUser() {
    try {
        await fetch(`${API_URL}/users/`, { 
            method: "POST", 
            headers: { "Content-Type": "application/json" }, 
            body: JSON.stringify({ username: "admin", email: "chu@tro.com", password: "123", full_name: "Chủ Trọ Demo" }) 
        });
        alert("Đã gửi lệnh tạo Admin (ID: 1)");
    } catch (e) { console.error(e); }
}

async function createTenant() {
    try {
        await fetch(`${API_URL}/users/`, { 
            method: "POST", 
            headers: { "Content-Type": "application/json" }, 
            body: JSON.stringify({ username: "khach", email: "khach@thue.com", password: "123", full_name: "Khách Thuê Demo" }) 
        });
        alert("Đã gửi lệnh tạo Khách Thuê (Email: khach@thue.com)");
    } catch (e) { console.error(e); }
}

// ==========================================
// 5. KHỞI TẠO ỨNG DỤNG
// ==========================================
// Chạy ngay khi web vừa load xong
loadProperties();
loadContracts();