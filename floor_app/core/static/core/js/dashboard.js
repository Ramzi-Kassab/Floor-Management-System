/**
 * Floor Management System - Dashboard JavaScript
 * Real-time monitoring dashboard with charts and metrics
 */

const Dashboard = {
    charts: {},
    refreshInterval: null,
    config: {
        refreshRate: 30000, // 30 seconds
        chartOptions: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    position: 'bottom'
                }
            }
        }
    },

    /**
     * Initialize dashboard
     */
    init() {
        console.log('Initializing Dashboard...');

        this.initializeCharts();
        this.loadInitialData();
        this.startAutoRefresh();
        this.initializeEventHandlers();
    },

    /**
     * Initialize all charts
     */
    initializeCharts() {
        // Activity Trend Chart
        if (document.getElementById('activityTrendChart')) {
            this.charts.activityTrend = this.createActivityTrendChart();
        }

        // System Events Chart
        if (document.getElementById('systemEventsChart')) {
            this.charts.systemEvents = this.createSystemEventsChart();
        }

        // User Activity Chart
        if (document.getElementById('userActivityChart')) {
            this.charts.userActivity = this.createUserActivityChart();
        }

        // Performance Gauge
        if (document.getElementById('performanceGauge')) {
            this.charts.performance = this.createPerformanceGauge();
        }
    },

    /**
     * Create Activity Trend Line Chart
     */
    createActivityTrendChart() {
        const ctx = document.getElementById('activityTrendChart').getContext('2d');

        return new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Activities',
                    data: [],
                    borderColor: FloorMS.config.chartColors.primary,
                    backgroundColor: FloorMS.config.chartColors.primary + '20',
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                ...this.config.chartOptions,
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            stepSize: 1
                        }
                    }
                }
            }
        });
    },

    /**
     * Create System Events Pie Chart
     */
    createSystemEventsChart() {
        const ctx = document.getElementById('systemEventsChart').getContext('2d');

        return new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Critical', 'Error', 'Warning', 'Info'],
                datasets: [{
                    data: [0, 0, 0, 0],
                    backgroundColor: [
                        '#dc3545', // Critical - Red
                        '#ffc107', // Error - Yellow
                        '#17a2b8', // Warning - Cyan
                        '#007bff'  // Info - Blue
                    ]
                }]
            },
            options: this.config.chartOptions
        });
    },

    /**
     * Create User Activity Bar Chart
     */
    createUserActivityChart() {
        const ctx = document.getElementById('userActivityChart').getContext('2d');

        return new Chart(ctx, {
            type: 'bar',
            data: {
                labels: [],
                datasets: [{
                    label: 'Actions',
                    data: [],
                    backgroundColor: FloorMS.config.chartColors.success,
                }]
            },
            options: {
                ...this.config.chartOptions,
                indexAxis: 'y',
                scales: {
                    x: {
                        beginAtZero: true
                    }
                }
            }
        });
    },

    /**
     * Create Performance Gauge
     */
    createPerformanceGauge() {
        const ctx = document.getElementById('performanceGauge').getContext('2d');

        return new Chart(ctx, {
            type: 'doughnut',
            data: {
                datasets: [{
                    data: [75, 25],
                    backgroundColor: [
                        FloorMS.config.chartColors.success,
                        '#e9ecef'
                    ],
                    borderWidth: 0
                }]
            },
            options: {
                ...this.config.chartOptions,
                circumference: 180,
                rotation: 270,
                cutout: '75%',
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        enabled: false
                    }
                }
            }
        });
    },

    /**
     * Load initial dashboard data
     */
    loadInitialData() {
        this.loadActivityTrend();
        this.loadSystemEvents();
        this.loadUserActivity();
        this.loadMetrics();
    },

    /**
     * Load activity trend data
     */
    loadActivityTrend() {
        FloorMS.ajax.get('/api/core/activity-logs/stats/', { days: 7 })
            .then(data => {
                if (this.charts.activityTrend && data.trend) {
                    this.charts.activityTrend.data.labels = data.trend.labels;
                    this.charts.activityTrend.data.datasets[0].data = data.trend.values;
                    this.charts.activityTrend.update();
                }
            })
            .catch(error => console.error('Error loading activity trend:', error));
    },

    /**
     * Load system events data
     */
    loadSystemEvents() {
        FloorMS.ajax.get('/api/core/system-events/stats/')
            .then(data => {
                if (this.charts.systemEvents && data.by_level) {
                    this.charts.systemEvents.data.datasets[0].data = [
                        data.by_level.CRITICAL || 0,
                        data.by_level.ERROR || 0,
                        data.by_level.WARNING || 0,
                        data.by_level.INFO || 0
                    ];
                    this.charts.systemEvents.update();
                }

                // Update event badges
                this.updateEventBadges(data);
            })
            .catch(error => console.error('Error loading system events:', error));
    },

    /**
     * Load user activity data
     */
    loadUserActivity() {
        FloorMS.ajax.get('/api/core/activity-logs/top-users/')
            .then(data => {
                if (this.charts.userActivity && data.users) {
                    this.charts.userActivity.data.labels = data.users.map(u => u.username);
                    this.charts.userActivity.data.datasets[0].data = data.users.map(u => u.count);
                    this.charts.userActivity.update();
                }
            })
            .catch(error => console.error('Error loading user activity:', error));
    },

    /**
     * Load real-time metrics
     */
    loadMetrics() {
        FloorMS.ajax.get('/api/core/health/')
            .then(data => {
                // Update metric cards
                this.updateMetricCard('totalActivities', data.total_activities);
                this.updateMetricCard('unresolvedErrors', data.unresolved_errors);
                this.updateMetricCard('activeUsers', data.active_users);
                this.updateMetricCard('systemHealth', data.health_score + '%');

                // Update performance gauge
                if (this.charts.performance) {
                    const healthScore = data.health_score || 0;
                    this.charts.performance.data.datasets[0].data = [healthScore, 100 - healthScore];

                    // Update color based on health
                    if (healthScore >= 80) {
                        this.charts.performance.data.datasets[0].backgroundColor[0] = FloorMS.config.chartColors.success;
                    } else if (healthScore >= 60) {
                        this.charts.performance.data.datasets[0].backgroundColor[0] = FloorMS.config.chartColors.warning;
                    } else {
                        this.charts.performance.data.datasets[0].backgroundColor[0] = FloorMS.config.chartColors.danger;
                    }

                    this.charts.performance.update();
                }
            })
            .catch(error => console.error('Error loading metrics:', error));
    },

    /**
     * Update metric card value
     */
    updateMetricCard(id, value) {
        const element = document.querySelector(`[data-metric="${id}"]`);
        if (element) {
            // Animate number change
            const currentValue = parseInt(element.textContent) || 0;
            this.animateValue(element, currentValue, value, 1000);
        }
    },

    /**
     * Animate number value
     */
    animateValue(element, start, end, duration) {
        const range = end - start;
        const increment = range / (duration / 16);
        let current = start;

        const timer = setInterval(() => {
            current += increment;
            if ((increment > 0 && current >= end) || (increment < 0 && current <= end)) {
                element.textContent = FloorMS.utils.formatNumber(end);
                clearInterval(timer);
            } else {
                element.textContent = FloorMS.utils.formatNumber(Math.round(current));
            }
        }, 16);
    },

    /**
     * Update event badges
     */
    updateEventBadges(data) {
        const badges = {
            'critical': data.by_level?.CRITICAL || 0,
            'error': data.by_level?.ERROR || 0,
            'warning': data.by_level?.WARNING || 0,
            'unresolved': data.unresolved || 0
        };

        Object.keys(badges).forEach(key => {
            const badge = document.querySelector(`[data-badge="${key}"]`);
            if (badge) {
                badge.textContent = badges[key];

                // Add pulse animation if value > 0
                if (badges[key] > 0) {
                    badge.classList.add('badge-pulse');
                } else {
                    badge.classList.remove('badge-pulse');
                }
            }
        });
    },

    /**
     * Start auto-refresh
     */
    startAutoRefresh() {
        this.refreshInterval = setInterval(() => {
            console.log('Auto-refreshing dashboard...');
            this.loadInitialData();
            this.updateLastRefreshTime();
        }, this.config.refreshRate);

        this.updateLastRefreshTime();
    },

    /**
     * Stop auto-refresh
     */
    stopAutoRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
        }
    },

    /**
     * Manual refresh
     */
    refresh() {
        FloorMS.notify.info('Refreshing dashboard...');
        this.loadInitialData();
        this.updateLastRefreshTime();
    },

    /**
     * Update last refresh time display
     */
    updateLastRefreshTime() {
        const element = document.getElementById('lastRefreshTime');
        if (element) {
            element.textContent = new Date().toLocaleTimeString();
        }
    },

    /**
     * Initialize event handlers
     */
    initializeEventHandlers() {
        // Refresh button
        const refreshBtn = document.getElementById('refreshDashboard');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.refresh());
        }

        // Auto-refresh toggle
        const autoRefreshToggle = document.getElementById('autoRefreshToggle');
        if (autoRefreshToggle) {
            autoRefreshToggle.addEventListener('change', (e) => {
                if (e.target.checked) {
                    this.startAutoRefresh();
                    FloorMS.notify.success('Auto-refresh enabled');
                } else {
                    this.stopAutoRefresh();
                    FloorMS.notify.info('Auto-refresh disabled');
                }
            });
        }

        // Export button
        const exportBtn = document.getElementById('exportDashboard');
        if (exportBtn) {
            exportBtn.addEventListener('click', () => this.exportData());
        }
    },

    /**
     * Export dashboard data
     */
    exportData() {
        FloorMS.modal.confirm(
            'Export Dashboard Data',
            'Choose export format:',
            () => {
                window.location.href = '/system/dashboard/export/?format=excel';
            }
        );
    }
};

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
    if (document.querySelector('[data-page="dashboard"]')) {
        Dashboard.init();
    }
});
