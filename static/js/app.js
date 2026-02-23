/**
 * Mission Control - Bulletproof JavaScript
 * Simple, reliable vanilla JS with progressive enhancement
 */

(function() {
    'use strict';

    // Utility functions
    function $(selector) {
        return document.querySelector(selector);
    }

    function $$(selector) {
        return document.querySelectorAll(selector);
    }

    // Safe event listener wrapper
    function onReady(callback) {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', callback);
        } else {
            callback();
        }
    }

    // Toast notification system
    window.showToast = function(message, type) {
        type = type || 'info';
        
        // Remove existing toast
        var existing = $('.toast');
        if (existing) {
            existing.remove();
        }
        
        // Create new toast
        var toast = document.createElement('div');
        toast.className = 'toast toast-' + type;
        toast.textContent = message;
        toast.style.cssText = 'position:fixed;bottom:2rem;right:2rem;padding:1rem 1.5rem;' +
            'border-radius:8px;font-weight:500;z-index:1000;animation:slideIn 0.3s ease;';
        
        if (type === 'success') {
            toast.style.background = '#22c55e';
            toast.style.color = 'white';
        } else if (type === 'error') {
            toast.style.background = '#ef4444';
            toast.style.color = 'white';
        }
        
        document.body.appendChild(toast);
        
        // Auto remove
        setTimeout(function() {
            if (toast.parentNode) {
                toast.remove();
            }
        }, 3000);
    };

    // Escape HTML to prevent XSS
    window.escapeHtml = function(text) {
        var div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    };

    // Navigation active state
    function initNavigation() {
        var currentPath = window.location.pathname;
        var navLinks = $$('.nav-link');
        
        navLinks.forEach(function(link) {
            var href = link.getAttribute('href');
            if (href && currentPath.startsWith(href) && href !== '/') {
                link.parentElement.classList.add('active');
            } else if (href === '/' && currentPath === '/') {
                link.parentElement.classList.add('active');
            }
            
            // Ensure proper touch handling on mobile
            link.addEventListener('touchstart', function(e) {
                // Prevent any default touch behaviors that might interfere
                e.stopPropagation();
            }, {passive: true});
            
            link.addEventListener('click', function(e) {
                // Let the default link behavior work (navigation)
                // Just update active state visually before navigation
                navLinks.forEach(function(l) {
                    l.parentElement.classList.remove('active');
                });
                this.parentElement.classList.add('active');
            });
        });
    }

    // Auto-hide flash messages
    function initFlashMessages() {
        var flashes = $$('.flash');
        
        flashes.forEach(function(flash) {
            setTimeout(function() {
                flash.style.opacity = '0';
                flash.style.transition = 'opacity 0.5s ease';
                setTimeout(function() {
                    if (flash.parentNode) {
                        flash.remove();
                    }
                }, 500);
            }, 5000);
        });
    }

    // Chat functionality enhancement
    function initChat() {
        var chatForm = $('#chat-form');
        var messageInput = $('#message-input');
        
        if (!chatForm || !messageInput) return;
        
        // Focus input on load
        messageInput.focus();
        
        // Handle form submission
        chatForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            var message = messageInput.value.trim();
            if (!message) return;
            
            // The form's onsubmit handler will handle the actual sending
            // This is just for progressive enhancement
        });
        
        // Keyboard shortcuts
        messageInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                chatForm.dispatchEvent(new Event('submit'));
            }
        });
    }

    // Project progress slider enhancement
    function initProjectSliders() {
        var sliders = $$('.progress-slider');
        
        sliders.forEach(function(slider) {
            var projectId = slider.dataset.projectId;
            var fill = $('#progress-fill-' + projectId);
            var text = $('#progress-text-' + projectId);
            
            if (!fill || !text) return;
            
            // Update visual feedback while dragging
            slider.addEventListener('input', function() {
                var value = this.value;
                fill.style.width = value + '%';
                text.textContent = value + '%';
            });
        });
    }

    // Command center form enhancement
    function initCommandCenter() {
        var spawnForm = $('#spawn-form');
        var agentSelect = $('#agent-select');
        var taskInput = $('#task-input');
        
        if (!spawnForm) return;
        
        // Focus task input when agent selected
        if (agentSelect) {
            agentSelect.addEventListener('change', function() {
                if (this.value && taskInput) {
                    taskInput.focus();
                }
            });
        }
    }

    // Modal functionality
    function initModals() {
        var modals = $$('.modal');
        
        modals.forEach(function(modal) {
            // Close on outside click
            modal.addEventListener('click', function(e) {
                if (e.target === modal) {
                    modal.style.display = 'none';
                }
            });
            
            // Close on escape key
            document.addEventListener('keydown', function(e) {
                if (e.key === 'Escape' && modal.style.display === 'block') {
                    modal.style.display = 'none';
                }
            });
        });
    }

    // Status polling (optional - for live updates)
    function initStatusPolling() {
        // Poll agent statuses every 30 seconds
        setInterval(function() {
            fetch('/api/agents/status')
                .then(function(response) { return response.json(); })
                .then(function(data) {
                    if (data.success && data.agents) {
                        updateAgentStatuses(data.agents);
                    }
                })
                .catch(function(err) {
                    // Silently fail - don't spam console
                });
        }, 30000);
    }

    // Update agent status badges
    function updateAgentStatuses(agents) {
        agents.forEach(function(agent) {
            var badges = $$('.status-badge');
            badges.forEach(function(badge) {
                // Find badges that belong to this agent
                var card = badge.closest('[data-agent-id]');
                if (card && card.dataset.agentId == agent.id) {
                    badge.className = 'status-badge status-' + agent.status;
                    badge.textContent = agent.status;
                }
            });
        });
    }

    // Initialize everything when DOM is ready
    onReady(function() {
        initNavigation();
        initFlashMessages();
        initChat();
        initProjectSliders();
        initCommandCenter();
        initModals();
        initStatusPolling();
        
        console.log('🎯 Mission Control initialized');
    });

})();
