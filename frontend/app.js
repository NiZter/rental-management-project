const API_URL = "http://localhost:8000";
const paymentModal = new bootstrap.Modal(
    document.getElementById("paymentModal")
);

// ==================================================
// 1. TÀI SẢN
// ==================================================
async function loadProperties() {
    try {
        const filterCat = document.getElementById("filterCategory")?.value || "";
        const res = await fetch(`${API_URL}/properties/`);
        const data = await res.json();

        const listBody = document.getElementById("propertyList");
        const selectBox = document.getElementById("contractPropId");

        listBody.innerHTML = "";
        selectBox.innerHTML = `<option value="">-- Chọn tài sản --</option>`;

        data
            .filter(p => !filterCat || p.category === filterCat)
            .forEach(prop => {
                const icon =
                    prop.category === "vehicle" ? "🚗" :
                    prop.category === "item" ? "📦" : "🏠";

                const badge = prop.status === "available"
                    ? `<span class="badge bg-success">Sẵn sàng</span>`
                    : `<span class="badge bg-secondary">Đang thuê</span>`;

                listBody.innerHTML += `
                    <tr>
                        <td class="text-center fs-5">${icon}</td>
                        <td>
                            <strong>${prop.name}</strong><br>
                            <small class="text-muted">${prop.address}</small>
                        </td>
                        <td class="fw-bold text-primary">
                            ${prop.price.toLocaleString()}
                        </td>
                        <td>${badge}</td>
                    </tr>
                `;

                if (prop.status === "available") {
                    selectBox.innerHTML += `
                        <option value="${prop.id}" data-price="${prop.price}">
                            [${icon}] ${prop.name}
                        </option>
                    `;
                }
            });
    } catch (err) {
        console.error(err);
    }
}

document.getElementById("propertyForm")?.addEventListener("submit", async e => {
    e.preventDefault();

    const payload = {
        name: document.getElementById("propName").value,
        address: document.getElementById("propAddress").value,
        price: Number(document.getElementById("propPrice").value),
        category: document.getElementById("propCategory").value,
        description: null,
        owner_id: 1 // admin mặc định
    };

    const res = await fetch(`${API_URL}/properties/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
    });

    if (!res.ok) {
        alert("❌ Thêm tài sản thất bại");
        return;
    }

    alert("✅ Thêm tài sản thành công");
    e.target.reset();
    loadProperties();
});

// ==================================================
// 2. TÍNH TIỀN (GIỐNG BACKEND)
// ==================================================
function calculateTotal() {
    const propSelect = document.getElementById("contractPropId");
    const option = propSelect.options[propSelect.selectedIndex];
    const price = Number(option?.dataset.price || 0);

    const start = document.getElementById("startDate").value;
    const end = document.getElementById("endDate").value;

    if (!price || !start || !end) {
        document.getElementById("previewTotal").innerText = "0 đ";
        return;
    }

    const startDate = new Date(start);
    const endDate = new Date(end);
    const days = Math.ceil((endDate - startDate) / (1000 * 60 * 60 * 24));

    if (days <= 0) {
        document.getElementById("previewTotal").innerText = "Lỗi ngày";
        return;
    }

    const rentalType = document.querySelector(
        'input[name="rentalType"]:checked'
    ).value;

    let total = 0;
    if (rentalType === "daily") {
        total = days * price;
    } else {
        const months = Math.ceil(days / 30); // giống backend
        total = months * price;
    }

    document.getElementById("previewTotal").innerText =
        total.toLocaleString() + " đ";
}

// ==================================================
// 3. HỢP ĐỒNG
// ==================================================
async function loadContracts() {
    try {
        const res = await fetch(`${API_URL}/contracts/`);
        const data = await res.json();

        const list = document.getElementById("contractList");
        list.innerHTML = "";
        let totalRevenue = 0;

        for (const c of data) {
            const payments = await getPayments(c.id);
            const paid = payments.reduce((s, p) => s + p.amount, 0);
            totalRevenue += paid;

            list.innerHTML += `
                <li class="list-group-item list-group-item-action"
                    onclick="openPaymentModal(${c.id})">
                    <div class="d-flex justify-content-between">
                        <div>
                            <strong>HĐ #${c.id}</strong><br>
                            <small>Tổng: 
                                <span class="text-danger fw-bold">
                                    ${c.total_price.toLocaleString()} đ
                                </span>
                            </small>
                        </div>
                        <span class="badge bg-primary">
                            Đã thu ${paid.toLocaleString()}
                        </span>
                    </div>
                </li>
            `;
        }

        document.getElementById("totalRevenue").innerText =
            totalRevenue.toLocaleString() + " đ";
    } catch (err) {
        console.error(err);
    }
}

document.getElementById("contractForm")?.addEventListener("submit", async e => {
    e.preventDefault();

    const payload = {
        property_id: Number(document.getElementById("contractPropId").value),
        tenant_email: document.getElementById("contractEmail").value,
        start_date: document.getElementById("startDate").value,
        end_date: document.getElementById("endDate").value,
        deposit: Number(document.getElementById("deposit").value) || 0,
        rental_type: document.querySelector(
            'input[name="rentalType"]:checked'
        ).value
    };

    const res = await fetch(`${API_URL}/contracts/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
    });

    if (!res.ok) {
        const err = await res.json();
        alert("❌ " + (err.detail || "Lỗi tạo hợp đồng"));
        return;
    }

    alert("✅ Ký hợp đồng thành công");
    e.target.reset();
    document.getElementById("previewTotal").innerText = "0 đ";
    loadProperties();
    loadContracts();
});

// ==================================================
// 4. THANH TOÁN
// ==================================================
async function getPayments(cid) {
    try {
        const res = await fetch(`${API_URL}/contracts/${cid}/payments`);
        return await res.json();
    } catch {
        return [];
    }
}

async function openPaymentModal(cid) {
    document.getElementById("modalContractId").innerText = cid;
    document.getElementById("payContractId").value = cid;
    document.getElementById("payDate").valueAsDate = new Date();

    const payments = await getPayments(cid);
    const history = document.getElementById("paymentHistoryList");
    history.innerHTML = "";

    payments.forEach(p => {
        history.innerHTML += `
            <tr>
                <td>${p.payment_date}</td>
                <td>${p.note || "-"}</td>
                <td class="text-success">
                    +${p.amount.toLocaleString()}
                </td>
            </tr>
        `;
    });

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

    await fetch(`${API_URL}/payments/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
    });

    alert("✅ Thu tiền thành công");
    openPaymentModal(payload.contract_id);
    loadContracts();
});

// ==================================================
// 5. MOCK USER
// ==================================================
async function createMockAdmin() {
    await fetch(`${API_URL}/users/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            username: "admin",
            email: "admin@rental.com",
            password: "123456",
            full_name: "Admin"
        })
    });
    alert("Admin đã tồn tại hoặc tạo xong");
}

async function createTenant() {
    await fetch(`${API_URL}/users/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            username: "khach",
            email: "khach@thue.com",
            password: "123456",
            full_name: "Khách thuê"
        })
    });
    alert("Khách đã tồn tại hoặc tạo xong");
}

// INIT
loadProperties();
loadContracts();
