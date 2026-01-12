/**
 * UI Controller
 * Handles interactions for Sidebar, Navbar, and Global UI elements
 */

document.addEventListener('DOMContentLoaded', () => {
    // Elements
    const sidebar = document.getElementById('sidebar');
    const sidebarToggle = document.getElementById('sidebarToggle');
    const mobileSidebarToggle = document.getElementById('sidebarToggleMobile');
    const sidebarOverlay = document.getElementById('sidebarOverlay');
    const themeToggle = document.getElementById('themeToggle');
    const themeIcon = document.getElementById('themeIcon');
    const globalSearch = document.getElementById('globalSearch');
    const searchResults = document.getElementById('searchResults');

    // 1. Sidebar Logic
    const toggleSidebar = (force) => {
        const isCollapsed = force !== undefined ? force : !sidebar.classList.contains('collapsed');
        sidebar.classList.toggle('collapsed', isCollapsed);
        localStorage.setItem('sidebarCollapsed', isCollapsed);
    };

    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', () => toggleSidebar());
    }

    if (localStorage.getItem('sidebarCollapsed') === 'true') {
        sidebar?.classList.add('collapsed');
    }

    const closeSidebarMobile = () => {
        sidebar?.classList.remove('mobile-open');
        sidebarOverlay?.classList.remove('active');
        document.body.style.overflow = '';
    };

    // 2. Mobile Sidebar Logic
    if (mobileSidebarToggle) {
        mobileSidebarToggle.addEventListener('click', () => {
            sidebar?.classList.add('mobile-open');
            sidebarOverlay?.classList.add('active');
            document.body.style.overflow = 'hidden';
        });
    }

    const sidebarCloseMobile = document.getElementById('sidebarCloseMobile');
    if (sidebarCloseMobile) {
        sidebarCloseMobile.addEventListener('click', closeSidebarMobile);
    }

    if (sidebarOverlay) {
        sidebarOverlay.addEventListener('click', closeSidebarMobile);
    }

    // 3. Theme Logic
    const setTheme = (theme) => {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('theme', theme);
        if (themeIcon) {
            themeIcon.className = theme === 'dark' ? 'bi bi-sun fs-5' : 'bi bi-moon fs-5';
        }
    };

    if (themeToggle) {
        themeToggle.addEventListener('click', () => {
            const currentTheme = document.documentElement.getAttribute('data-theme');
            setTheme(currentTheme === 'dark' ? 'light' : 'dark');
        });
        setTheme(localStorage.getItem('theme') || 'light');
    }

    // 4. Search Logic
    let searchTimeout;
    if (globalSearch && searchResults) {
        globalSearch.addEventListener('input', (e) => {
            const q = e.target.value.trim();
            clearTimeout(searchTimeout);

            if (q.length < 2) {
                searchResults.classList.add('d-none');
                return;
            }

            searchTimeout = setTimeout(async () => {
                try {
                    const resp = await axios.get(`${API_URL}/dashboard/search`, { params: { q } });
                    const results = resp.data;

                    if (results.length === 0) {
                        searchResults.innerHTML = '<div class="px-3 py-2 smaller text-muted">No results found</div>';
                    } else {
                        searchResults.innerHTML = results.map(r => `
                            <li><a class="dropdown-item py-2 d-flex justify-content-between align-items-center" href="${r.url}">
                                <span>${r.name}</span>
                                <span class="badge bg-light text-muted fw-normal" style="font-size: 0.65rem;">${r.type}</span>
                            </a></li>
                        `).join('');
                    }
                    searchResults.classList.remove('d-none');
                } catch (e) {
                    console.error("Search failed", e);
                }
            }, 300);
        });

        globalSearch.addEventListener('blur', () => {
            setTimeout(() => searchResults.classList.add('d-none'), 200);
        });
    }

    // 5. Notifications Logic
    async function updateNotifications() {
        const list = document.querySelector('.notifications-list');
        const count = document.getElementById('notificationCount');
        if (!list || !count) return;

        try {
            const resp = await axios.get(`${API_URL}/dashboard/notifications`);
            const notes = resp.data;

            count.textContent = notes.length;
            count.style.display = notes.length > 0 ? 'block' : 'none';

            if (notes.length === 0) {
                list.innerHTML = '<div class="p-3 text-center text-muted smaller">No new notifications</div>';
                return;
            }

            list.innerHTML = notes.map(n => `
                <div class="p-3 border-bottom last-child-no-border">
                    <div class="d-flex justify-content-between align-items-start mb-1">
                        <span class="fw-bold small text-${n.type}">${n.title}</span>
                        <span class="text-muted" style="font-size: 0.7rem;">${n.time}</span>
                    </div>
                    <p class="mb-0 text-muted small">${n.message}</p>
                </div>
            `).join('');
        } catch (e) {
            console.error("Notifications fetch failed", e);
        }
    }

    // Initialize Active Nav & Notifications
    const highlightActiveNav = () => {
        const currentPath = window.location.pathname;
        document.querySelectorAll('.nav-link, .dropdown-item').forEach(link => {
            if (link.getAttribute('href') === currentPath) link.classList.add('active');
            else link.classList.remove('active');
        });
    };

    highlightActiveNav();
    updateNotifications();
    setInterval(updateNotifications, 60000); // Pulse every minute

    // 6. Global Utilities
    window.ui = {
        showToast: (message, type = 'info') => {
            let msg = message;
            if (typeof message === 'object' && message !== null) {
                if (Array.isArray(message)) {
                    msg = message.map(err => {
                        if (typeof err === 'string') return err;
                        const loc = err.loc ? err.loc.join('.') : '';
                        return `${loc ? loc + ': ' : ''}${err.msg || JSON.stringify(err)}`;
                    }).join('<br>');
                } else {
                    msg = message.detail || JSON.stringify(message);
                }
            }

            const toast = document.createElement('div');
            toast.className = `toast align-items-center text-white bg-${type} border-0`;
            toast.innerHTML = `
                <div class="d-flex">
                    <div class="toast-body">${msg}</div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
                </div>
            `;
            let container = document.getElementById('toastContainer');
            if (!container) {
                container = document.createElement('div');
                container.id = 'toastContainer';
                container.className = 'toast-container position-fixed top-0 end-0 p-3';
                container.style.zIndex = '9999';
                document.body.appendChild(container);
            }
            container.appendChild(toast);
            new bootstrap.Toast(toast).show();
            toast.addEventListener('hidden.bs.toast', () => toast.remove());
        },
        confirmDelete: (options) => {
            const { title, message, onConfirm, confirmText = 'Delete', confirmButtonClass = 'btn-danger' } = options;
            const modalId = 'globalConfirmDeleteModal';
            let modalEl = document.getElementById(modalId);
            if (!modalEl) {
                modalEl = document.createElement('div');
                modalEl.id = modalId;
                modalEl.className = 'modal fade';
                modalEl.innerHTML = `
                    <div class="modal-dialog modal-dialog-centered">
                        <div class="modal-content border-0 shadow-lg">
                            <div class="modal-header border-0 pt-4 px-4">
                                <h5 class="modal-title fw-bold"></h5>
                                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                            </div>
                            <div class="modal-body px-4 py-0">
                                <p class="text-muted mb-0"></p>
                            </div>
                            <div class="modal-footer border-0 pb-4 px-4 pt-3">
                                <button type="button" class="btn btn-light px-4" data-bs-dismiss="modal">Cancel</button>
                                <button type="button" class="btn ${confirmButtonClass} px-4 confirm-btn">${confirmText}</button>
                            </div>
                        </div>
                    </div>
                `;
                document.body.appendChild(modalEl);
            }

            modalEl.querySelector('.modal-title').textContent = title || 'Confirm Action';
            modalEl.querySelector('.modal-body p').textContent = message || 'Are you sure you want to proceed?';
            const confirmBtn = modalEl.querySelector('.confirm-btn');
            confirmBtn.className = `btn ${confirmButtonClass} px-4 confirm-btn`;
            confirmBtn.textContent = confirmText;

            const modal = bootstrap.Modal.getOrCreateInstance(modalEl);

            const newConfirmBtn = confirmBtn.cloneNode(true);
            confirmBtn.parentNode.replaceChild(newConfirmBtn, confirmBtn);

            newConfirmBtn.addEventListener('click', async () => {
                newConfirmBtn.disabled = true;
                newConfirmBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Processing...';
                try {
                    await onConfirm();
                    modal.hide();
                } catch (e) {
                    console.error(e);
                    window.ui.showToast(e.response?.data?.detail || 'Operation failed', 'danger');
                    newConfirmBtn.disabled = false;
                    newConfirmBtn.innerHTML = confirmText;
                }
            });

            modal.show();
        }
    };

    // 7. Initialize Tooltips
    const initTooltips = () => {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl, {
                trigger: 'hover',
                boundary: 'viewport'
            });
        });
    };

    initTooltips();
});
