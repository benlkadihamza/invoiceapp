document.addEventListener('DOMContentLoaded', function() {

    const savedTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-bs-theme', savedTheme);
    updateThemeIcon(savedTheme);

    document.getElementById('themeToggle')?.addEventListener('click', toggleTheme);
    document.getElementById('mobileThemeToggle')?.addEventListener('click', toggleTheme);

    function toggleTheme() {
        const current = document.documentElement.getAttribute('data-bs-theme');
        const next = current === 'dark' ? 'light' : 'dark';
        document.documentElement.setAttribute('data-bs-theme', next);
        localStorage.setItem('theme', next);
        updateThemeIcon(next);
    }

    function updateThemeIcon(theme) {
        const icon = theme === 'dark' ? 'bi-sun' : 'bi-moon-stars';
        document.querySelectorAll('#themeToggle i, #mobileThemeToggle i').forEach(function(el) {
            el.className = 'bi ' + icon;
        });
    }

    const mobileToggle = document.getElementById('mobileMenuToggle');
    const sidebar = document.getElementById('sidebar');
    let overlay = document.createElement('div');
    overlay.className = 'sidebar-overlay';
    document.body.appendChild(overlay);

    mobileToggle?.addEventListener('click', function() {
        sidebar.classList.toggle('show');
        overlay.classList.toggle('show');
    });

    overlay.addEventListener('click', function() {
        sidebar.classList.remove('show');
        overlay.classList.remove('show');
    });

    document.querySelectorAll('[data-bs-dismiss="alert"]').forEach(function(btn) {
        btn.addEventListener('click', function() {
            setTimeout(function() {
                const alerts = document.querySelectorAll('.alert');
                alerts.forEach(function(a) { if (!a.closest('.show')) a.remove(); });
            }, 300);
        });
    });

    setTimeout(function() {
        document.querySelectorAll('.alert').forEach(function(el) {
            el.classList.remove('show');
            setTimeout(function() { el.remove(); }, 300);
        });
    }, 5000);

    document.querySelectorAll('.btn-outline-danger[onclick]').forEach(function(btn) {
        btn.addEventListener('click', function(e) {
            if (!this.closest('form') && this.getAttribute('onclick')?.includes('confirmDelete')) {
                e.preventDefault();
            }
        });
    });

    const tooltips = document.querySelectorAll('[title]');
    tooltips.forEach(function(el) {
        if (!el.closest('.dataTable') && !el.closest('table')) {
            new bootstrap.Tooltip(el, { trigger: 'hover', delay: { show: 500, hide: 100 } });
        }
    });
});

function confirmDelete(url) {
    const modal = new bootstrap.Modal(document.getElementById('deleteModal'));
    document.getElementById('deleteForm').action = url;
    modal.show();
}

function formatCurrency(amount) {
    return new Intl.NumberFormat('fr-MA', { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(amount) + ' DH';
}
