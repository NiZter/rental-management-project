const API_URL = "http://localhost:8000";
let paymentModal;

// Format tiền VNĐ
const fmtMoney = (amount) => new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(amount);

// Toast notification
function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `
        <div style="display: flex; align-items: center; gap: 12px;">
            <span>${type === 'success' ? '✅' : '❌'}</span>
            <span>${message}</span>
        </div>
    `;
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
        
        if (!res.ok) {
            showToast("Lỗi kết nối Backend", "error");
            return;
        }

        const data = await res.json();
        const listBody = document.getElementById("propertyList");
        const selectBox = document.getElementById("contractPropId");
        let propertyCount = 0;
        
        listBody.innerHTML = "";
        selectBox.innerHTML = `<option value="">-- Chọn tài sản --</option>`;

        const filteredData = Array.isArray(data) ? data. filter(p => ! filterCat || p.category === filterCat) : [];
        propertyCount = filteredData.length;
        
        if (filteredData.length === 0) {
            listBody.innerHTML = `<tr><td colspan="5" class="text-center text-muted py-4">Chưa có tài sản nào</td></tr>`;
        } else {
            filteredData.forEach(prop => {
                let imgHtml = '';
                if (prop.image_url) {
                    imgHtml = `<img src="${prop.image_url}" class="property-img" onerror="this.src='https://via.placeholder.com/60? text=Error'">`;
                } else {
                    const icon = prop.category === "vehicle" ? "🚗" :  prop.category === "item" ? "📦" : "🏠";
                    imgHtml = `<div class="icon-lg">${icon}</div>`;
                }

                const badge = prop.status === "available"
                    ? `<span class="badge badge-success">Sẵn sàng</span>`
                    : `<span class="badge badge-secondary">Đang thuê</span>`;

                listBody.innerHTML += `
                    <tr>
                        <td>${imgHtml}</td>
                        <td>
                            <div style="font-weight: 600; color: #1f2937; margin-bottom: 4px;">${prop.name}</div>
                            <div style="font-size: 12px; color: #6b7280;">${prop.address}</div>
                        </td>
                        <td class="text-end" style="color: #667eea; font-weight: 600;">${fmtMoney(prop.price)}</td>
                        <td class="text-center">${badge}</td>
                        <td class="text-center">
                            <button class="btn btn-sm btn-danger" onclick="deleteProperty(${prop.id})" title="Xóa">
                                <i class="fas fa-trash"></i>
                            </button>
                        </td>
                    </tr>
                `;

                if (prop.status === "available") {
                    selectBox.innerHTML += `
                        <option value="${prop. id}" data-price="${prop.price}">
                            ${prop.name} - ${fmtMoney(prop.price)}/ngày
                        </option>
                    `;
                }
            });
        }

        document.getElementById("totalProperties").innerText = propertyCount;

    } catch (err) {
        console.error(err);
        showToast("Lỗi tải dữ liệu", "error");
    }
}

// Thêm Tài Sản
document.getElementById("propertyForm")?.addEventListener("submit", async e => {
    e.preventDefault();
    const payload = {
        name: document.getElementById("propName").value,
        address: document.getElementById("propAddress").value,
        price: Number(document.getElementById("propPrice").value),
        category: document. getElementById("propCategory").value,
        image_url: document.getElementById("propImage").value || null
    };

    try {
        const res = await fetch(`${API_URL}/properties/`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        
        if (res.ok) {
            showToast("✅ Đã thêm tài sản mới!");
            e.target.reset();
            loadProperties();
        } else {
            const errData = await res.json().catch(() => ({}));
            showToast("Lỗi: " + (errData.detail || "Không rõ lý do"), "error");
        }
    } catch (err) {
        console.error(err);
        showToast("Lỗi kết nối", "error");
    }
});

// Xóa Tài Sản
async function deleteProperty(id) {
    if (!confirm("Xóa tài sản này? ")) return;
    try {
        const res = await fetch(`${API_URL}/properties/${id}`, { method: "DELETE" });
        if (res.ok) {
            showToast("✅ Đã xóa tài sản");
            loadProperties();
            loadContracts();
        } else {
            const err = await res.json().catch(() => ({}));
            showToast("❌ " + (err.detail || "Không thể xóa"), "error");
        }
    } catch (err) {
        console.error(err);
    }
}

// ============================================================
// 2. TÍNH TIỀN HỢP ĐỒNG
// ============================================================
function calculateTotal() {
    const propSelect = document.getElementById("contractPropId");
    const option = propSelect?. options[propSelect.selectedIndex];
    const price = Number(option?.dataset.price || 0);

    const start = document.getElementById("startDate")?.value;
    const end = document.getElementById("endDate")?.value;
    const rentalType = document.querySelector('input[name="rentalType"]:checked')?.value || "daily";
    const display = document.getElementById("previewTotal");

    if (!price || !start || !end) {
        if (display) display.innerText = "0 đ";
        return;
    }

    const startDate = new Date(start);
    const endDate = new Date(end);
    const diffTime = endDate - startDate;
    const days = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

    if (days <= 0) {
        if (display) display.innerText = "Ngày không hợp lệ";
        return;
    }

    let total = 0;
    if (rentalType === "daily") {
        total = days * price;
    } else if (rentalType === "monthly") {
        const months = Math.max(1, Math.ceil((days + 15) / 30));
        total = months * price;
    }

    if (display) display.innerText = fmtMoney(total);
}

// ============================================================
// 3. QUẢN LÝ HỢP ĐỒNG
// ============================================================
async function loadContracts() {
    try {
        const res = await fetch(`${API_URL}/contracts/`);
        if (!res.ok) return;

        const data = await res.json();
        const list = document.getElementById("contractList");
        if (! list) return;

        list.innerHTML = "";
        let totalRevenue = 0;
        let contractCount = 0;

        if (! Array.isArray(data) || data.length === 0) {
            list.innerHTML = `<div class="text-center text-muted py-4">📋 Chưa có hợp đồng nào</div>`;
        } else {
            for (const c of data) {
                contractCount++;
                let paid = 0;
                try {
                    const payRes = await fetch(`${API_URL}/contracts/${c.id}/payments`);
                    if (payRes.ok) {
                        const payments = await payRes.json();
                        if (Array.isArray(payments)) {
                            paid = payments.reduce((s, p) => s + p.amount, 0);
                        }
                    }
                } catch (err) {
                    console.error(err);
                }

                totalRevenue += paid;
                const percent = Math.min(100, (paid / (c.total_price || 1)) * 100);
                const progressColor = paid >= c.total_price ? '#10b981' : '#f59e0b';

                list.innerHTML += `
                    <div class="contract-item" onclick="openPaymentModal(${c.id}, '${c.status || 'active'}')">
                        <div class="contract-item-header">
                            <div class="contract-item-title">HĐ #${c.id}</div>
                            <span class="badge badge-success">${c.status || 'Active'}</span>
                        </div>
                        <div class="contract-item-dates">
                            <i class="fas fa-calendar"></i> ${c.start_date} → ${c.end_date}
                        </div>
                        <div class="contract-item-row">
                            <span class="contract-item-label">Tổng tiền:</span>
                            <span class="contract-item-value">${fmtMoney(c.total_price || 0)}</span>
                        </div>
                        <div class="contract-item-row">
                            <span class="contract-item-label">Đã thu:</span>
                            <span class="contract-item-value" style="color: #10b981;">${fmtMoney(paid)}</span>
                        </div>
                        <div class="progress">
                            <div class="progress-bar" style="background-color: ${progressColor}; width: ${percent}%"></div>
                        </div>
                        <div style="display: flex; gap: 6px;">
                            <button class="btn btn-primary w-100 btn-sm" onclick="openPaymentModal(${c.id}, '${c.status || 'active'}'); event.stopPropagation();">
                                <i class="fas fa-plus"></i> Nộp tiền
                            </button>
                            <button class="btn btn-info w-100 btn-sm" onclick="downloadContractPDF(${c.id}); event.stopPropagation();">
                                <i class="fas fa-download"></i> PDF
                            </button>
                        </div>
                    </div>
                `;
            }
        }

        document. getElementById("totalContracts").innerText = contractCount;
        document.getElementById("totalRevenue").innerText = fmtMoney(totalRevenue);

    } catch (err) {
        console.error(err);
    }
}

// Download PDF Hợp Đồng
function downloadContractPDF(contractId) {
    const url = `${API_URL}/contracts/${contractId}/download`;
    window.open(url, '_blank');
}

// Tạo Hợp Đồng
document.getElementById("contractForm")?.addEventListener("submit", async e => {
    e.preventDefault();
    const payload = {
        property_id: Number(document.getElementById("contractPropId").value),
        tenant_email: document.getElementById("contractEmail").value,
        start_date: document.getElementById("startDate").value,
        end_date: document.getElementById("endDate").value,
        deposit:  Number(document.getElementById("deposit").value) || 0,
        rental_type: document.querySelector('input[name="rentalType"]:checked').value
    };

    try {
        const res = await fetch(`${API_URL}/contracts/`, {
            method: "POST",
            headers: { "Content-Type":  "application/json" },
            body: JSON.stringify(payload)
        });

        if (res.ok) {
            showToast("✅ Ký hợp đồng thành công!");
            e.target.reset();
            document.getElementById("previewTotal").innerText = "0 đ";
            loadProperties();
            loadContracts();
        } else {
            const err = await res.json().catch(() => ({}));
            showToast("❌ " + (err.detail || "Lỗi tạo hợp đồng"), "error");
        }
    } catch (err) {
        console.error(err);
        showToast("❌ Lỗi kết nối", "error");
    }
});

// Xóa Hợp Đồng
async function deleteContract(id, event) {
    if (event) event.preventDefault();
    if (!confirm("Hủy hợp đồng này?")) return;
    
    try {
        const res = await fetch(`${API_URL}/contracts/${id}`, { method: "DELETE" });
        if (res.ok) {
            showToast("✅ Đã hủy hợp đồng");
            loadContracts();
            loadProperties();
        }
    } catch (err) {
        console.error(err);
    }
}

// ============================================================
// 4. THANH TOÁN
// ============================================================
function initPaymentModal() {
    const modalElem = document.getElementById("paymentModal");
    if (modalElem) {
        paymentModal = new bootstrap.Modal(modalElem);
    }
}

async function openPaymentModal(cid, status) {
    const modalDisplay = document.getElementById("modalContractIdDisplay");
    const payContractId = document.getElementById("payContractId");
    const modalStatus = document.getElementById("modalContractStatus");
    const payDate = document.getElementById("payDate");

    if (modalDisplay) modalDisplay.innerText = "#" + cid;
    if (payContractId) payContractId.value = cid;
    if (modalStatus) modalStatus.innerText = status;
    if (payDate) payDate.valueAsDate = new Date();

    let totalPrice = 0;
    let paid = 0;

    try {
        const contractRes = await fetch(`${API_URL}/contracts/`);
        if (contractRes.ok) {
            const contracts = await contractRes.json();
            const contract = contracts.find(c => c.id === cid);
            if (contract) {
                totalPrice = contract.total_price || 0;
            }
        }
    } catch (err) {
        console.error(err);
    }

    const tbody = document.getElementById("paymentHistoryList");
    if (tbody) tbody.innerHTML = "<tr><td colspan='4' class='text-center text-muted py-4'>Đang tải... </td></tr>";

    try {
        const res = await fetch(`${API_URL}/contracts/${cid}/payments`);
        if (res.ok) {
            const payments = await res.json();
            if (tbody) {
                tbody.innerHTML = "";
                if (! Array.isArray(payments) || payments.length === 0) {
                    tbody.innerHTML = "<tr><td colspan='4' class='text-center text-muted py-3'>Chưa có giao dịch</td></tr>";
                } else {
                    paid = payments.reduce((s, p) => s + p.amount, 0);
                    
                    payments.forEach(p => {
                        tbody.innerHTML += `
                            <tr>
                                <td><small>${p.payment_date || '-'}</small></td>
                                <td><small>${p.note || '-'}</small></td>
                                <td class="text-end"><small style="color: #10b981; font-weight: 600;">+${fmtMoney(p.amount)}</small></td>
                                <td class="text-center">
                                    <button class="btn btn-sm btn-warning" onclick="editPayment(${p.id}, ${cid})" title="Sửa">
                                        <i class="fas fa-edit"></i>
                                    </button>
                                    <button class="btn btn-sm btn-danger" onclick="deletePayment(${p.id}, ${cid})" title="Xóa">
                                        <i class="fas fa-trash"></i>
                                    </button>
                                </td>
                            </tr>
                        `;
                    });
                }
            }
        }
    } catch (e) {
        console.error(e);
    }

    const remaining = Math.max(0, totalPrice - paid);
    
    document.getElementById('totalPriceDisplay').innerText = fmtMoney(totalPrice);
    document.getElementById('paidDisplay').innerText = fmtMoney(paid);
    document.getElementById('remainingDisplay').innerText = fmtMoney(remaining);

    const statusMsg = document.getElementById('paymentStatus');
    if (remaining === 0) {
        statusMsg.innerHTML = '<i class="fas fa-check-circle"></i> ✅ Đã thanh toán đủ! ';
        statusMsg.style.background = '#d1fae5';
        statusMsg. style.color = '#065f46';
    } else {
        statusMsg.innerHTML = `<i class="fas fa-exclamation-circle"></i> 💡 Còn thiếu <strong>${fmtMoney(remaining)}</strong>`;
        statusMsg.style.background = '#fef08a';
        statusMsg.style. color = '#854d0e';
    }

    const payAmountInput = document.getElementById('payAmount');
    const payAmountHelper = document.getElementById('payAmountHelper');
    
    if (remaining > 0) {
        payAmountInput.value = remaining;
        payAmountInput.style.borderColor = '#f59e0b';
        payAmountHelper.innerHTML = `💡 <strong>Gợi ý: </strong> Còn thiếu <strong>${fmtMoney(remaining)}</strong>`;
        payAmountHelper.style.color = '#f59e0b';
    } else {
        payAmountInput.value = '';
        payAmountInput.style.borderColor = '';
        payAmountHelper.innerHTML = '✅ Hợp đồng đã được thanh toán đầy đủ';
        payAmountHelper.style.color = '#10b981';
    }

    // Load Damage Reports
    loadDamages(cid);

    if (paymentModal) paymentModal.show();
}

// Submit Thanh Toán
document.getElementById("paymentForm")?.addEventListener("submit", async e => {
    e.preventDefault();
    const cid = document.getElementById("payContractId")?.value;
    
    const payload = {
        contract_id: Number(cid),
        amount: Number(document.getElementById("payAmount").value),
        payment_date: document.getElementById("payDate").value,
        note: document. getElementById("payNote").value
    };

    try {
        const res = await fetch(`${API_URL}/payments/`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON. stringify(payload)
        });
        
        if (res.ok) {
            showToast("✅ Đã ghi nhận thanh toán");
            document.getElementById("payAmount").value = "";
            document.getElementById("payNote").value = "";
            openPaymentModal(cid);
            loadContracts();
        } else {
            showToast("❌ Lỗi thanh toán", "error");
        }
    } catch (err) {
        console.error(err);
        showToast("❌ Lỗi kết nối", "error");
    }
});

// Xóa Thanh Toán
async function deletePayment(paymentId, contractId) {
    if (!confirm("Xóa thanh toán này? ")) return;
    
    try {
        const res = await fetch(`${API_URL}/payments/${paymentId}`, { method: "DELETE" });
        if (res.ok) {
            showToast("✅ Đã xóa thanh toán");
            openPaymentModal(contractId);
            loadContracts();
        } else {
            showToast("❌ Không thể xóa", "error");
        }
    } catch (err) {
        console.error(err);
    }
}

// Sửa Thanh Toán
async function editPayment(paymentId, contractId) {
    const newAmount = prompt("Nhập số tiền mới:");
    if (! newAmount || isNaN(newAmount)) {
        showToast("Số tiền không hợp lệ", "error");
        return;
    }
    
    try {
        const res = await fetch(`${API_URL}/payments/${paymentId}`, { 
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                contract_id: contractId,
                amount: Number(newAmount),
                payment_date: new Date().toISOString().split('T')[0],
                note: "Sửa lại thanh toán"
            })
        });
        
        if (res.ok) {
            showToast("✅ Đã cập nhật thanh toán");
            openPaymentModal(contractId);
            loadContracts();
        } else {
            showToast("❌ Lỗi cập nhật", "error");
        }
    } catch (err) {
        console.error(err);
        showToast("❌ Lỗi", "error");
    }
}

// ============================================================
// 5. DAMAGE TRACKING
// ============================================================
async function loadDamages(contractId) {
    try {
        const res = await fetch(`${API_URL}/contracts/${contractId}/damages`);
        if (!res.ok) return;

        const damages = await res.json();
        const list = document.getElementById('damageList');
        list.innerHTML = '';

        if (damages.length === 0) {
            list.innerHTML = '<div class="text-center text-muted py-3">✅ Không có báo cáo hư hỏng nào</div>';
            return;
        }

        let totalCost = 0;
        damages.forEach((d) => {
            totalCost += d.repair_cost;
            const severityIcon = d.severity === 'high' ? '🔴' : d.severity === 'medium' ?  '🟡' : '🟢';
            const statusColor = d.status === 'pending' ? '#f59e0b' : d.status === 'repaired' ? '#10b981' : '#6b7280';

            list.innerHTML += `
                <div style="background:  white; border-left: 4px solid ${statusColor}; padding: 12px; margin-bottom: 10px; border-radius: 6px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                        <strong>${severityIcon} ${d.description}</strong>
                        <span style="background: ${statusColor}; color:  white; padding: 4px 10px; border-radius: 4px; font-size: 11px; font-weight: bold;">
                            ${d.status. toUpperCase()}
                        </span>
                    </div>
                    <div style="display: flex; justify-content: space-between; font-size: 12px; color: #6b7280; margin-bottom: 10px;">
                        <span>Ngày: ${d.reported_date}</span>
                        <span style="color: #ef4444; font-weight: bold;">Chi phí: ${fmtMoney(d.repair_cost)}</span>
                    </div>
                    <div style="display: flex; gap: 6px;">
                        ${d.status === 'pending' ? `
                            <button class="btn btn-sm btn-success" onclick="markRepaired(${d.id}, ${contractId})">
                                ✅ Đã sửa
                            </button>
                        ` : ''}
                        <button class="btn btn-sm btn-danger" onclick="deleteDamage(${d.id}, ${contractId})">
                            🗑️ Xóa
                        </button>
                    </div>
                </div>
            `;
        });

        if (totalCost > 0) {
            list.innerHTML += `
                <div style="background: #fee2e2; border:  2px solid #ef4444; padding: 12px; border-radius: 6px; margin-top: 10px;">
                    <strong style="color: #dc2626;">💰 Tổng chi phí sửa chữa: ${fmtMoney(totalCost)}</strong>
                </div>
            `;
        }
    } catch (err) {
        console.error(err);
    }
}

// Submit báo cáo hư hỏng
document. getElementById('damageForm')?.addEventListener('submit', async e => {
    e.preventDefault();
    const cid = document.getElementById('payContractId').value;
    
    let propertyId = 0;
    try {
        const res = await fetch(`${API_URL}/contracts/`);
        const contracts = await res.json();
        const contract = contracts.find(c => c.id === parseInt(cid));
        propertyId = contract?. property_id || 0;
    } catch (err) {
        console.error(err);
    }

    const payload = {
        contract_id: parseInt(cid),
        property_id: propertyId,
        description: document.getElementById('damageDesc').value,
        severity: document.getElementById('damageSeverity').value,
        repair_cost: Number(document.getElementById('repairCost').value) || 0,
        reported_date:  document.getElementById('damageDate').value
    };

    try {
        const res = await fetch(`${API_URL}/damage-reports/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (res.ok) {
            showToast('✅ Đã báo cáo hư hỏng');
            e.target.reset();
            loadDamages(cid);
        } else {
            showToast('❌ Lỗi báo cáo', 'error');
        }
    } catch (err) {
        console.error(err);
        showToast('❌ Lỗi kết nối', 'error');
    }
});

// Đánh dấu đã sửa
async function markRepaired(damageId, contractId) {
    try {
        const res = await fetch(`${API_URL}/damage-reports/${damageId}/mark-repaired`, { method: 'PATCH' });
        if (res.ok) {
            showToast('✅ Đã cập nhật trạng thái');
            loadDamages(contractId);
        }
    } catch (err) {
        console.error(err);
    }
}

// Xóa báo cáo hư hỏng
async function deleteDamage(damageId, contractId) {
    if (!confirm('Xóa báo cáo này?')) return;
    try {
        const res = await fetch(`${API_URL}/damage-reports/${damageId}`, { method: 'DELETE' });
        if (res.ok) {
            showToast('✅ Đã xóa báo cáo');
            loadDamages(contractId);
        }
    } catch (err) {
        console.error(err);
    }
}

// KHỞI CHẠY
window.addEventListener('DOMContentLoaded', () => {
    initPaymentModal();
    loadProperties();
    loadContracts();
    
    // Refresh dữ liệu mỗi 30 giây
    setInterval(() => {
        loadContracts();
    }, 30000);
});
