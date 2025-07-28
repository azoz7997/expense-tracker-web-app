// Global variables
let expenses = [];
let totalAmount = 0;

// DOM elements
const expenseForm = document.getElementById('expenseForm');
const descriptionInput = document.getElementById('description');
const amountInput = document.getElementById('amount');
const expensesList = document.getElementById('expensesList');
const emptyState = document.getElementById('emptyState');
const totalAmountElement = document.getElementById('totalAmount');
const expenseCountElement = document.getElementById('expenseCount');
const exportPdfBtn = document.getElementById('exportPdfBtn');
const clearAllBtn = document.getElementById('clearAllBtn');
const loadingOverlay = document.getElementById('loadingOverlay');
const toastContainer = document.getElementById('toastContainer');

// Initialize app
document.addEventListener('DOMContentLoaded', function() {
    loadExpenses();
    setupEventListeners();
});

// Setup event listeners
function setupEventListeners() {
    expenseForm.addEventListener('submit', handleAddExpense);
    exportPdfBtn.addEventListener('click', handleExportPdf);
    clearAllBtn.addEventListener('click', handleClearAll);
}

// Show loading overlay
function showLoading() {
    loadingOverlay.classList.add('show');
}

// Hide loading overlay
function hideLoading() {
    loadingOverlay.classList.remove('show');
}

// Show toast notification
function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    const icon = type === 'success' ? 'fa-check-circle' : 'fa-exclamation-circle';
    
    toast.innerHTML = `
        <i class="fas ${icon}"></i>
        <span>${message}</span>
    `;
    
    toastContainer.appendChild(toast);
    
    // Auto remove after 3 seconds
    setTimeout(() => {
        toast.remove();
    }, 3000);
}

// API calls
async function apiCall(endpoint, options = {}) {
    try {
        const response = await fetch(`/api${endpoint}`, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'حدث خطأ غير متوقع');
        }
        
        return data;
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

// Load expenses from API
async function loadExpenses() {
    try {
        showLoading();
        const data = await apiCall('/expenses');
        
        expenses = data.expenses || [];
        totalAmount = data.total || 0;
        
        renderExpenses();
        updateSummary();
        
    } catch (error) {
        showToast(`خطأ في تحميل المصاريف: ${error.message}`, 'error');
    } finally {
        hideLoading();
    }
}

// Add new expense
async function handleAddExpense(e) {
    e.preventDefault();
    
    const description = descriptionInput.value.trim();
    const amount = parseFloat(amountInput.value);
    
    if (!description) {
        showToast('يرجى إدخال وصف المصروف', 'error');
        return;
    }
    
    if (!amount || amount <= 0) {
        showToast('يرجى إدخال مبلغ صحيح', 'error');
        return;
    }
    
    try {
        showLoading();
        
        const data = await apiCall('/expenses', {
            method: 'POST',
            body: JSON.stringify({
                description: description,
                amount: amount
            })
        });
        
        showToast(data.message);
        
        // Reset form
        expenseForm.reset();
        descriptionInput.focus();
        
        // Reload expenses
        await loadExpenses();
        
    } catch (error) {
        showToast(`خطأ في إضافة المصروف: ${error.message}`, 'error');
    } finally {
        hideLoading();
    }
}

// Delete expense
async function deleteExpense(expenseId) {
    if (!confirm('هل أنت متأكد من حذف هذا المصروف؟')) {
        return;
    }
    
    try {
        showLoading();
        
        const data = await apiCall(`/expenses/${expenseId}`, {
            method: 'DELETE'
        });
        
        showToast(data.message);
        
        // Reload expenses
        await loadExpenses();
        
    } catch (error) {
        showToast(`خطأ في حذف المصروف: ${error.message}`, 'error');
    } finally {
        hideLoading();
    }
}

// Clear all expenses
async function handleClearAll() {
    if (!expenses.length) {
        showToast('لا توجد مصاريف لحذفها', 'error');
        return;
    }
    
    if (!confirm('هل أنت متأكد من حذف جميع المصاريف؟ هذا الإجراء لا يمكن التراجع عنه.')) {
        return;
    }
    
    try {
        showLoading();
        
        const data = await apiCall('/expenses/clear', {
            method: 'DELETE'
        });
        
        showToast(data.message);
        
        // Reload expenses
        await loadExpenses();
        
    } catch (error) {
        showToast(`خطأ في حذف المصاريف: ${error.message}`, 'error');
    } finally {
        hideLoading();
    }
}

// Export to HTML for printing
async function handleExportPdf() {
    if (!expenses.length) {
        showToast('لا توجد مصاريف للتصدير', 'error');
        return;
    }
    
    try {
        showLoading();
        
        // Open HTML export in new window for printing
        const url = '/api/expenses/export-html';
        window.open(url, '_blank');
        
        showToast('تم فتح التقرير للطباعة');
        
    } catch (error) {
        showToast(`خطأ في تصدير التقرير: ${error.message}`, 'error');
    } finally {
        hideLoading();
    }
}

// Render expenses list
function renderExpenses() {
    if (!expenses.length) {
        expensesList.innerHTML = `
            <div class="empty-state" id="emptyState">
                <i class="fas fa-receipt"></i>
                <p>لا توجد مصاريف حتى الآن</p>
                <small>ابدأ بإضافة أول مصروف لك</small>
            </div>
        `;
        return;
    }
    
    const expensesHtml = expenses.map(expense => {
        const date = new Date(expense.date_created);
        const formattedDate = date.toLocaleDateString('ar-SA', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
        
        return `
            <div class="expense-item">
                <div class="expense-info">
                    <div class="expense-description">${expense.description}</div>
                    <div class="expense-date">${formattedDate}</div>
                </div>
                <div class="expense-amount">${expense.amount.toFixed(2)} ريال</div>
                <div class="expense-actions">
                    <button class="btn btn-small btn-delete" onclick="deleteExpense(${expense.id})">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </div>
        `;
    }).join('');
    
    expensesList.innerHTML = expensesHtml;
}

// Update summary
function updateSummary() {
    totalAmountElement.textContent = `${totalAmount.toFixed(2)} ريال`;
    
    const count = expenses.length;
    const countText = count === 0 ? 'لا توجد مصاريف' : 
                     count === 1 ? 'مصروف واحد' : 
                     count === 2 ? 'مصروفان' : 
                     count <= 10 ? `${count} مصاريف` : 
                     `${count} مصروف`;
    
    expenseCountElement.textContent = countText;
}

// Format number with Arabic locale
function formatCurrency(amount) {
    return new Intl.NumberFormat('ar-SA', {
        style: 'currency',
        currency: 'SAR',
        minimumFractionDigits: 2
    }).format(amount);
}

// Auto-focus on description input
descriptionInput.focus();

