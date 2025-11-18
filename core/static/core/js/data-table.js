/**
 * Global Data Table Component JavaScript
 * Handles sorting, filtering, column visibility, bulk actions, and preferences
 */

(function() {
    'use strict';

    // Data Table Controller
    class DataTableController {
        constructor(tableId) {
            this.tableId = tableId;
            this.wrapper = document.getElementById(`${tableId}_wrapper`);
            this.table = document.getElementById(tableId);
            this.viewName = this.wrapper?.dataset.viewName || tableId;

            if (!this.wrapper || !this.table) {
                console.warn(`Table ${tableId} not found`);
                return;
            }

            this.init();
        }

        init() {
            this.bindSorting();
            this.bindSearch();
            this.bindFilters();
            this.bindColumnToggle();
            this.bindBulkActions();
            this.bindPageSize();
            this.bindExport();
            this.loadColumnPreferences();
        }

        // Sorting functionality
        bindSorting() {
            const sortableHeaders = this.table.querySelectorAll('.sortable-column');
            sortableHeaders.forEach(header => {
                header.style.cursor = 'pointer';
                header.addEventListener('click', () => this.handleSort(header));
            });
        }

        handleSort(header) {
            const columnKey = header.dataset.columnKey;
            let direction = header.dataset.sortDirection || '';

            // Toggle direction
            if (direction === 'asc') {
                direction = 'desc';
            } else if (direction === 'desc') {
                direction = '';
            } else {
                direction = 'asc';
            }

            // Update URL with sort parameters
            const url = new URL(window.location);
            if (direction) {
                url.searchParams.set('sort', columnKey);
                url.searchParams.set('order', direction);
            } else {
                url.searchParams.delete('sort');
                url.searchParams.delete('order');
            }
            url.searchParams.set('page', '1');
            window.location.href = url.toString();
        }

        // Search functionality
        bindSearch() {
            const searchInput = this.wrapper.querySelector('.table-search-input');
            if (!searchInput) return;

            let debounceTimer;
            searchInput.addEventListener('input', () => {
                clearTimeout(debounceTimer);
                debounceTimer = setTimeout(() => {
                    this.performSearch(searchInput.value);
                }, 500);
            });

            // Handle Enter key
            searchInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    clearTimeout(debounceTimer);
                    this.performSearch(searchInput.value);
                }
            });
        }

        performSearch(query) {
            const url = new URL(window.location);
            if (query) {
                url.searchParams.set('search', query);
            } else {
                url.searchParams.delete('search');
            }
            url.searchParams.set('page', '1');
            window.location.href = url.toString();
        }

        // Filter functionality
        bindFilters() {
            const filters = this.wrapper.querySelectorAll('.table-filter');
            filters.forEach(filter => {
                filter.addEventListener('change', () => {
                    this.applyFilters();
                });
            });
        }

        applyFilters() {
            const url = new URL(window.location);
            const filters = this.wrapper.querySelectorAll('.table-filter');

            filters.forEach(filter => {
                const key = filter.dataset.filterKey;
                const value = filter.value;
                if (value) {
                    url.searchParams.set(key, value);
                } else {
                    url.searchParams.delete(key);
                }
            });

            url.searchParams.set('page', '1');
            window.location.href = url.toString();
        }

        // Column visibility toggle
        bindColumnToggle() {
            const toggles = this.wrapper.querySelectorAll('.column-toggle');
            toggles.forEach(toggle => {
                toggle.addEventListener('change', () => {
                    this.toggleColumn(toggle.dataset.columnKey, toggle.checked);
                });
            });

            // Save preferences button
            const saveBtn = this.wrapper.querySelector('.save-column-config');
            if (saveBtn) {
                saveBtn.addEventListener('click', () => this.saveColumnPreferences());
            }
        }

        toggleColumn(columnKey, visible) {
            // Toggle header
            const header = this.table.querySelector(`th.column-${columnKey}`);
            if (header) {
                header.style.display = visible ? '' : 'none';
            }

            // Toggle all cells in this column
            const cells = this.table.querySelectorAll(`td.column-${columnKey}`);
            cells.forEach(cell => {
                cell.style.display = visible ? '' : 'none';
            });
        }

        loadColumnPreferences() {
            // Load from localStorage first (immediate)
            const savedConfig = localStorage.getItem(`table_columns_${this.viewName}`);
            if (savedConfig) {
                try {
                    const columns = JSON.parse(savedConfig);
                    this.applyColumnConfig(columns);
                } catch (e) {
                    console.warn('Failed to parse column config from localStorage');
                }
            }

            // Then try to load from server
            this.fetchColumnPreferencesFromServer();
        }

        async fetchColumnPreferencesFromServer() {
            try {
                const response = await fetch(`/api/user-preferences/table-columns/?view=${this.viewName}`);
                if (response.ok) {
                    const data = await response.json();
                    if (data.columns && data.columns.length > 0) {
                        this.applyColumnConfig(data.columns);
                        localStorage.setItem(`table_columns_${this.viewName}`, JSON.stringify(data.columns));
                    }
                }
            } catch (e) {
                // Server preferences not available, use localStorage
            }
        }

        applyColumnConfig(visibleColumns) {
            const allToggles = this.wrapper.querySelectorAll('.column-toggle');
            allToggles.forEach(toggle => {
                const columnKey = toggle.dataset.columnKey;
                const shouldBeVisible = visibleColumns.includes(columnKey);
                toggle.checked = shouldBeVisible;
                this.toggleColumn(columnKey, shouldBeVisible);
            });
        }

        async saveColumnPreferences() {
            const toggles = this.wrapper.querySelectorAll('.column-toggle:checked');
            const visibleColumns = Array.from(toggles).map(t => t.dataset.columnKey);

            // Save to localStorage immediately
            localStorage.setItem(`table_columns_${this.viewName}`, JSON.stringify(visibleColumns));

            // Save to server
            try {
                const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value ||
                                  this.getCookie('csrftoken');

                const response = await fetch('/api/user-preferences/table-columns/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken,
                    },
                    body: JSON.stringify({
                        view: this.viewName,
                        columns: visibleColumns,
                    }),
                });

                if (response.ok) {
                    this.showNotification('Column preferences saved!', 'success');
                } else {
                    this.showNotification('Saved locally. Server sync pending.', 'info');
                }
            } catch (e) {
                this.showNotification('Saved locally. Server sync pending.', 'info');
            }
        }

        // Bulk actions
        bindBulkActions() {
            const selectAllCheckbox = this.wrapper.querySelector('.select-all-rows');
            const rowCheckboxes = this.wrapper.querySelectorAll('.row-checkbox');
            const bulkActionsBar = document.getElementById(`${this.tableId}_bulk_actions`);
            const clearSelectionBtn = this.wrapper.querySelector('.clear-selection');
            const bulkActionBtns = this.wrapper.querySelectorAll('.bulk-action-btn');

            if (selectAllCheckbox) {
                selectAllCheckbox.addEventListener('change', () => {
                    rowCheckboxes.forEach(cb => cb.checked = selectAllCheckbox.checked);
                    this.updateBulkActionsBar();
                });
            }

            rowCheckboxes.forEach(cb => {
                cb.addEventListener('change', () => {
                    this.updateBulkActionsBar();
                });
            });

            if (clearSelectionBtn) {
                clearSelectionBtn.addEventListener('click', () => {
                    rowCheckboxes.forEach(cb => cb.checked = false);
                    if (selectAllCheckbox) selectAllCheckbox.checked = false;
                    this.updateBulkActionsBar();
                });
            }

            bulkActionBtns.forEach(btn => {
                btn.addEventListener('click', () => {
                    const action = btn.dataset.action;
                    const selectedIds = this.getSelectedIds();
                    this.handleBulkAction(action, selectedIds);
                });
            });
        }

        updateBulkActionsBar() {
            const selectedCount = this.getSelectedIds().length;
            const bulkActionsBar = document.getElementById(`${this.tableId}_bulk_actions`);
            const countBadge = bulkActionsBar?.querySelector('.selected-count');

            if (bulkActionsBar) {
                if (selectedCount > 0) {
                    bulkActionsBar.classList.remove('d-none');
                    if (countBadge) {
                        countBadge.textContent = `${selectedCount} selected`;
                    }
                } else {
                    bulkActionsBar.classList.add('d-none');
                }
            }
        }

        getSelectedIds() {
            const checkboxes = this.wrapper.querySelectorAll('.row-checkbox:checked');
            return Array.from(checkboxes).map(cb => cb.value);
        }

        handleBulkAction(action, ids) {
            if (ids.length === 0) {
                this.showNotification('No items selected', 'warning');
                return;
            }

            switch (action) {
                case 'delete':
                    if (confirm(`Are you sure you want to delete ${ids.length} item(s)?`)) {
                        this.executeBulkDelete(ids);
                    }
                    break;
                case 'export':
                    this.executeBulkExport(ids);
                    break;
                default:
                    console.log(`Bulk action: ${action}`, ids);
            }
        }

        async executeBulkDelete(ids) {
            try {
                const csrfToken = this.getCookie('csrftoken');
                const response = await fetch(`/api/bulk-delete/`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken,
                    },
                    body: JSON.stringify({
                        table: this.viewName,
                        ids: ids,
                    }),
                });

                if (response.ok) {
                    this.showNotification(`${ids.length} item(s) deleted`, 'success');
                    location.reload();
                } else {
                    this.showNotification('Delete operation failed', 'danger');
                }
            } catch (e) {
                this.showNotification('Delete operation failed', 'danger');
            }
        }

        executeBulkExport(ids) {
            // For now, just redirect with IDs
            const url = new URL(window.location);
            url.pathname = '/api/export/';
            url.searchParams.set('table', this.viewName);
            url.searchParams.set('ids', ids.join(','));
            window.open(url.toString(), '_blank');
        }

        // Page size selector
        bindPageSize() {
            const selector = this.wrapper.querySelector('.page-size-selector');
            if (selector) {
                selector.addEventListener('change', () => {
                    const url = new URL(window.location);
                    url.searchParams.set('page_size', selector.value);
                    url.searchParams.set('page', '1');
                    window.location.href = url.toString();
                });
            }
        }

        // Export functionality
        bindExport() {
            const exportBtns = this.wrapper.querySelectorAll('.export-table');
            exportBtns.forEach(btn => {
                btn.addEventListener('click', (e) => {
                    e.preventDefault();
                    const format = btn.dataset.format;
                    this.exportTable(format);
                });
            });
        }

        exportTable(format) {
            const url = new URL(window.location);
            url.pathname = '/api/export/';
            url.searchParams.set('table', this.viewName);
            url.searchParams.set('format', format);
            window.open(url.toString(), '_blank');
        }

        // Utility methods
        getCookie(name) {
            let cookieValue = null;
            if (document.cookie && document.cookie !== '') {
                const cookies = document.cookie.split(';');
                for (let i = 0; i < cookies.length; i++) {
                    const cookie = cookies[i].trim();
                    if (cookie.substring(0, name.length + 1) === (name + '=')) {
                        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                        break;
                    }
                }
            }
            return cookieValue;
        }

        showNotification(message, type = 'info') {
            // Create toast notification
            const toastContainer = document.getElementById('toast-container') || this.createToastContainer();

            const toast = document.createElement('div');
            toast.className = `toast align-items-center text-white bg-${type} border-0`;
            toast.setAttribute('role', 'alert');
            toast.innerHTML = `
                <div class="d-flex">
                    <div class="toast-body">${message}</div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
                </div>
            `;

            toastContainer.appendChild(toast);
            const bsToast = new bootstrap.Toast(toast, { delay: 3000 });
            bsToast.show();

            toast.addEventListener('hidden.bs.toast', () => toast.remove());
        }

        createToastContainer() {
            const container = document.createElement('div');
            container.id = 'toast-container';
            container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
            container.style.zIndex = '9999';
            document.body.appendChild(container);
            return container;
        }
    }

    // Initialize all data tables on page load
    document.addEventListener('DOMContentLoaded', function() {
        const tables = document.querySelectorAll('.data-table');
        tables.forEach(table => {
            new DataTableController(table.id);
        });
    });

    // Export for global access
    window.DataTableController = DataTableController;

})();
