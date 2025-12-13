const API_URL = "http://localhost:8000";

// --- 1. LOAD DANH SÁCH NHÀ (Properties) ---
async function loadProperties() {
    try {
        const res = await fetch(`${API_URL}/properties/`);
        const data = await res.json();
        
        const listBody = document.getElementById("propertyList");
        const selectBox = document.getElementById("contractPropId");
        
        // Reset giao diện
        listBody.innerHTML = "";
        selectBox.innerHTML = '<option value="">-- Chọn phòng --</option>';

        data.forEach(prop => {
            // A. Vẽ bảng danh sách nhà
            let badgeClass = prop.status === 'available' ? 'bg-success' : 'bg-secondary';
            let statusText = prop.status === 'available' ? 'Trống' : 'Đã thuê';
            
            const row = `
                <tr>
                    <td>${prop.id}</td>
                    <td><strong>${prop.name}</strong><br><small>${prop.address}</small></td>
                    <td>${prop.price.toLocaleString()}</td>
                    <td><span class="badge ${badgeClass}">${statusText}</span></td>
                </tr>
            `;
            listBody.innerHTML += row;

            // B. Đổ dữ liệu vào Dropdown chọn phòng (Chỉ hiện nhà còn trống)
            if (prop.status === 'available') {
                const option = `<option value="${prop.id}">${prop.name} - ${prop.price}đ</option>`;
                selectBox.innerHTML += option;
            }
        });
    } catch (error) { 
        console.error("Lỗi load nhà:", error); 
    }
}

// --- 2. LOAD DANH SÁCH HỢP ĐỒNG (Contracts) - ĐÃ SỬA LOGIC ---
async function loadContracts() {
    try {
        const res = await fetch(`${API_URL}/contracts/`);
        const data = await res.json();
        
        const list = document.getElementById("contractList");
        list.innerHTML = ""; // Xóa danh sách cũ

        data.forEach(c => {
            // Lưu ý: Backend trả về 'deposit' (theo tên cột DB), chứ không phải 'deposit_amount'
            // Nên ở đây phải dùng c.deposit
            const tienCoc = c.deposit ? c.deposit.toLocaleString() : "0";

            list.innerHTML += `
                <li class="list-group-item d-flex justify-content-between align-items-center">
                    <div>
                        <strong>Hợp đồng #${c.id}</strong><br>
                        <small>
                            Phòng ID: ${c.property_id} | Khách ID: ${c.tenant_id} <br>
                            Tiền cọc: <span class="text-danger fw-bold">${tienCoc} đ</span>
                        </small>
                    </div>
                    <span class="badge bg-primary">Active</span>
                </li>
            `;
        });
    } catch (e) { 
        console.error("Lỗi load hợp đồng:", e); 
    }
}

// --- 3. XỬ LÝ FORM THÊM NHÀ ---
document.getElementById("propertyForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const payload = {
        name: document.getElementById("propName").value,
        address: document.getElementById("propAddress").value,
        price: parseFloat(document.getElementById("propPrice").value),
        description: "Mô tả mẫu"
    };

    try {
        const res = await fetch(`${API_URL}/properties/?owner_id=1`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        if (res.ok) {
            alert("Thêm nhà thành công!");
            loadProperties();
            document.getElementById("propertyForm").reset();
        } else {
            alert("Lỗi thêm nhà");
        }
    } catch (err) { console.error(err); }
});

// --- 4. XỬ LÝ FORM KÝ HỢP ĐỒNG (QUAN TRỌNG) ---
document.getElementById("contractForm").addEventListener("submit", async (e) => {
    e.preventDefault();

    // Lấy dữ liệu từ form
    const propId = document.getElementById("contractPropId").value;
    const email = document.getElementById("contractEmail").value;
    const start = document.getElementById("startDate").value;
    const end = document.getElementById("endDate").value;
    const deposit = document.getElementById("deposit").value;

    // Validate cơ bản
    if (!propId) { alert("Vui lòng chọn phòng!"); return; }
    if (!start || !end) { alert("Vui lòng chọn ngày!"); return; }

    // Payload gửi đi: Phải dùng 'deposit_amount' để khớp với Schema input
    const payload = {
        property_id: parseInt(propId),
        tenant_email: email,
        start_date: start,
        end_date: end,
        deposit_amount: parseFloat(deposit) || 0 
    };

    try {
        const res = await fetch(`${API_URL}/contracts/`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        if (res.ok) {
            alert("✅ Ký hợp đồng thành công! Nhà đã cập nhật trạng thái.");
            
            // Gọi lại 2 hàm này để làm mới dữ liệu ngay lập tức
            await loadProperties(); // Để nhà vừa thuê biến mất khỏi list trống
            await loadContracts();  // Để hợp đồng mới hiện ra list bên dưới
            
            document.getElementById("contractForm").reset();
        } else {
            const err = await res.json();
            // Hiển thị lỗi chi tiết từ Backend trả về (nếu có)
            alert("❌ Lỗi: " + (err.detail || JSON.stringify(err)));
            console.log(err);
        }
    } catch (error) {
        alert("Không kết nối được server!");
        console.error(error);
    }
});

// --- 5. HÀM TẠO DATA MẪU (CHO DỄ TEST) ---
async function createMockUser() {
    await fetch(`${API_URL}/users/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username: "admin_tro", email: "chu@tro.com", password: "123", full_name: "Chủ Trọ Demo" })
    });
    alert("Đã gửi lệnh tạo Chủ Trọ.");
}

async function createTenant() {
    await fetch(`${API_URL}/users/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username: "khach_demo", email: "khach@thue.com", password: "123", full_name: "Khách Demo" })
    });
    alert("Đã gửi lệnh tạo Khách Thuê.");
}

// CHẠY LẦN ĐẦU KHI VÀO WEB
loadProperties();
loadContracts();
