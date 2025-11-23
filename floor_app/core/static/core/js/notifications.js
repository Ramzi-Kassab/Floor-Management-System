/**
 * Floor Management System - Notification System
 * Real-time notifications with dropdown and management
 */

const NotificationSystem = {
    config: {
        pollInterval: 15000, // Check for new notifications every 15 seconds
        maxDisplayed: 10,
        soundEnabled: true
    },

    unreadCount: 0,
    pollTimer: null,
    lastNotificationId: 0,

    /**
     * Initialize notification system
     */
    init() {
        console.log('Initializing Notification System...');

        this.createDropdown();
        this.loadNotifications();
        this.startPolling();
        this.initializeEventHandlers();
        this.requestPermission();
    },

    /**
     * Create notification dropdown in navbar
     */
    createDropdown() {
        const navbar = document.querySelector('.navbar-nav');
        if (!navbar) return;

        const dropdownHtml = `
            <li class="nav-item dropdown" id="notificationDropdown">
                <a class="nav-link dropdown-toggle position-relative" href="#" role="button"
                   data-bs-toggle="dropdown" aria-expanded="false">
                    <i class="bi bi-bell fs-5"></i>
                    <span class="position-absolute top-0 start-100 translate-middle badge rounded-pill bg-danger"
                          id="notificationBadge" style="display: none;">
                        0
                    </span>
                </a>
                <div class="dropdown-menu dropdown-menu-end notification-dropdown p-0"
                     style="min-width: 350px; max-width: 400px;">
                    <div class="dropdown-header d-flex justify-content-between align-items-center">
                        <span class="fw-bold">Notifications</span>
                        <button class="btn btn-sm btn-link text-decoration-none" id="markAllRead">
                            Mark all read
                        </button>
                    </div>
                    <div class="notification-list" id="notificationList" style="max-height: 400px; overflow-y: auto;">
                        <div class="text-center py-5 text-muted">
                            <i class="bi bi-bell-slash fs-1 d-block mb-2"></i>
                            No notifications
                        </div>
                    </div>
                    <div class="dropdown-footer text-center">
                        <a href="/system/notifications/" class="btn btn-sm btn-link">View all notifications</a>
                    </div>
                </div>
            </li>
        `;

        navbar.insertAdjacentHTML('beforeend', dropdownHtml);
    },

    /**
     * Load notifications from API
     */
    loadNotifications() {
        FloorMS.ajax.get('/api/core/notifications/', { limit: this.config.maxDisplayed })
            .then(data => {
                this.renderNotifications(data.results || []);
                this.updateBadge(data.unread_count || 0);

                if (data.results && data.results.length > 0) {
                    this.lastNotificationId = data.results[0].id;
                }
            })
            .catch(error => console.error('Error loading notifications:', error));
    },

    /**
     * Render notifications in dropdown
     */
    renderNotifications(notifications) {
        const list = document.getElementById('notificationList');
        if (!list) return;

        if (notifications.length === 0) {
            list.innerHTML = `
                <div class="text-center py-5 text-muted">
                    <i class="bi bi-bell-slash fs-1 d-block mb-2"></i>
                    No notifications
                </div>
            `;
            return;
        }

        list.innerHTML = notifications.map(notif => this.createNotificationItem(notif)).join('');

        // Add click handlers
        list.querySelectorAll('[data-notification-id]').forEach(item => {
            item.addEventListener('click', (e) => {
                const id = e.currentTarget.dataset.notificationId;
                this.markAsRead(id);
            });
        });
    },

    /**
     * Create notification item HTML
     */
    createNotificationItem(notification) {
        const typeIcons = {
            'INFO': 'bi-info-circle text-info',
            'SUCCESS': 'bi-check-circle text-success',
            'WARNING': 'bi-exclamation-triangle text-warning',
            'ERROR': 'bi-x-circle text-danger',
            'SYSTEM': 'bi-gear text-secondary'
        };

        const icon = typeIcons[notification.notification_type] || 'bi-info-circle text-info';
        const timeAgo = this.getTimeAgo(notification.created_at);
        const unreadClass = notification.is_read ? '' : 'bg-light';

        return `
            <div class="dropdown-item notification-item ${unreadClass}"
                 data-notification-id="${notification.id}"
                 style="cursor: pointer; border-bottom: 1px solid #dee2e6;">
                <div class="d-flex align-items-start">
                    <div class="me-3">
                        <i class="bi ${icon} fs-4"></i>
                    </div>
                    <div class="flex-grow-1">
                        <div class="fw-bold small">${this.escapeHtml(notification.title)}</div>
                        <div class="small text-muted">${this.escapeHtml(notification.message)}</div>
                        <div class="small text-muted mt-1">
                            <i class="bi bi-clock"></i> ${timeAgo}
                        </div>
                    </div>
                    ${!notification.is_read ? '<div class="ms-2"><span class="badge bg-primary">New</span></div>' : ''}
                </div>
            </div>
        `;
    },

    /**
     * Update notification badge
     */
    updateBadge(count) {
        this.unreadCount = count;
        const badge = document.getElementById('notificationBadge');

        if (badge) {
            if (count > 0) {
                badge.textContent = count > 99 ? '99+' : count;
                badge.style.display = 'inline-block';
            } else {
                badge.style.display = 'none';
            }
        }
    },

    /**
     * Mark notification as read
     */
    markAsRead(notificationId) {
        FloorMS.ajax.post(`/api/core/notifications/${notificationId}/mark_read/`)
            .then(() => {
                this.loadNotifications();
            })
            .catch(error => console.error('Error marking notification as read:', error));
    },

    /**
     * Mark all notifications as read
     */
    markAllAsRead() {
        FloorMS.ajax.post('/api/core/notifications/mark_all_read/')
            .then(() => {
                FloorMS.notify.success('All notifications marked as read');
                this.loadNotifications();
            })
            .catch(error => console.error('Error marking all as read:', error));
    },

    /**
     * Start polling for new notifications
     */
    startPolling() {
        this.pollTimer = setInterval(() => {
            this.checkForNew();
        }, this.config.pollInterval);
    },

    /**
     * Stop polling
     */
    stopPolling() {
        if (this.pollTimer) {
            clearInterval(this.pollTimer);
            this.pollTimer = null;
        }
    },

    /**
     * Check for new notifications
     */
    checkForNew() {
        FloorMS.ajax.get('/api/core/notifications/', {
            limit: 1,
            after: this.lastNotificationId
        })
        .then(data => {
            if (data.results && data.results.length > 0) {
                // New notification received
                const newNotif = data.results[0];
                this.showDesktopNotification(newNotif);
                this.playSound();
                this.loadNotifications(); // Reload all
            }
        })
        .catch(error => console.error('Error checking for new notifications:', error));
    },

    /**
     * Show desktop notification
     */
    showDesktopNotification(notification) {
        if ('Notification' in window && Notification.permission === 'granted') {
            const desktopNotif = new Notification(notification.title, {
                body: notification.message,
                icon: '/static/img/logo.png',
                tag: 'floor-ms-' + notification.id
            });

            desktopNotif.onclick = () => {
                window.focus();
                this.markAsRead(notification.id);
                if (notification.link) {
                    window.location.href = notification.link;
                }
            };
        }
    },

    /**
     * Play notification sound
     */
    playSound() {
        if (this.config.soundEnabled) {
            const audio = new Audio('/static/sounds/notification.mp3');
            audio.volume = 0.5;
            audio.play().catch(() => {
                // Ignore errors (sound might not be available)
            });
        }
    },

    /**
     * Request desktop notification permission
     */
    requestPermission() {
        if ('Notification' in window && Notification.permission === 'default') {
            Notification.requestPermission();
        }
    },

    /**
     * Initialize event handlers
     */
    initializeEventHandlers() {
        // Mark all as read button
        const markAllBtn = document.getElementById('markAllRead');
        if (markAllBtn) {
            markAllBtn.addEventListener('click', () => this.markAllAsRead());
        }

        // Sound toggle
        const soundToggle = document.getElementById('notificationSoundToggle');
        if (soundToggle) {
            soundToggle.addEventListener('change', (e) => {
                this.config.soundEnabled = e.target.checked;
                localStorage.setItem('notificationSound', e.target.checked);
            });

            // Load saved preference
            const savedPref = localStorage.getItem('notificationSound');
            if (savedPref !== null) {
                this.config.soundEnabled = savedPref === 'true';
                soundToggle.checked = this.config.soundEnabled;
            }
        }
    },

    /**
     * Get time ago string
     */
    getTimeAgo(dateString) {
        const date = new Date(dateString);
        const now = new Date();
        const seconds = Math.floor((now - date) / 1000);

        if (seconds < 60) return 'Just now';
        if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
        if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
        if (seconds < 604800) return `${Math.floor(seconds / 86400)}d ago`;
        return date.toLocaleDateString();
    },

    /**
     * Escape HTML to prevent XSS
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
};

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
    NotificationSystem.init();
});

// Clean up on page unload
window.addEventListener('beforeunload', () => {
    NotificationSystem.stopPolling();
});
