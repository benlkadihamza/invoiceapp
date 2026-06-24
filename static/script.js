document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('date').value = new Date().toISOString().split('T')[0];
    calculateAll();
});

document.getElementById('items-body').addEventListener('input', (e) => {
    if (e.target.classList.contains('item-qty') || e.target.classList.contains('item-price')) {
        calculateRow(e.target.closest('tr'));
        calculateTotal();
    }
});

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

function calculateRow(tr) {
    const qty = parseFloat(tr.querySelector('.item-qty').value) || 0;
    const price = parseFloat(tr.querySelector('.item-price').value) || 0;
    tr.querySelector('.item-total').textContent = (qty * price).toFixed(2);
}

function calculateTotal() {
    let total = 0;
    document.querySelectorAll('.item-total').forEach(el => {
        total += parseFloat(el.textContent) || 0;
    });
    document.getElementById('grand-total').querySelector('small').parentElement.firstChild.textContent = total.toFixed(2);
}

function calculateAll() {
    document.querySelectorAll('#items-body tr').forEach(tr => {
        calculateRow(tr);
    });
    calculateTotal();
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

    return {
        invoice_num: document.getElementById('invoice_num').value.trim() || '001',
        date: document.getElementById('date').value,
        client_name: document.getElementById('client_name').value.trim() || 'Client',
        client_address: document.getElementById('client_address').value.trim(),
        items: items,
        total: items.reduce((s, i) => s + i.total, 0)
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
