const SUGGESTIONS = [
    "Cuisine",
    "Protection Bas De L'évier",
    "Accessoire Apoon",
    "Tiroir à Épices",
    "Système De Gaz",
    "Séparation",
    "Tiroir"
];

document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('date').value = new Date().toISOString().split('T')[0];
    calculateAll();
    document.getElementById('remise-amount').disabled = true;
});

document.getElementById('items-body').addEventListener('input', (e) => {
    if (e.target.classList.contains('item-qty') || e.target.classList.contains('item-price')) {
        calculateRow(e.target.closest('tr'));
        calculateTotal();
    }
    if (e.target.classList.contains('item-desc')) {
        ghostComplete(e.target);
    }
});

document.getElementById('items-body').addEventListener('keydown', (e) => {
    if (e.target.classList.contains('item-desc') && e.key === 'Tab') {
        const selStart = e.target.selectionStart;
        const selEnd = e.target.selectionEnd;
        if (selEnd > selStart) {
            e.target.setSelectionRange(selEnd, selEnd);
        }
    }
});

document.getElementById('remise-toggle').addEventListener('change', () => {
    const enabled = document.getElementById('remise-toggle').checked;
    document.getElementById('remise-amount').disabled = !enabled;
    if (!enabled) document.getElementById('remise-amount').value = 0;
    calculateNetTotal();
});

document.getElementById('remise-amount').addEventListener('input', calculateNetTotal);

document.getElementById('btn-add-item').addEventListener('click', () => {
    const tbody = document.getElementById('items-body');
    const tr = document.createElement('tr');
    tr.innerHTML = `
        <td><input type="text" class="item-desc" placeholder="Description" required></td>
        <td><input type="number" class="item-qty" value="1" min="0" step="any" required></td>
        <td><input type="number" class="item-price" value="0" min="0" step="any" required></td>
        <td class="item-total">0.00</td>
        <td><button type="button" class="btn-remove" title="Supprimer">&times;</button></td>
    `;
    tbody.appendChild(tr);
    tr.querySelector('.item-desc').focus();
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
    const net = Math.max(0, base - remise);
    document.getElementById('net-total').querySelector('small').parentElement.firstChild.textContent = formatNumber(net);
}

function calculateAll() {
    document.querySelectorAll('#items-body tr').forEach(tr => {
        calculateRow(tr);
    });
    calculateTotal();
    calculateNetTotal();
}

function ghostComplete(input) {
    const val = input.value;
    const prevLen = parseInt(input.dataset.prevlen || 0);
    if (val.length < prevLen) {
        input.dataset.prevlen = val.length;
        return;
    }
    const cursor = input.selectionStart;
    const typed = val.substring(0, cursor).toLowerCase();
    const match = SUGGESTIONS.find(s => s.toLowerCase().startsWith(typed));
    if (match && val.toLowerCase() !== match.toLowerCase()) {
        input.value = match;
        input.setSelectionRange(cursor, match.length);
        input.dataset.prevlen = match.length;
    } else {
        input.dataset.prevlen = val.length;
    }
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
    const netTotal = Math.max(0, baseTotal - remiseAmount);

    return {
        invoice_num: document.getElementById('invoice_num').value.trim() || '001',
        show_facture_num: document.getElementById('show-facture-num').checked,
        date: document.getElementById('date').value,
        client_name: document.getElementById('client_name').value.trim() || 'Client',
        client_address: document.getElementById('client_address').value.trim(),
        items: items,
        total: baseTotal,
        remise_enabled: remiseEnabled,
        remise: remiseAmount,
        net_total: netTotal
    };
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

    try {
        const res = await fetch('/generate_pdf', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = getFilenameFromHeaders(res) || `facture_${data.invoice_num}.pdf`;
        a.click();
        URL.revokeObjectURL(url);
    } catch (e) {
        alert('Erreur lors de la génération du PDF.');
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
