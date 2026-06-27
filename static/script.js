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

// Tracks the DB id of the invoice currently loaded in the form.
// null = creating a new invoice; number = editing an existing invoice.
let currentInvoiceId = null;

document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('date').value = new Date().toISOString().split('T')[0];
    calculateAll();
    document.getElementById('remise-amount').disabled = true;
    document.getElementById('payer-amount').disabled = true;

    // If the page was opened with ?edit=<id>, load that invoice into the form.
    const params = new URLSearchParams(window.location.search);
    const editId = params.get('edit');
    if (editId) {
        loadInvoiceForEdit(parseInt(editId, 10));
    }
});

document.getElementById('items-body').addEventListener('input', (e) => {
    if (e.target.classList.contains('item-qty') || e.target.classList.contains('item-price')) {
        calculateRow(e.target.closest('tr'));
        calculateTotal();
    }
    if (e.target.classList.contains('item-desc')) {
        filterSuggestions(e.target);
    }
});

document.getElementById('items-body').addEventListener('mousedown', (e) => {
    if (e.target.classList.contains('item-desc')) {
        focusedDesc = e.target;
    }
});

document.getElementById('items-body').addEventListener('focusin', (e) => {
    if (e.target.classList.contains('item-desc')) {
        focusedDesc = e.target;
        filterSuggestions(e.target);
    }
});

document.getElementById('items-body').addEventListener('keydown', (e) => {
    if (e.target.classList.contains('item-desc') && e.key === 'Escape') {
        const list = e.target.closest('.desc-wrapper')?.querySelector('.suggestion-list');
        if (list) list.classList.remove('active');
    }
});

document.addEventListener('click', (e) => {
    if (e.target === focusedDesc) {
        focusedDesc = null;
        return;
    }
    focusedDesc = null;
    if (!e.target.closest('.desc-wrapper')) {
        document.querySelectorAll('.suggestion-list.active').forEach(el => el.classList.remove('active'));
    }
});

document.getElementById('remise-toggle').addEventListener('change', () => {
    const enabled = document.getElementById('remise-toggle').checked;
    document.getElementById('remise-amount').disabled = !enabled;
    if (!enabled) document.getElementById('remise-amount').value = 0;
    calculateNetTotal();
});

document.getElementById('remise-amount').addEventListener('input', calculateNetTotal);

document.getElementById('payer-toggle').addEventListener('change', () => {
    const enabled = document.getElementById('payer-toggle').checked;
    document.getElementById('payer-amount').disabled = !enabled;
    if (!enabled) document.getElementById('payer-amount').value = 0;
    calculateNetTotal();
});

document.getElementById('payer-amount').addEventListener('input', calculateNetTotal);

document.getElementById('btn-add-item').addEventListener('click', () => {
    const tbody = document.getElementById('items-body');
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
    // Focus the input and trigger suggestions
    descInput.focus();
    // Manually trigger the suggestion filter after a tiny delay to ensure DOM is ready
    setTimeout(() => {
        filterSuggestions(descInput);
    }, 50);
    
    tr.querySelectorAll('.item-qty, .item-price').forEach(el => {
        el.addEventListener('input', () => {
            calculateRow(tr);
            calculateTotal();
        });
    });
    tr.querySelector('.btn-remove').addEventListener('click', () => {
        tr.remove();
        calculateTotal();
    });
});

document.getElementById('items-body').addEventListener('click', (e) => {
    if (e.target.classList.contains('btn-remove')) {
        const rows = document.querySelectorAll('#items-body tr');
        if (rows.length > 1) {
            e.target.closest('tr').remove();
            calculateTotal();
        }
    }
});

function formatNumber(n) {
    return Number(n).toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ' ');
}

function calculateRow(tr) {
    const qty = parseFloat(tr.querySelector('.item-qty').value) || 0;
    const price = parseFloat(tr.querySelector('.item-price').value) || 0;
    tr.querySelector('.item-total').textContent = formatNumber(qty * price);
}

function calculateTotal() {
    let total = 0;
    document.querySelectorAll('.item-total').forEach(el => {
        total += parseFloat(el.textContent.replace(/\s/g, '')) || 0;
    });
    document.getElementById('grand-total').querySelector('small').parentElement.firstChild.textContent = formatNumber(total);
    calculateNetTotal();
}

function calculateNetTotal() {
    const base = parseFloat(document.getElementById('grand-total').textContent.replace(/\s/g, '')) || 0;
    const remise = document.getElementById('remise-toggle').checked
        ? (parseFloat(document.getElementById('remise-amount').value) || 0)
        : 0;
    const payer = document.getElementById('payer-toggle').checked
        ? (parseFloat(document.getElementById('payer-amount').value) || 0)
        : 0;
    const net = Math.max(0, base - remise - payer);
    document.getElementById('net-total').querySelector('small').parentElement.firstChild.textContent = formatNumber(net);
}

function calculateAll() {
    document.querySelectorAll('#items-body tr').forEach(tr => {
        calculateRow(tr);
    });
    calculateTotal();
    calculateNetTotal();
}

function filterSuggestions(input) {
    const wrapper = input.closest('.desc-wrapper');
    if (!wrapper) return;
    const list = wrapper.querySelector('.suggestion-list');
    const val = input.value.trim().toLowerCase();

    list.innerHTML = '';

    const filtered = SUGGESTIONS.filter(s =>
        s.toLowerCase().includes(val)
    );

    // Show all suggestions when input is empty or no matches found
    if (filtered.length === 0 && val === '') {
        SUGGESTIONS.forEach(s => addSuggestionItem(list, s, input));
    } else if (filtered.length > 0) {
        filtered.forEach(s => addSuggestionItem(list, s, input));
    } else {
        // If no matches, show all suggestions
        SUGGESTIONS.forEach(s => addSuggestionItem(list, s, input));
    }

    // Only add "Autre" option if there's text in the input
    if (val) {
        const otherItem = document.createElement('div');
        otherItem.className = 'suggestion-item suggestion-other';
        otherItem.textContent = val ? `Autre: "${input.value}"` : 'Autre...';
        otherItem.addEventListener('click', () => {
            list.classList.remove('active');
            input.focus();
        });
        list.appendChild(otherItem);
    }

    list.classList.add('active');
}

function addSuggestionItem(list, text, input) {
    const item = document.createElement('div');
    item.className = 'suggestion-item';
    item.textContent = text;
    item.addEventListener('click', () => {
        input.value = text;
        list.classList.remove('active');
        input.focus();
    });
    list.appendChild(item);
}

function getFormData() {
    const items = [];
    document.querySelectorAll('#items-body tr').forEach(tr => {
        const desc = tr.querySelector('.item-desc').value.trim();
        const qty = parseFloat(tr.querySelector('.item-qty').value) || 0;
        const price = parseFloat(tr.querySelector('.item-price').value) || 0;
        if (desc) {
            items.push({ description: desc, quantity: qty, unit_price: price, total: qty * price });
        }
    });

    const baseTotal = items.reduce((s, i) => s + i.total, 0);
    const remiseEnabled = document.getElementById('remise-toggle').checked;
    const remiseAmount = remiseEnabled ? (parseFloat(document.getElementById('remise-amount').value) || 0) : 0;
    const payerEnabled = document.getElementById('payer-toggle').checked;
    const payerAmount = payerEnabled ? (parseFloat(document.getElementById('payer-amount').value) || 0) : 0;
    const netTotal = Math.max(0, baseTotal - remiseAmount - payerAmount);

    const data = {
        invoice_num: document.getElementById('invoice_num').value.trim() || '001',
        show_facture_num: document.getElementById('show-facture-num').checked,
        date: document.getElementById('date').value,
        client_name: document.getElementById('client_name').value.trim() || 'Client',
        client_address: document.getElementById('client_address').value.trim(),
        items: items,
        total: baseTotal,
        remise_enabled: remiseEnabled,
        remise: remiseAmount,
        payer_enabled: payerEnabled,
        payer: payerAmount,
        net_total: netTotal
    };

    // Include the DB id when editing so the backend does UPDATE, not INSERT.
    if (currentInvoiceId !== null) {
        data.id = currentInvoiceId;
    }

    return data;
}

// ─────────────────────────────────────────────────────────────────────────────
// Edit Invoice
// Fetches all invoice data from the backend, populates every form field,
// and switches the form into "edit mode" (Save → UPDATE instead of INSERT).
// ─────────────────────────────────────────────────────────────────────────────
async function loadInvoiceForEdit(invoiceId) {
    try {
        const res = await fetch(`/invoices/${invoiceId}/json`);
        if (!res.ok) { alert('Facture introuvable.'); return; }
        const inv = await res.json();

        // Store the id so Save knows to UPDATE this row.
        currentInvoiceId = inv.id;

        // ── Header fields ──────────────────────────────────────────────────
        document.getElementById('invoice_num').value    = inv.invoice_num    || '';
        document.getElementById('date').value           = inv.date           || '';
        document.getElementById('client_name').value    = inv.client_name    || '';
        document.getElementById('client_address').value = inv.client_address || '';

        // ── Items ──────────────────────────────────────────────────────────
        const tbody   = document.getElementById('items-body');
        tbody.innerHTML = '';  // clear existing rows

        const itemsArr = Array.isArray(inv.items) && inv.items.length > 0
            ? inv.items
            : [{ description: '', quantity: 1, unit_price: 0, total: 0 }];

        itemsArr.forEach(item => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td><div class="desc-wrapper"><input type="text" class="item-desc" placeholder="Description" required><div class="suggestion-list"></div></div></td>
                <td><input type="number" class="item-qty"   value="1" min="0" step="any" required></td>
                <td><input type="number" class="item-price" value="0" min="0" step="any" required></td>
                <td class="item-total">0.00</td>
                <td><button type="button" class="btn-remove" title="Supprimer">&times;</button></td>
            `;
            tbody.appendChild(tr);
            tr.querySelector('.item-desc').value  = item.description || '';
            tr.querySelector('.item-qty').value   = item.quantity    ?? 1;
            tr.querySelector('.item-price').value = item.unit_price  ?? 0;
            tr.querySelector('.btn-remove').addEventListener('click', () => {
                if (document.querySelectorAll('#items-body tr').length > 1) {
                    tr.remove();
                    calculateTotal();
                }
            });
        });

        // ── Discount / payment ─────────────────────────────────────────────
        const remise = inv.remise || 0;
        const payer  = inv.payer  || 0;
        if (remise > 0) {
            document.getElementById('remise-toggle').checked  = true;
            document.getElementById('remise-amount').disabled = false;
            document.getElementById('remise-amount').value    = remise;
        }
        if (payer > 0) {
            document.getElementById('payer-toggle').checked  = true;
            document.getElementById('payer-amount').disabled = false;
            document.getElementById('payer-amount').value    = payer;
        }

        // ── Recalculate totals ─────────────────────────────────────────────
        calculateAll();

        // ── Visual indicator ───────────────────────────────────────────────
        const saveBtn = document.getElementById('btn-save');
        saveBtn.textContent = '💾 Mettre à jour';
        saveBtn.title = `Modification de la facture ID ${inv.id}`;

        window.scrollTo({ top: 0, behavior: 'smooth' });

    } catch (err) {
        console.error(err);
        alert('Erreur lors du chargement de la facture pour modification.');
    }
}

document.getElementById('btn-preview').addEventListener('click', async () => {
    const data = getFormData();
    if (!data.items.length) return alert('Ajoutez au moins un article.');

    try {
        const res = await fetch('/preview', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        const html = await res.text();
        const modal = document.getElementById('preview-modal');
        const body = document.getElementById('preview-body');
        body.innerHTML = html;
        modal.classList.add('active');
    } catch (e) {
        alert('Erreur lors de la génération de l\'aperçu.');
    }
});

document.querySelector('.modal-close').addEventListener('click', () => {
    document.getElementById('preview-modal').classList.remove('active');
});

document.getElementById('preview-modal').addEventListener('click', (e) => {
    if (e.target === e.currentTarget) {
        document.getElementById('preview-modal').classList.remove('active');
    }
});

function getFilenameFromHeaders(res) {
    const cd = res.headers.get('Content-Disposition');
    if (!cd) return null;
    const match = cd.match(/filename\*?=(?:UTF-8'')?["']?([^"';]+)["']?/);
    return match ? match[1] : null;
}

document.getElementById('btn-pdf').addEventListener('click', async () => {
    const data = getFormData();
    if (!data.items.length) return alert('Ajoutez au moins un article.');

    // Capture mode BEFORE the save so the reset decision is correct even
    // though resetFormToNewInvoice() will clear currentInvoiceId.
    const wasEditing = currentInvoiceId !== null;

    // ── Step 1: Save / update the invoice first ───────────────────────────────
    let savedId;
    try {
        const saveRes = await fetch('/save_invoice', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        const saveResult = await saveRes.json();
        if (!saveResult || !saveResult.id) {
            alert("Erreur lors de l'enregistrement de la facture. Le PDF n'a pas \u00e9t\u00e9 g\u00e9n\u00e9r\u00e9.");
            return;
        }
        savedId = saveResult.id;
    } catch (e) {
        alert("Erreur lors de l'enregistrement de la facture. Le PDF n'a pas \u00e9t\u00e9 g\u00e9n\u00e9r\u00e9.");
        return;
    }

    // ── Step 2: Generate and download the PDF ─────────────────────────────────
    try {
        const pdfRes = await fetch('/generate_pdf', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        const blob = await pdfRes.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = getFilenameFromHeaders(pdfRes) || `facture_${data.invoice_num}.pdf`;
        a.click();
        URL.revokeObjectURL(url);
    } catch (e) {
        alert('Erreur lors de la g\u00e9n\u00e9ration du PDF.');
        return;
    }

    // ── Step 3: Post-download state ───────────────────────────────────────────
    if (wasEditing) {
        // EDIT mode: stay on the invoice, just show a confirmation banner.
        showSuccessBanner(`Facture mise \u00e0 jour et PDF t\u00e9l\u00e9charg\u00e9. ID\u00a0: ${savedId}`);
    } else {
        // CREATE mode: new invoice saved \u2192 reset the form for the next one.
        resetFormToNewInvoice();
    }
});

document.getElementById('btn-excel').addEventListener('click', async () => {
    const data = getFormData();
    if (!data.items.length) return alert('Ajoutez au moins un article.');

    try {
        const res = await fetch('/generate_excel', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
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
});

// ─────────────────────────────────────────────────────────────────────────────
// resetFormToNewInvoice
// Called after a NEW invoice is successfully saved.
// Clears every field and returns the form to "create" mode so the user can
// immediately start entering a new invoice without a page reload.
// ─────────────────────────────────────────────────────────────────────────────
function resetFormToNewInvoice() {
    // ── 1. Exit edit mode ─────────────────────────────────────────────────────
    currentInvoiceId = null;

    // ── 2. Header fields ──────────────────────────────────────────────────────
    document.getElementById('invoice_num').value    = '001';
    document.getElementById('date').value           = new Date().toISOString().split('T')[0];
    document.getElementById('client_name').value    = '';
    document.getElementById('client_address').value = '';
    document.getElementById('show-facture-num').checked = false;

    // ── 3. Items – remove all rows, add one blank row ─────────────────────────
    const tbody = document.getElementById('items-body');
    tbody.innerHTML = `
        <tr>
            <td><div class="desc-wrapper"><input type="text" class="item-desc" placeholder="Description" required><div class="suggestion-list"></div></div></td>
            <td><input type="number" class="item-qty"   value="1" min="0" step="any" required></td>
            <td><input type="number" class="item-price" value="0" min="0" step="any" required></td>
            <td class="item-total">0.00</td>
            <td><button type="button" class="btn-remove" title="Supprimer">&times;</button></td>
        </tr>
    `;

    // ── 4. Discount / payment ─────────────────────────────────────────────────
    document.getElementById('remise-toggle').checked  = false;
    document.getElementById('remise-amount').value    = 0;
    document.getElementById('remise-amount').disabled = true;
    document.getElementById('payer-toggle').checked   = false;
    document.getElementById('payer-amount').value     = 0;
    document.getElementById('payer-amount').disabled  = true;

    // ── 5. Recalculate totals to zero ─────────────────────────────────────────
    calculateAll();

    // ── 6. Restore Save button to create-mode label ───────────────────────────
    const saveBtn = document.getElementById('btn-save');
    saveBtn.textContent = 'Enregistrer';
    saveBtn.title = '';

    // ── 7. Show a non-blocking success banner ─────────────────────────────────
    showSuccessBanner('Facture enregistrée avec succès. Vous pouvez créer une nouvelle facture.');

    // ── 8. Focus client name so the user can start typing immediately ─────────
    document.getElementById('client_name').focus();

    // ── 9. Scroll to top ──────────────────────────────────────────────────────
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// ─────────────────────────────────────────────────────────────────────────────
// showSuccessBanner
// Displays a transient green success notification at the top of the page.
// It auto-dismisses after 4 seconds or when the user clicks it.
// ─────────────────────────────────────────────────────────────────────────────
function showSuccessBanner(message) {
    // Remove any existing banner first.
    const existing = document.getElementById('success-banner');
    if (existing) existing.remove();

    const banner = document.createElement('div');
    banner.id = 'success-banner';
    banner.textContent = message;
    Object.assign(banner.style, {
        position:        'fixed',
        top:             '20px',
        left:            '50%',
        transform:       'translateX(-50%)',
        background:      '#27ae60',
        color:           '#fff',
        padding:         '14px 28px',
        borderRadius:    '8px',
        fontSize:        '15px',
        fontWeight:      '600',
        boxShadow:       '0 4px 20px rgba(0,0,0,0.18)',
        zIndex:          '9999',
        cursor:          'pointer',
        transition:      'opacity 0.4s ease',
        whiteSpace:      'nowrap',
        maxWidth:        '90vw',
        textAlign:       'center',
    });

    document.body.appendChild(banner);

    // Fade out and remove after 4 s.
    const fadeOut = () => {
        banner.style.opacity = '0';
        setTimeout(() => banner.remove(), 400);
    };
    banner.addEventListener('click', fadeOut);
    setTimeout(fadeOut, 4000);
}

document.getElementById('btn-save').addEventListener('click', async () => {
    const data = getFormData();
    if (!data.items.length) return alert('Ajoutez au moins un article.');

    // Remember whether we were in create or edit mode BEFORE the fetch,
    // because resetFormToNewInvoice() will clear currentInvoiceId.
    const wasEditing = currentInvoiceId !== null;

    try {
        const res = await fetch('/save_invoice', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        const result = await res.json();
        if (result && result.id) {
            if (wasEditing) {
                // ── EDIT mode: invoice updated, stay on the same invoice ──────
                alert(`Facture mise à jour avec succès. ID: ${result.id}`);
                // currentInvoiceId stays set; form keeps the edited data.
            } else {
                // ── CREATE mode: new invoice saved → reset to blank form ──────
                resetFormToNewInvoice();
            }
        } else {
            const msg = result && result.error ? result.error : "Erreur lors de l'enregistrement de la facture.";
            alert(msg);
        }
    } catch (e) {
        alert("Erreur lors de l'enregistrement de la facture.");
        console.error(e);
    }
});