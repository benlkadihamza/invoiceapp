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
    const mobileBottomToggle = document.getElementById('mobileBottomMenuToggle');
    const sidebarCloseBtn = document.getElementById('sidebarCloseBtn');
    const sidebar = document.getElementById('sidebar');
    let overlay = document.createElement('div');
    overlay.className = 'sidebar-overlay';
    document.body.appendChild(overlay);

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

        sidebar.addEventListener('scroll', function() {
            sessionStorage.setItem('sidebarScrollPos', sidebar.scrollTop);
        }, { passive: true });
    }

    // Auto-close sidebar on mobile when navigating via sidebar link & save scroll position
    document.querySelectorAll('#sidebar .nav-link, #sidebar a').forEach(function(link) {
        link.addEventListener('click', function() {
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
    sidebar?.addEventListener('touchstart', function(e) {
        touchStartX = e.changedTouches[0].screenX;
    }, { passive: true });

    sidebar?.addEventListener('touchend', function(e) {
        const touchEndX = e.changedTouches[0].screenX;
        if (touchStartX - touchEndX > 50) { // Swiped left
            closeSidebar();
        }
    }, { passive: true });

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

function confirmDelete(target, message) {
    const modalEl = document.getElementById('deleteModal');
    if (!modalEl) return;
    
    const modal = bootstrap.Modal.getInstance(modalEl) || new bootstrap.Modal(modalEl);
    const form = document.getElementById('deleteForm');
    const msgEl = document.getElementById('deleteModalMessage');
    
    if (msgEl) {
        msgEl.textContent = message || "Êtes-vous sûr de vouloir supprimer cet élément ? Cette action est irréversible.";
    }
    
    form.onsubmit = null;
    
    if (typeof target === 'function') {
        form.action = '#';
        form.onsubmit = function(e) {
            e.preventDefault();
            modal.hide();
            target();
        };
    } else {
        form.action = target;
    }
    
    modal.show();
}

function formatCurrency(amount) {
    return new Intl.NumberFormat('fr-MA', { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(amount) + ' DH';
}
