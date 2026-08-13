//==============================================================================
// 1. CONSTANTS & STATE MANAGEMENT
//==============================================================================
const SUGGESTIONS = [
    "Cuisine",
    "Protection Bas De L'évier",
    "Accessoire Apoon",
    "Tiroir à Épices",
    "Système De Gaz",
    "Séparation",
    "Tiroir"
];

let focusedDesc = null;
let acDropdown = null;
let acTarget = null;
let currentInvoiceId = null;

//==============================================================================
// 2. INITIALIZATION & THEME MANAGEMENT
//==============================================================================
document.addEventListener('DOMContentLoaded', () => {
    // Theme Initialization
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-bs-theme', savedTheme);
    updateThemeIcon(savedTheme);

    document.getElementById('themeToggle')?.addEventListener('click', toggleTheme);
    document.getElementById('mobileThemeToggle')?.addEventListener('click', toggleTheme);

    // Responsive Sidebar Initialization
    initSidebar();

    // General UI Utilities Initialization
    initUIUtilities();

    // Description Drag-and-Drop Initialization
    if (document.getElementById('descriptions-sortable')) {
        initDescriptionSortable();
    }

    // Invoice Generator Initialization (only if invoice form exists)
    if (document.getElementById('invoice-form') || document.getElementById('items-body')) {
        initInvoiceApp();
    }
});

function toggleTheme() {
    const current = document.documentElement.getAttribute('data-bs-theme');
    const next = current === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-bs-theme', next);
    localStorage.setItem('theme', next);
    updateThemeIcon(next);
}

function updateThemeIcon(theme) {
    const icon = theme === 'dark' ? 'bi-sun' : 'bi-moon-stars';
    document.querySelectorAll('#themeToggle i, #mobileThemeToggle i').forEach(el => {
        el.className = 'bi ' + icon;
    });
}

//==============================================================================
// 3. RESPONSIVE NAVIGATION & MOBILE UI
//==============================================================================
function initSidebar() {
    const mobileToggle = document.getElementById('mobileMenuToggle');
    const mobileBottomToggle = document.getElementById('mobileBottomMenuToggle');
    const sidebarCloseBtn = document.getElementById('sidebarCloseBtn');
    const sidebar = document.getElementById('sidebar');

    let overlay = document.querySelector('.sidebar-overlay');
    if (!overlay) {
        overlay = document.createElement('div');
        overlay.className = 'sidebar-overlay';
        document.body.appendChild(overlay);
    }

    function openSidebar() {
        sidebar?.classList.add('show');
        overlay.classList.add('show');
        document.body.style.overflow = 'hidden';
    }

    function closeSidebar() {
        sidebar?.classList.remove('show');
        overlay.classList.remove('show');
        document.body.style.overflow = '';
    }

    function toggleSidebar() {
        if (sidebar?.classList.contains('show')) {
            closeSidebar();
        } else {
            openSidebar();
        }
    }

    mobileToggle?.addEventListener('click', toggleSidebar);
    mobileBottomToggle?.addEventListener('click', toggleSidebar);
    sidebarCloseBtn?.addEventListener('click', closeSidebar);
    overlay.addEventListener('click', closeSidebar);

    // Preserve sidebar scroll position across page navigation
    if (sidebar) {
        const savedScrollPos = sessionStorage.getItem('sidebarScrollPos');
        if (savedScrollPos !== null) {
            sidebar.scrollTop = parseInt(savedScrollPos, 10);
        }

        sidebar.addEventListener('scroll', () => {
            sessionStorage.setItem('sidebarScrollPos', sidebar.scrollTop);
        }, { passive: true });
    }

    // Auto-close sidebar on mobile when navigating via sidebar link & save scroll position
    document.querySelectorAll('#sidebar .nav-link, #sidebar a').forEach(link => {
        link.addEventListener('click', () => {
            if (sidebar) {
                sessionStorage.setItem('sidebarScrollPos', sidebar.scrollTop);
            }
            if (window.innerWidth < 992) {
                closeSidebar();
            }
        });
    });

    // Touch swipe left to close sidebar on mobile
    let touchStartX = 0;
    sidebar?.addEventListener('touchstart', (e) => {
        touchStartX = e.changedTouches[0].screenX;
    }, { passive: true });

    sidebar?.addEventListener('touchend', (e) => {
        const touchEndX = e.changedTouches[0].screenX;
        if (touchStartX - touchEndX > 50) {
            closeSidebar();
        }
    }, { passive: true });
}

//==============================================================================
// 4. ALERTS, TOOLTIPS & CONFIRMATION MODAL
//==============================================================================
function initUIUtilities() {
    // Universal Submit Protection & Loading State for all POST forms
    document.addEventListener('submit', function (e) {
        const form = e.target;
        if (!form || form.tagName !== 'FORM') return;

        // Skip GET forms (like search filters)
        if (form.method && form.method.toUpperCase() === 'GET') return;

        // Prevent double submission if form is already submitting
        if (form.dataset.submitting === 'true') {
            e.preventDefault();
            e.stopPropagation();
            return false;
        }

        form.dataset.submitting = 'true';

        // Find primary submit button
        const submitBtn = form.querySelector('button[type="submit"], input[type="submit"]');
        if (submitBtn) {
            if (submitBtn.disabled) {
                e.preventDefault();
                return false;
            }
            submitBtn.disabled = true;
            submitBtn.dataset.originalHtml = submitBtn.innerHTML;
            submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Enregistrement...';
        }

        // Disable cancel/secondary buttons to prevent double click
        form.querySelectorAll('.btn-outline-secondary, a.btn, button:not([type="submit"])').forEach(btn => {
            if (btn.tagName === 'BUTTON') btn.disabled = true;
            btn.classList.add('disabled');
            btn.setAttribute('aria-disabled', 'true');
        });
    });

    // Alert dismissal
    document.querySelectorAll('[data-bs-dismiss="alert"]').forEach(btn => {
        btn.addEventListener('click', () => {
            setTimeout(() => {
                document.querySelectorAll('.alert').forEach(a => {
                    if (!a.closest('.show')) a.remove();
                });
            }, 300);
        });
    });

    // Auto-remove flash alerts after 5s
    setTimeout(() => {
        document.querySelectorAll('.alert').forEach(el => {
            el.classList.remove('show');
            setTimeout(() => { el.remove(); }, 300);
        });
    }, 5000);

    // Confirmation buttons safety check
    document.querySelectorAll('.btn-outline-danger[onclick]').forEach(btn => {
        btn.addEventListener('click', function(e) {
            if (!this.closest('form') && this.getAttribute('onclick')?.includes('confirmDelete')) {
                e.preventDefault();
            }
        });
    });

    // Tooltips
    const tooltips = document.querySelectorAll('[title]');
    tooltips.forEach(el => {
        if (!el.closest('.dataTable') && !el.closest('table')) {
            new bootstrap.Tooltip(el, { trigger: 'hover', delay: { show: 500, hide: 100 } });
        }
    });
}

function initDescriptionSortable() {
    const sortableEl = document.getElementById('descriptions-sortable');
    const saveBtn = document.getElementById('btn-save-order');
    const unsavedBadge = document.getElementById('unsaved-badge');
    if (!sortableEl || !saveBtn) return;

    let hasUnsavedChanges = false;

    function updateRowNumbers() {
        const rows = sortableEl.querySelectorAll('.sortable-item');
        rows.forEach((row, index) => {
            const numEl = row.querySelector('.row-number');
            if (numEl) numEl.textContent = index + 1;
        });
    }

    function setUnsaved(state) {
        hasUnsavedChanges = state;
        if (state) {
            saveBtn.removeAttribute('disabled');
            unsavedBadge?.classList.remove('d-none');
        } else {
            saveBtn.setAttribute('disabled', 'true');
            unsavedBadge?.classList.add('d-none');
        }
    }

    window.addEventListener('beforeunload', (e) => {
        if (hasUnsavedChanges) {
            e.preventDefault();
            e.returnValue = 'Vous avez des modifications non enregistrées. Voulez-vous quitter cette page ?';
            return e.returnValue;
        }
    });

    if (typeof Sortable !== 'undefined') {
        new Sortable(sortableEl, {
            handle: '.drag-handle',
            animation: 150,
            ghostClass: 'table-active',
            chosenClass: 'table-warning',
            dragClass: 'shadow-lg',
            delay: 150,
            delayOnTouchOnly: true,
            touchStartThreshold: 5,
            onEnd: function () {
                updateRowNumbers();
                setUnsaved(true);
            }
        });
    }

    saveBtn.addEventListener('click', async function () {
        if (!hasUnsavedChanges) return;

        const rows = sortableEl.querySelectorAll('.sortable-item');
        const orderPayload = [];
        rows.forEach((row, index) => {
            const id = parseInt(row.getAttribute('data-id'), 10);
            if (id) {
                orderPayload.push({ id: id, sort_order: index + 1 });
            }
        });

        saveBtn.disabled = true;
        saveBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1" role="status" aria-hidden="true"></span>Enregistrement...';

        try {
            const response = await fetch('/categories/descriptions/reorder', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfToken()
                },
                body: JSON.stringify({ order: orderPayload })
            });

            const result = await response.json();
            if (response.ok && result.success) {
                setUnsaved(false);
                saveBtn.innerHTML = '<i class="bi bi-check-circle me-1"></i>Enregistrer l\'ordre';
                if (typeof Swal !== 'undefined') {
                    Swal.fire({
                        icon: 'success',
                        title: 'Succès',
                        text: result.message || 'Ordre enregistré avec succès.',
                        timer: 2000,
                        showConfirmButton: false
                    });
                } else {
                    alert(result.message || 'Ordre enregistré avec succès.');
                }
            } else {
                setUnsaved(true);
                saveBtn.innerHTML = '<i class="bi bi-check-circle me-1"></i>Enregistrer l\'ordre';
                alert(result.message || 'Erreur lors de l\'enregistrement de l\'ordre.');
            }
        } catch (err) {
            setUnsaved(true);
            saveBtn.innerHTML = '<i class="bi bi-check-circle me-1"></i>Enregistrer l\'ordre';
            alert('Erreur réseau lors de la communication avec le serveur.');
        }
    });
}

function confirmDelete(target, message, options = {}) {
    const modalEl = document.getElementById('deleteModal');
    if (!modalEl) return;
    
    const modal = bootstrap.Modal.getInstance(modalEl) || new bootstrap.Modal(modalEl);
    const form = document.getElementById('deleteForm');
    const msgEl = document.getElementById('deleteModalMessage');
    const titleEl = modalEl.querySelector('.modal-title');
    const submitBtn = form ? form.querySelector('button[type="submit"]') : null;
    
    if (msgEl) {
        msgEl.textContent = message || "Êtes-vous sûr de vouloir supprimer cet élément ? Cette action est irréversible.";
    }

    if (titleEl) {
        titleEl.textContent = options.title || "Confirmer la suppression";
    }

    if (submitBtn) {
        submitBtn.textContent = options.btnText || "Supprimer";
        submitBtn.className = `btn ${options.btnClass || 'btn-danger'}`;
    }
    
    if (form) {
        form.onsubmit = null;
        if (typeof target === 'function') {
            form.action = '#';
            form.onsubmit = function(e) {
                e.preventDefault();
                modal.hide();
                target();
            };
        } else if (target) {
            form.action = target;
        } else {
            form.action = '#';
            form.onsubmit = function(e) {
                e.preventDefault();
                modal.hide();
            };
        }
    }
    
    modal.show();
}

function formatCurrency(amount) {
    return new Intl.NumberFormat('fr-MA', { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(amount) + ' DH';
}

//==============================================================================
// 5. INVOICE CALCULATIONS & CALCULATOR LOGIC
//==============================================================================
function formatNumber(n) {
    const val = Number(n) || 0;
    const showDec = window.SHOW_DECIMALS || false;
    if (showDec) {
        return val.toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ' ');
    } else {
        if (Number.isInteger(val)) {
            return val.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ' ');
        }
        return val.toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ' ');
    }
}

function calculateRow(tr) {
    const qty = parseFloat(tr.querySelector('.item-qty')?.value) || 0;
    const price = parseFloat(tr.querySelector('.item-price')?.value) || 0;
    const totalEl = tr.querySelector('.item-total');
    if (totalEl) {
        totalEl.textContent = formatNumber(qty * price);
    }
}

function calculateTotal() {
    let total = 0;
    document.querySelectorAll('.item-total').forEach(el => {
        total += parseFloat(el.textContent.replace(/\s/g, '')) || 0;
    });
    const grandTotalEl = document.getElementById('grand-total');
    if (grandTotalEl) {
        grandTotalEl.querySelector('small').parentElement.firstChild.textContent = formatNumber(total);
    }
    calculateNetTotal();
}

function calculateNetTotal() {
    const grandTotalEl = document.getElementById('grand-total');
    if (!grandTotalEl) return;

    const base = parseFloat(grandTotalEl.textContent.replace(/\s/g, '')) || 0;
    const remiseToggle = document.getElementById('remise-toggle');
    const remiseAmount = document.getElementById('remise-amount');
    const payerToggle = document.getElementById('payer-toggle');
    const payerAmount = document.getElementById('payer-amount');

    const remise = remiseToggle?.checked ? (parseFloat(remiseAmount?.value) || 0) : 0;
    const payer = payerToggle?.checked ? (parseFloat(payerAmount?.value) || 0) : 0;
    const net = Math.max(0, base - remise - payer);

    const netTotalEl = document.getElementById('net-total');
    if (netTotalEl) {
        netTotalEl.querySelector('small').parentElement.firstChild.textContent = formatNumber(net);
    }
}

function calculateAll() {
    document.querySelectorAll('#items-body tr').forEach(tr => {
        calculateRow(tr);
    });
    calculateTotal();
    calculateNetTotal();
}

//==============================================================================
// 6. AUTOCOMPLETE & DROPDOWN POSITIONING
//==============================================================================
function createAcDropdown() {
    if (document.querySelector('.ac-dropdown')) {
        acDropdown = document.querySelector('.ac-dropdown');
        return;
    }
    acDropdown = document.createElement('div');
    acDropdown.className = 'ac-dropdown';
    document.body.appendChild(acDropdown);
}

function positionDropdown(input) {
    if (!input || !acDropdown) return;
    const rect = input.getBoundingClientRect();
    const isMobile = window.innerWidth < 768;
    const dropdownHeight = acDropdown.offsetHeight || 180;

    const spaceBelow = window.innerHeight - rect.bottom;
    const spaceAbove = rect.top;

    let top = rect.bottom;
    if (spaceBelow < dropdownHeight && spaceAbove > dropdownHeight && !isMobile) {
        top = rect.top - dropdownHeight;
    }

    acDropdown.style.top = Math.max(0, top) + 'px';
    acDropdown.style.left = Math.max(8, rect.left) + 'px';
    acDropdown.style.width = Math.min(rect.width, window.innerWidth - 16) + 'px';
}

function closeAcDropdown() {
    if (acDropdown) acDropdown.classList.remove('active');
    if (acTarget) acTarget.classList.remove('ac-open');
    acTarget = null;
}

function filterSuggestions(input) {
    acTarget = input;
    const val = input.value.trim().toLowerCase();

    if (!acDropdown) createAcDropdown();
    acDropdown.innerHTML = '';

    const filtered = SUGGESTIONS.filter(s => s.toLowerCase().includes(val));

    if (filtered.length === 0 && val === '') {
        SUGGESTIONS.forEach(s => addAcItem(s, input));
    } else if (filtered.length > 0) {
        filtered.forEach(s => addAcItem(s, input));
    } else {
        SUGGESTIONS.forEach(s => addAcItem(s, input));
    }

    if (val) {
        const otherItem = document.createElement('div');
        otherItem.className = 'suggestion-item suggestion-other';
        otherItem.textContent = `Autre: "${input.value}"`;
        otherItem.addEventListener('click', () => {
            closeAcDropdown();
            input.focus();
        });
        acDropdown.appendChild(otherItem);
    }

    acDropdown.classList.add('active');
    input.classList.add('ac-open');
    positionDropdown(input);
}

function addAcItem(text, input) {
    const item = document.createElement('div');
    item.className = 'suggestion-item';
    item.textContent = text;
    item.addEventListener('click', () => {
        input.value = text;
        closeAcDropdown();
        input.focus();
    });
    acDropdown.appendChild(item);
}

//==============================================================================
// 7. DYNAMIC INVOICE ITEMS (ROWS MANAGER)
//==============================================================================
function initInvoiceApp() {
    const dateEl = document.getElementById('date');
    if (dateEl && !dateEl.value) {
        dateEl.value = new Date().toISOString().split('T')[0];
    }
    
    calculateAll();

    const remiseAmount = document.getElementById('remise-amount');
    const payerAmount = document.getElementById('payer-amount');
    if (remiseAmount) remiseAmount.disabled = true;
    if (payerAmount) payerAmount.disabled = true;

    createAcDropdown();

    // Attach Autocomplete Scroll and Resize Listeners
    window.addEventListener('scroll', () => {
        if (acTarget && acDropdown && acDropdown.classList.contains('active')) {
            positionDropdown(acTarget);
        }
    }, { passive: true });

    window.addEventListener('resize', () => {
        if (acTarget && acDropdown && acDropdown.classList.contains('active')) {
            positionDropdown(acTarget);
        }
    });

    // Delegation on items-body for calculations & autocomplete
    const itemsBody = document.getElementById('items-body');
    if (itemsBody) {
        itemsBody.addEventListener('input', (e) => {
            if (e.target.classList.contains('item-qty') || e.target.classList.contains('item-price')) {
                calculateRow(e.target.closest('tr'));
                calculateTotal();
            }
            if (e.target.classList.contains('item-desc')) {
                filterSuggestions(e.target);
            }
        });

        itemsBody.addEventListener('mousedown', (e) => {
            if (e.target.classList.contains('item-desc')) {
                focusedDesc = e.target;
            }
        });

        itemsBody.addEventListener('focusin', (e) => {
            if (e.target.classList.contains('item-desc')) {
                focusedDesc = e.target;
                filterSuggestions(e.target);
            }
        });

        itemsBody.addEventListener('keydown', (e) => {
            if (!e.target.classList.contains('item-desc')) return;

            if (e.key === 'Escape') {
                closeAcDropdown();
                return;
            }

            if (!acDropdown || !acDropdown.classList.contains('active')) return;

            const items = acDropdown.querySelectorAll('.suggestion-item');
            if (!items.length) return;

            const currentIndex = Array.from(items).indexOf(acDropdown.querySelector('.suggestion-item.selected'));

            if (e.key === 'ArrowDown') {
                e.preventDefault();
                const next = currentIndex < items.length - 1 ? currentIndex + 1 : 0;
                items.forEach(i => i.classList.remove('selected'));
                items[next].classList.add('selected');
                items[next].scrollIntoView({ block: 'nearest' });
            } else if (e.key === 'ArrowUp') {
                e.preventDefault();
                const prev = currentIndex > 0 ? currentIndex - 1 : items.length - 1;
                items.forEach(i => i.classList.remove('selected'));
                items[prev].classList.add('selected');
                items[prev].scrollIntoView({ block: 'nearest' });
            } else if (e.key === 'Enter') {
                const selected = acDropdown.querySelector('.suggestion-item.selected');
                if (selected) {
                    e.preventDefault();
                    selected.click();
                }
            }
        });

        itemsBody.addEventListener('click', (e) => {
            if (e.target.classList.contains('btn-remove')) {
                const rows = document.querySelectorAll('#items-body tr');
                if (rows.length > 1) {
                    e.target.closest('tr').remove();
                    calculateTotal();
                }
            }
        });
    }

    // Click outside handler for autocomplete
    document.addEventListener('click', (e) => {
        if (e.target === focusedDesc) {
            focusedDesc = null;
            return;
        }
        focusedDesc = null;
        if (!e.target.closest('.ac-dropdown') && e.target !== acTarget) {
            closeAcDropdown();
        }
    });

    // Discount & Payment Toggles
    document.getElementById('remise-toggle')?.addEventListener('change', () => {
        const enabled = document.getElementById('remise-toggle').checked;
        const input = document.getElementById('remise-amount');
        if (input) {
            input.disabled = !enabled;
            if (!enabled) input.value = 0;
        }
        calculateNetTotal();
    });

    document.getElementById('remise-amount')?.addEventListener('input', calculateNetTotal);

    document.getElementById('payer-toggle')?.addEventListener('change', () => {
        const enabled = document.getElementById('payer-toggle').checked;
        const input = document.getElementById('payer-amount');
        if (input) {
            input.disabled = !enabled;
            if (!enabled) input.value = 0;
        }
        calculateNetTotal();
    });

    document.getElementById('payer-amount')?.addEventListener('input', calculateNetTotal);

    // Add Row Button
    document.getElementById('btn-add-item')?.addEventListener('click', () => {
        const tbody = document.getElementById('items-body');
        if (!tbody) return;
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td><div class="desc-wrapper"><input type="text" class="item-desc" placeholder="Description" required><div class="suggestion-list"></div></div></td>
            <td><input type="number" class="item-qty" value="1" min="0" step="any" required></td>
            <td><input type="number" class="item-price" value="0" min="0" step="any" required></td>
            <td class="item-total">0.00</td>
            <td><button type="button" class="btn-remove" title="Supprimer">&times;</button></td>
        `;
        tbody.appendChild(tr);

        const descInput = tr.querySelector('.item-desc');
        descInput?.focus();
        setTimeout(() => {
            if (descInput) filterSuggestions(descInput);
        }, 50);

        tr.querySelectorAll('.item-qty, .item-price').forEach(el => {
            el.addEventListener('input', () => {
                calculateRow(tr);
                calculateTotal();
            });
        });
        tr.querySelector('.btn-remove')?.addEventListener('click', () => {
            tr.remove();
            calculateTotal();
        });
    });

    // Check for Edit parameter in URL
    const params = new URLSearchParams(window.location.search);
    const editId = params.get('edit');
    if (editId) {
        loadInvoiceForEdit(parseInt(editId, 10));
    }

    // Modal & Action Buttons setup
    document.getElementById('btn-preview')?.addEventListener('click', handleInvoicePreview);
    document.getElementById('btn-pdf')?.addEventListener('click', handleInvoicePdfDownload);
    document.getElementById('btn-excel')?.addEventListener('click', handleInvoiceExcelDownload);
    document.getElementById('btn-save')?.addEventListener('click', handleInvoiceSave);

    document.querySelector('.modal-close')?.addEventListener('click', () => {
        document.getElementById('preview-modal')?.classList.remove('active');
    });

    document.getElementById('preview-modal')?.addEventListener('click', (e) => {
        if (e.target === e.currentTarget) {
            document.getElementById('preview-modal')?.classList.remove('active');
        }
    });
}

//==============================================================================
// 8. INVOICE FORM DATA & API HANDLERS (SAVE, EDIT, PREVIEW, EXPORTS)
//==============================================================================
function getFormData() {
    const items = [];
    document.querySelectorAll('#items-body tr').forEach(tr => {
        const desc = tr.querySelector('.item-desc')?.value.trim();
        const qty = parseFloat(tr.querySelector('.item-qty')?.value) || 0;
        const price = parseFloat(tr.querySelector('.item-price')?.value) || 0;
        if (desc) {
            items.push({ description: desc, quantity: qty, unit_price: price, total: qty * price });
        }
    });

    const baseTotal = items.reduce((s, i) => s + i.total, 0);
    const remiseEnabled = document.getElementById('remise-toggle')?.checked || false;
    const remiseAmount = remiseEnabled ? (parseFloat(document.getElementById('remise-amount')?.value) || 0) : 0;
    const payerEnabled = document.getElementById('payer-toggle')?.checked || false;
    const payerAmount = payerEnabled ? (parseFloat(document.getElementById('payer-amount')?.value) || 0) : 0;
    const netTotal = Math.max(0, baseTotal - remiseAmount - payerAmount);

    const data = {
        invoice_num: document.getElementById('invoice_num')?.value.trim() || '001',
        show_facture_num: document.getElementById('show-facture-num')?.checked || false,
        date: document.getElementById('date')?.value || new Date().toISOString().split('T')[0],
        client_name: document.getElementById('client_name')?.value.trim() || 'Client',
        client_address: document.getElementById('client_address')?.value.trim() || '',
        items: items,
        total: baseTotal,
        remise_enabled: remiseEnabled,
        remise: remiseAmount,
        payer_enabled: payerEnabled,
        payer: payerAmount,
        net_total: netTotal,
        request_token: document.getElementById('invoice_request_token')?.value || ''
    };

    if (currentInvoiceId !== null) {
        data.id = currentInvoiceId;
    }

    return data;
}

async function loadInvoiceForEdit(invoiceId) {
    try {
        const res = await fetch(`/invoices/${invoiceId}/json`);
        if (!res.ok) { alert('Facture introuvable.'); return; }
        const inv = await res.json();

        currentInvoiceId = inv.id;

        const invNum = document.getElementById('invoice_num');
        const dateEl = document.getElementById('date');
        const clientName = document.getElementById('client_name');
        const clientAddr = document.getElementById('client_address');
        const showNumToggle = document.getElementById('show-facture-num');

        if (invNum) invNum.value = inv.invoice_num || '';
        if (dateEl) dateEl.value = inv.date || '';
        if (clientName) clientName.value = inv.client_name || '';
        if (clientAddr) clientAddr.value = inv.client_address || '';
        if (showNumToggle) showNumToggle.checked = !!inv.show_facture_num;

        const tbody = document.getElementById('items-body');
        if (tbody) {
            tbody.innerHTML = '';
            const itemsArr = Array.isArray(inv.items) && inv.items.length > 0
                ? inv.items
                : [{ description: '', quantity: 1, unit_price: 0, total: 0 }];

            itemsArr.forEach(item => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td><div class="desc-wrapper"><input type="text" class="item-desc" placeholder="Description" required><div class="suggestion-list"></div></div></td>
                    <td><input type="number" class="item-qty" value="1" min="0" step="any" required></td>
                    <td><input type="number" class="item-price" value="0" min="0" step="any" required></td>
                    <td class="item-total">0.00</td>
                    <td><button type="button" class="btn-remove" title="Supprimer">&times;</button></td>
                `;
                tbody.appendChild(tr);
                tr.querySelector('.item-desc').value = item.description || '';
                tr.querySelector('.item-qty').value = item.quantity ?? 1;
                tr.querySelector('.item-price').value = item.unit_price ?? 0;
                tr.querySelector('.btn-remove')?.addEventListener('click', () => {
                    if (document.querySelectorAll('#items-body tr').length > 1) {
                        tr.remove();
                        calculateTotal();
                    }
                });
            });
        }

        const remise = inv.remise || 0;
        const payer = inv.payer || 0;
        const remiseToggle = document.getElementById('remise-toggle');
        const remiseInput = document.getElementById('remise-amount');
        const payerToggle = document.getElementById('payer-toggle');
        const payerInput = document.getElementById('payer-amount');

        if (remise > 0 && remiseToggle && remiseInput) {
            remiseToggle.checked = true;
            remiseInput.disabled = false;
            remiseInput.value = remise;
        }
        if (payer > 0 && payerToggle && payerInput) {
            payerToggle.checked = true;
            payerInput.disabled = false;
            payerInput.value = payer;
        }

        calculateAll();

        const saveBtn = document.getElementById('btn-save');
        if (saveBtn) {
            saveBtn.textContent = '💾 Mettre à jour';
            saveBtn.title = `Modification de la facture ID ${inv.id}`;
        }

        window.scrollTo({ top: 0, behavior: 'smooth' });

    } catch (err) {
        console.error(err);
        alert('Erreur lors du chargement de la facture pour modification.');
    }
}

function getCsrfToken() {
    const meta = document.querySelector('meta[name="csrf-token"]');
    return meta ? meta.getAttribute('content') : '';
}

function getFilenameFromHeaders(res) {
    const cd = res.headers.get('Content-Disposition');
    if (!cd) return null;
    const match = cd.match(/filename\*?=(?:UTF-8'')?["']?([^"';]+)["']?/);
    return match ? match[1] : null;
}

async function handleInvoicePreview() {
    const data = getFormData();
    if (!data.items.length) return alert('Ajoutez au moins un article.');

    try {
        const res = await fetch('/invoices/preview', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify(data)
        });
        const html = await res.text();
        const modal = document.getElementById('preview-modal');
        const body = document.getElementById('preview-body');
        if (body) body.innerHTML = html;
        modal?.classList.add('active');
    } catch (e) {
        alert('Erreur lors de la génération de l\'aperçu.');
    }
}

async function handleInvoicePdfDownload() {
    const data = getFormData();
    if (!data.items.length) return alert('Ajoutez au moins un article.');

    const wasEditing = currentInvoiceId !== null;

    let savedId;
    try {
        const saveRes = await fetch('/invoices/save', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify(data)
        });
        const saveResult = await saveRes.json();
        if (!saveResult || !saveResult.id) {
            alert("Erreur lors de l'enregistrement de la facture. Le PDF n'a pas été généré.");
            return;
        }
        savedId = saveResult.id;
    } catch (e) {
        alert("Erreur lors de l'enregistrement de la facture. Le PDF n'a pas été généré.");
        return;
    }

    try {
        const pdfRes = await fetch(`/invoices/${savedId}/pdf`);
        const blob = await pdfRes.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = getFilenameFromHeaders(pdfRes) || `facture_${data.invoice_num}.pdf`;
        a.click();
        URL.revokeObjectURL(url);
    } catch (e) {
        alert('Erreur lors de la génération du PDF.');
        return;
    }

    if (wasEditing) {
        showSuccessBanner(`Facture mise à jour et PDF téléchargé. ID : ${savedId}`);
    } else {
        resetFormToNewInvoice();
    }
}

async function handleInvoiceExcelDownload() {
    const data = getFormData();
    if (!data.items.length) return alert('Ajoutez au moins un article.');

    try {
        const res = await fetch('/invoices/generate_excel', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify(data)
        });
        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = getFilenameFromHeaders(res) || `facture_${data.invoice_num}.xlsx`;
        a.click();
        URL.revokeObjectURL(url);
    } catch (e) {
        alert('Erreur lors de la génération du fichier Excel.');
    }
}

let isInvoiceSaving = false;
async function handleInvoiceSave() {
    if (isInvoiceSaving) return;

    const data = getFormData();
    if (!data.items.length) {
        showErrorBanner('Ajoutez au moins un article.');
        return;
    }

    const saveBtn = document.getElementById('btn-save');
    const wasEditing = currentInvoiceId !== null;
    let origHtml = '';

    if (saveBtn) {
        if (saveBtn.disabled) return;
        saveBtn.disabled = true;
        origHtml = saveBtn.innerHTML;
        saveBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Saving...';
    }

    isInvoiceSaving = true;

    try {
        const res = await fetch('/invoices/save', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken(),
                'X-Request-Token': data.request_token || ''
            },
            body: JSON.stringify(data)
        });
        const result = await res.json();
        if (result && result.id) {
            if (wasEditing) {
                window.location.href = result.redirect || '/invoices/';
            } else {
                resetFormToNewInvoice();
            }
        } else {
            const msg = result && result.error ? result.error : "Erreur lors de l'enregistrement de la facture.";
            showErrorBanner(msg);
            if (saveBtn) {
                saveBtn.disabled = false;
                saveBtn.innerHTML = origHtml;
            }
        }
    } catch (e) {
        showErrorBanner("Erreur lors de l'enregistrement de la facture.");
        console.error(e);
        if (saveBtn) {
            saveBtn.disabled = false;
            saveBtn.innerHTML = origHtml;
        }
    } finally {
        isInvoiceSaving = false;
    }
}

function resetFormToNewInvoice() {
    currentInvoiceId = null;

    const invNum = document.getElementById('invoice_num');
    const dateEl = document.getElementById('date');
    const clientName = document.getElementById('client_name');
    const clientAddr = document.getElementById('client_address');
    const showNumToggle = document.getElementById('show-facture-num');

    if (invNum) invNum.value = '001';
    if (dateEl) dateEl.value = new Date().toISOString().split('T')[0];
    if (clientName) clientName.value = '';
    if (clientAddr) clientAddr.value = '';
    if (showNumToggle) showNumToggle.checked = false;

    const tbody = document.getElementById('items-body');
    if (tbody) {
        tbody.innerHTML = `
            <tr>
                <td><div class="desc-wrapper"><input type="text" class="item-desc" placeholder="Description" required><div class="suggestion-list"></div></div></td>
                <td><input type="number" class="item-qty" value="1" min="0" step="any" required></td>
                <td><input type="number" class="item-price" value="0" min="0" step="any" required></td>
                <td class="item-total">0.00</td>
                <td><button type="button" class="btn-remove" title="Supprimer">&times;</button></td>
            </tr>
        `;
    }

    const remiseToggle = document.getElementById('remise-toggle');
    const remiseAmount = document.getElementById('remise-amount');
    const payerToggle = document.getElementById('payer-toggle');
    const payerAmount = document.getElementById('payer-amount');

    if (remiseToggle) remiseToggle.checked = false;
    if (remiseAmount) { remiseAmount.value = 0; remiseAmount.disabled = true; }
    if (payerToggle) payerToggle.checked = false;
    if (payerAmount) { payerAmount.value = 0; payerAmount.disabled = true; }

    calculateAll();

    const saveBtn = document.getElementById('btn-save');
    if (saveBtn) {
        saveBtn.textContent = 'Enregistrer';
        saveBtn.title = '';
    }

    showSuccessBanner('Facture enregistrée avec succès. Vous pouvez créer une nouvelle facture.');
    document.getElementById('client_name')?.focus();
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

function showSuccessBanner(message) {
    const existing = document.getElementById('success-banner');
    if (existing) existing.remove();

    const banner = document.createElement('div');
    banner.id = 'success-banner';
    banner.textContent = message;
    Object.assign(banner.style, {
        position: 'fixed',
        top: '20px',
        left: '50%',
        transform: 'translateX(-50%)',
        background: '#27ae60',
        color: '#fff',
        padding: '14px 28px',
        borderRadius: '8px',
        fontSize: '15px',
        fontWeight: '600',
        boxShadow: '0 4px 20px rgba(0,0,0,0.18)',
        zIndex: '9999',
        cursor: 'pointer',
        transition: 'opacity 0.4s ease',
        whiteSpace: 'nowrap',
        maxWidth: '90vw',
        textAlign: 'center',
    });

    document.body.appendChild(banner);

    const fadeOut = () => {
        banner.style.opacity = '0';
        setTimeout(() => banner.remove(), 400);
    };
    banner.addEventListener('click', fadeOut);
    setTimeout(fadeOut, 4000);
}

function showErrorBanner(message) {
    const existing = document.getElementById('error-banner');
    if (existing) existing.remove();

    const banner = document.createElement('div');
    banner.id = 'error-banner';
    banner.textContent = message;
    Object.assign(banner.style, {
        position: 'fixed',
        top: '20px',
        left: '50%',
        transform: 'translateX(-50%)',
        background: '#e74c3c',
        color: '#fff',
        padding: '14px 28px',
        borderRadius: '8px',
        fontSize: '15px',
        fontWeight: '600',
        boxShadow: '0 4px 20px rgba(0,0,0,0.18)',
        zIndex: '9999',
        cursor: 'pointer',
        transition: 'opacity 0.4s ease',
        whiteSpace: 'nowrap',
        maxWidth: '90vw',
        textAlign: 'center',
    });

    document.body.appendChild(banner);

    const fadeOut = () => {
        banner.style.opacity = '0';
        setTimeout(() => banner.remove(), 400);
    };
    banner.addEventListener('click', fadeOut);
    setTimeout(fadeOut, 4000);
}
