/**
 * Floor Management System - Navigation & Sidebar
 *
 * Handles sidebar navigation, mobile menu interactions, and collapsible sections.
 *
 * Features:
 * - Mobile sidebar toggle with backdrop
 * - Collapsible navigation sections with state persistence
 * - Active link highlighting
 * - Responsive behavior for mobile/desktop
 */

// ========== NAVIGATION FUNCTIONS ==========

/**
 * Initialize sidebar toggle functionality
 * Handles mobile sidebar show/hide with backdrop
 */
function initSidebarToggle() {
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebar = document.getElementById('sidebar');
    const sidebarBackdrop = document.getElementById('sidebarBackdrop');

    if (!sidebarToggle || !sidebar) {
        return; // No sidebar on this page
    }

    // Toggle sidebar on button click
    sidebarToggle.addEventListener('click', function() {
        sidebar.classList.toggle('show');
        if (sidebarBackdrop) {
            sidebarBackdrop.classList.toggle('show');
        }
    });

    // Close sidebar when clicking backdrop (mobile)
    if (sidebarBackdrop) {
        sidebarBackdrop.addEventListener('click', function() {
            sidebar.classList.remove('show');
            sidebarBackdrop.classList.remove('show');
        });
    }

    // Close sidebar when clicking outside (mobile only)
    document.addEventListener('click', function(event) {
        if (window.innerWidth < 992) {
            const clickedInsideSidebar = sidebar.contains(event.target);
            const clickedToggleButton = sidebarToggle.contains(event.target);

            if (!clickedInsideSidebar && !clickedToggleButton) {
                sidebar.classList.remove('show');
                if (sidebarBackdrop) {
                    sidebarBackdrop.classList.remove('show');
                }
            }
        }
    });
}

/**
 * Initialize collapsible navigation sections
 * Persists expanded/collapsed state in localStorage
 * Auto-expands section containing current page
 */
function initCollapsibleSections() {
    const sectionToggles = document.querySelectorAll('.nav-section-toggle');
    const currentPath = window.location.pathname;

    sectionToggles.forEach(toggle => {
        const sectionId = toggle.getAttribute('data-section');
        const sectionContent = document.getElementById(sectionId);
        const toggleIcon = toggle.querySelector('.toggle-icon');

        if (!sectionContent) {
            return;
        }

        // Check if current page is within this section
        const sectionLinks = sectionContent.querySelectorAll('a.nav-sub-item');
        let isCurrentSection = false;

        sectionLinks.forEach(link => {
            const href = link.getAttribute('href');
            if (href && currentPath.startsWith(href.split('?')[0])) {
                isCurrentSection = true;
                link.classList.add('active');
            }
        });

        // Load saved state from localStorage OR auto-expand if current section
        const savedState = localStorage.getItem(`nav-section-${sectionId}`);

        if (isCurrentSection || savedState === 'expanded') {
            sectionContent.style.display = 'flex';
            if (toggleIcon) {
                toggleIcon.style.transform = 'rotate(180deg)';
            }
            // Save expanded state if it's the current section
            if (isCurrentSection) {
                localStorage.setItem(`nav-section-${sectionId}`, 'expanded');
            }
        }

        // Toggle section on click
        toggle.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation(); // Prevent event bubbling

            const isVisible = sectionContent.style.display !== 'none';

            if (isVisible) {
                // Collapse section
                sectionContent.style.display = 'none';
                if (toggleIcon) {
                    toggleIcon.style.transform = 'rotate(0deg)';
                }
                localStorage.setItem(`nav-section-${sectionId}`, 'collapsed');
            } else {
                // Expand section
                sectionContent.style.display = 'flex';
                if (toggleIcon) {
                    toggleIcon.style.transform = 'rotate(180deg)';
                }
                localStorage.setItem(`nav-section-${sectionId}`, 'expanded');
            }
        });
    });
}

/**
 * Highlight active navigation links based on current URL
 */
function highlightActiveNavLinks() {
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.nav-link, .nav-item a');

    navLinks.forEach(link => {
        const href = link.getAttribute('href');
        if (href && currentPath.startsWith(href) && href !== '/') {
            link.classList.add('active');
        }
    });
}

/**
 * Handle responsive navigation behavior
 * Adjusts navigation based on viewport width
 */
function handleResponsiveNav() {
    const sidebar = document.getElementById('sidebar');
    const sidebarBackdrop = document.getElementById('sidebarBackdrop');

    if (!sidebar) {
        return;
    }

    // Close mobile sidebar when resizing to desktop
    window.addEventListener('resize', function() {
        if (window.innerWidth >= 992) {
            sidebar.classList.remove('show');
            if (sidebarBackdrop) {
                sidebarBackdrop.classList.remove('show');
            }
        }
    });
}

/**
 * Initialize dropdown menus
 * Ensures dropdown menus work correctly
 */
function initDropdowns() {
    // Bootstrap handles most dropdown functionality
    // This function is for any custom dropdown behavior

    // Example: Close dropdown when clicking a link inside it
    document.querySelectorAll('.dropdown-menu a').forEach(link => {
        link.addEventListener('click', function() {
            // Bootstrap will handle closing the dropdown
            // This is here for any future custom behavior
        });
    });
}

/**
 * Keyboard navigation support
 * Adds keyboard shortcuts for navigation
 */
function initKeyboardNav() {
    document.addEventListener('keydown', function(e) {
        // ESC key closes mobile sidebar
        if (e.key === 'Escape') {
            const sidebar = document.getElementById('sidebar');
            const sidebarBackdrop = document.getElementById('sidebarBackdrop');

            if (sidebar && sidebar.classList.contains('show')) {
                sidebar.classList.remove('show');
                if (sidebarBackdrop) {
                    sidebarBackdrop.classList.remove('show');
                }
            }
        }
    });
}

// ========== INITIALIZATION ==========

document.addEventListener('DOMContentLoaded', function() {
    initSidebarToggle();
    initCollapsibleSections();
    highlightActiveNavLinks();
    handleResponsiveNav();
    initDropdowns();
    initKeyboardNav();
});

// Make navigation functions globally available
window.initSidebarToggle = initSidebarToggle;
window.initCollapsibleSections = initCollapsibleSections;
window.highlightActiveNavLinks = highlightActiveNavLinks;
