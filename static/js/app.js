/**
 * Adishi's dayplan Client Application Logic
 * Integrates with Python Flask JSON API.
 */

document.addEventListener('DOMContentLoaded', () => {
    // Application State
    const state = {
        tasks: [],
        stats: {},
        currentTab: 'dashboard', // 'dashboard' or 'planner'
        filters: {
            date: 'all', // 'all', 'today', 'tomorrow', 'upcoming', 'custom'
            customDate: '',
            priority: 'all', // 'all', 'high', 'medium', 'low'
            status: 'all', // 'all', 'pending', 'completed'
            search: ''
        },
        deleteTargetId: null
    };

    // DOM Selectors
    const body = document.body;
    const themeToggle = document.getElementById('theme-toggle');
    const currentHeaderDate = document.getElementById('current-header-date');
    
    // Navigation Tabs
    const tabDashboard = document.getElementById('tab-dashboard');
    const tabPlanner = document.getElementById('tab-planner');
    const viewDashboard = document.getElementById('view-dashboard');
    const viewPlanner = document.getElementById('view-planner');
    
    // Quotes Section
    const quoteText = document.getElementById('quote-text');
    const quoteAuthor = document.getElementById('quote-author');
    const refreshQuoteBtn = document.getElementById('refresh-quote');

    // Dashboard View Components
    const welcomeMessage = document.getElementById('welcome-message');
    const productivityMessage = document.getElementById('productivity-message');
    const completionPercentage = document.getElementById('completion-percentage');
    const dashboardProgressFill = document.getElementById('dashboard-progress-fill');
    const statTotalTasks = document.getElementById('stat-total-tasks');
    const statCompletedTasks = document.getElementById('stat-completed-tasks');
    const statPendingTasks = document.getElementById('stat-pending-tasks');
    const dashboardTodayList = document.getElementById('dashboard-today-list');
    
    // Priority Distribution Bars
    const pbarHigh = document.getElementById('pbar-high');
    const pbarMedium = document.getElementById('pbar-medium');
    const pbarLow = document.getElementById('pbar-low');
    const pcountHigh = document.getElementById('pcount-high');
    const pcountMedium = document.getElementById('pcount-medium');
    const pcountLow = document.getElementById('pcount-low');
    const upcomingDatesList = document.getElementById('upcoming-dates-list');

    // Planner View Components
    const btnOpenAddModal = document.getElementById('btn-open-add-modal');
    const searchInput = document.getElementById('search-input');
    const clearSearchBtn = document.getElementById('clear-search');
    
    // Planner Filters
    const filterDate = document.getElementById('filter-date');
    const filterDateCustom = document.getElementById('filter-date-custom');
    const filterPriority = document.getElementById('filter-priority');
    const filterStatus = document.getElementById('filter-status');
    const btnClearFilters = document.getElementById('btn-clear-filters');
    const activeTagsContainer = document.getElementById('active-tags');
    const tagsList = document.getElementById('tags-list');
    
    const plannerTasksCount = document.getElementById('planner-tasks-count');
    const plannerProgressFill = document.getElementById('planner-progress-fill');
    const tasksListContainer = document.getElementById('tasks-list-container');

    // Task Modals
    const taskModal = document.getElementById('task-modal');
    const taskForm = document.getElementById('task-form');
    const modalTitle = document.getElementById('modal-title');
    const taskIdField = document.getElementById('task-id');
    const taskTitleField = document.getElementById('task-title');
    const taskDescField = document.getElementById('task-description');
    const taskDateField = document.getElementById('task-date');
    const taskPriorityField = document.getElementById('task-priority');
    const modalCompletedGroup = document.getElementById('modal-completed-group');
    const taskCompletedCheckbox = document.getElementById('task-completed');
    const btnCloseTaskModal = document.getElementById('btn-close-task-modal');
    const btnCancelTask = document.getElementById('btn-cancel-task');
    
    // Delete Confirmation Modal
    const deleteModal = document.getElementById('delete-modal');
    const btnCloseDeleteModal = document.getElementById('btn-close-delete-modal');
    const btnCancelDelete = document.getElementById('btn-cancel-delete');
    const btnConfirmDelete = document.getElementById('btn-confirm-delete');
    const deletePreviewContent = document.getElementById('delete-preview-content');

    // Toast Container
    const toastContainer = document.getElementById('toast-container');

    /* ==========================================================================
       INITIALIZATION & THEME MANAGER
       ========================================================================== */

    function init() {
        // Set up local time display in header
        updateHeaderDate();
        setInterval(updateHeaderDate, 60000);

        // Theme Initialization
        const savedTheme = localStorage.getItem('theme') || 'light-theme';
        body.className = savedTheme;

        // Populate Default Form Dates
        const todayStr = getLocalDateString(new Date());
        taskDateField.value = todayStr;
        filterDateCustom.value = todayStr;

        // Fetch Initial Content
        fetchQuote();
        fetchStatsAndRender();
        fetchTasksAndRender();

        // Register Event Listeners
        registerEventListeners();
    }

    // Displays the current date formatted nicely in the header
    function updateHeaderDate() {
        const now = new Date();
        const options = { weekday: 'short', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' };
        currentHeaderDate.textContent = now.toLocaleDateString('en-US', options);
    }

    // Format Date helper ensuring ISO local string format: YYYY-MM-DD
    function getLocalDateString(date) {
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
    }

    // Toggle theme with CSS classes and local storage persistence
    themeToggle.addEventListener('click', () => {
        if (body.classList.contains('light-theme')) {
            body.classList.replace('light-theme', 'dark-theme');
            localStorage.setItem('theme', 'dark-theme');
            showToast('Dark mode enabled ✨', 'success');
        } else {
            body.classList.replace('dark-theme', 'light-theme');
            localStorage.setItem('theme', 'light-theme');
            showToast('Light mode enabled ☀️', 'success');
        }
    });

    /* ==========================================================================
       NAVIGATION & VIEW SWITCHING
       ========================================================================== */

    function switchTab(tabId) {
        state.currentTab = tabId;

        // Update Nav Tabs Active Class
        tabDashboard.classList.toggle('active', tabId === 'dashboard');
        tabPlanner.classList.toggle('active', tabId === 'planner');

        // Update Views Visibility
        viewDashboard.classList.toggle('active', tabId === 'dashboard');
        viewPlanner.classList.toggle('active', tabId === 'planner');

        // Refresh view specific data
        if (tabId === 'dashboard') {
            fetchStatsAndRender();
        } else {
            fetchTasksAndRender();
        }
    }

    function registerEventListeners() {
        // Tabs Switching
        tabDashboard.addEventListener('click', () => switchTab('dashboard'));
        tabPlanner.addEventListener('click', () => switchTab('planner'));

        // Handle Quick Link from Dashboard (Manage All)
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('go-to-planner')) {
                const targetFilter = e.target.getAttribute('data-target-filter');
                if (targetFilter === 'today') {
                    state.filters.date = 'today';
                    filterDate.value = 'today';
                }
                switchTab('planner');
            }
        });

        // Quotes Refresh
        refreshQuoteBtn.addEventListener('click', fetchQuote);

        // Modals Management
        btnOpenAddModal.addEventListener('click', () => openTaskModal());
        btnCloseTaskModal.addEventListener('click', closeTaskModal);
        btnCancelTask.addEventListener('click', closeTaskModal);
        
        btnCloseDeleteModal.addEventListener('click', closeDeleteModal);
        btnCancelDelete.addEventListener('click', closeDeleteModal);
        btnConfirmDelete.addEventListener('click', deleteConfirmed);

        // Close modal clicking outside content
        window.addEventListener('click', (e) => {
            if (e.target === taskModal) closeTaskModal();
            if (e.target === deleteModal) closeDeleteModal();
        });

        // Form Submit
        taskForm.addEventListener('submit', handleTaskFormSubmit);

        // Planner Actions & Filters
        searchInput.addEventListener('input', handleSearchInput);
        clearSearchBtn.addEventListener('click', () => {
            searchInput.value = '';
            clearSearchBtn.style.display = 'none';
            state.filters.search = '';
            fetchTasksAndRender();
        });

        filterDate.addEventListener('change', handleDateFilterChange);
        filterDateCustom.addEventListener('change', handleCustomDateChange);
        filterPriority.addEventListener('change', handlePriorityFilterChange);
        filterStatus.addEventListener('change', handleStatusFilterChange);
        btnClearFilters.addEventListener('click', resetFilters);
    }

    /* ==========================================================================
       TOAST NOTIFICATIONS
       ========================================================================== */

    function showToast(message, type = 'success') {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        
        toast.innerHTML = `
            <span class="toast-message">${message}</span>
            <button class="toast-close">&times;</button>
        `;

        toastContainer.appendChild(toast);

        // Auto remove toast
        const autoRemove = setTimeout(() => {
            removeToast(toast);
        }, 4000);

        toast.querySelector('.toast-close').addEventListener('click', () => {
            clearTimeout(autoRemove);
            removeToast(toast);
        });
    }

    function removeToast(toast) {
        toast.style.animation = 'fadeIn 0.3s ease reverse forwards';
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 300);
    }

    /* ==========================================================================
       DATA FETCHING & RENDERING (API INTEGRATION)
       ========================================================================== */

    // Fetch and display motivational quote
    async function fetchQuote() {
        try {
            refreshQuoteBtn.classList.add('spinning');
            const response = await fetch('/api/quote');
            const data = await response.json();
            quoteText.textContent = data.text;
            quoteAuthor.textContent = `— ${data.author}`;
        } catch (error) {
            console.error('Error fetching quote:', error);
            quoteText.textContent = "Your productivity is an investment in your future.";
            quoteAuthor.textContent = "— Anonymous";
        } finally {
            setTimeout(() => {
                refreshQuoteBtn.classList.remove('spinning');
            }, 500);
        }
    }

    // Fetch productivity metrics and update Dashboard UI
    async function fetchStatsAndRender() {
        try {
            const response = await fetch('/api/stats');
            const stats = await response.json();
            state.stats = stats;
            renderDashboardStats(stats);
        } catch (error) {
            console.error('Error fetching stats:', error);
            showToast('Failed to sync productivity data.', 'danger');
        }
    }

    function renderDashboardStats(stats) {
        // Welcome and Productivity Message
        const now = new Date();
        const hrs = now.getHours();
        let greeting = 'Good Evening';
        if (hrs < 12) greeting = 'Good Morning';
        else if (hrs < 18) greeting = 'Good Afternoon';
        
        const username = body.getAttribute('data-username') || 'Goal Getter';
        welcomeMessage.textContent = `${greeting}, ${username}`;

        // Update Stat Counters
        statTotalTasks.textContent = stats.total;
        statCompletedTasks.textContent = stats.completed;
        statPendingTasks.textContent = stats.pending;

        // Progress Fill Details
        const completionRate = stats.completion_rate;
        completionPercentage.textContent = `${completionRate}%`;
        dashboardProgressFill.style.width = `${completionRate}%`;

        // Interactive status message
        if (stats.total === 0) {
            productivityMessage.textContent = "Welcome! Add some tasks in the Task Planner tab to begin planning your day.";
        } else if (stats.pending === 0) {
            productivityMessage.textContent = "🎉 Excellent job! You've checked off every single task scheduled.";
        } else if (completionRate >= 75) {
            productivityMessage.textContent = `🚀 Phenomenal momentum! Just ${stats.pending} remaining tasks to absolute completion.`;
        } else if (completionRate >= 40) {
            productivityMessage.textContent = `💪 You're doing great! Keep going to knock out the last ${stats.pending} tasks.`;
        } else {
            productivityMessage.textContent = `Focus up! You have ${stats.pending} pending tasks waiting for your action.`;
        }

        // Priority breakdown progress bars
        const priorities = ['high', 'medium', 'low'];
        priorities.forEach(p => {
            const data = stats.priority_breakdown[p];
            const bar = document.getElementById(`pbar-${p}`);
            const counter = document.getElementById(`pcount-${p}`);
            
            counter.textContent = `${data.completed}/${data.total}`;
            const percentage = data.total > 0 ? (data.completed / data.total * 100) : 0;
            bar.style.width = `${percentage}%`;
        });

        // Load today's list dynamically on Dashboard
        fetchTodayHighlightTasks();
    }

    // Fetch and display incomplete/today's tasks in dashboard Focus card
    async function fetchTodayHighlightTasks() {
        const todayStr = getLocalDateString(new Date());
        try {
            const response = await fetch(`/api/tasks?date=${todayStr}`);
            const tasks = await response.json();
            
            dashboardTodayList.innerHTML = '';
            
            if (tasks.length === 0) {
                dashboardTodayList.innerHTML = `<p class="empty-state-text">No tasks scheduled for today. Take it easy or schedule a task!</p>`;
                return;
            }

            tasks.forEach(task => {
                const isCompleted = task.completed === 1;
                const taskEl = document.createElement('div');
                taskEl.className = `compact-task-item ${isCompleted ? 'completed-task' : ''}`;
                
                taskEl.innerHTML = `
                    <div class="compact-task-left">
                        <span class="priority-badge-dot ${task.priority}"></span>
                        <span class="compact-task-title">${escapeHTML(task.title)}</span>
                    </div>
                    <div>
                        <input type="checkbox" class="task-checkbox-quick" data-id="${task.id}" ${isCompleted ? 'checked' : ''} style="cursor:pointer;">
                    </div>
                `;

                // Handle quick complete toggle on dashboard focus list
                taskEl.querySelector('.task-checkbox-quick').addEventListener('change', async (e) => {
                    const isChecked = e.target.checked;
                    await toggleTaskCompletion(task.id, isChecked);
                    fetchStatsAndRender(); // refresh dashboard stats
                });

                dashboardTodayList.appendChild(taskEl);
            });
        } catch (error) {
            console.error('Error fetching today highlight tasks:', error);
        }
    }

    // Fetch, filter, and display tasks in the main Task Planner list
    async function fetchTasksAndRender() {
        tasksListContainer.innerHTML = `
            <div class="loading-state">
                <div class="spinner"></div>
                <p>Syncing your schedule...</p>
            </div>
        `;

        try {
            // Build Query Parameters string based on filter state
            const params = new URLSearchParams();
            
            // Handle dates query mappings
            const todayStr = getLocalDateString(new Date());
            if (state.filters.date === 'today') {
                params.append('date', todayStr);
            } else if (state.filters.date === 'tomorrow') {
                const tomorrow = new Date();
                tomorrow.setDate(tomorrow.getDate() + 1);
                params.append('date', getLocalDateString(tomorrow));
            } else if (state.filters.date === 'custom' && state.filters.customDate) {
                params.append('date', state.filters.customDate);
            }
            
            if (state.filters.priority !== 'all') {
                params.append('priority', state.filters.priority);
            }
            
            if (state.filters.status === 'completed') {
                params.append('completed', 'true');
            } else if (state.filters.status === 'pending') {
                params.append('completed', 'false');
            }

            if (state.filters.search) {
                params.append('search', state.filters.search);
            }

            const response = await fetch(`/api/tasks?${params.toString()}`);
            let tasks = await response.json();
            
            // Client side 'upcoming' filter processing (Flask returns all ordered by date)
            if (state.filters.date === 'upcoming') {
                tasks = tasks.filter(task => task.date > todayStr);
            }

            state.tasks = tasks;
            
            renderPlannerTasks(tasks);
            renderFilterTags();
            updateUpcomingDatesSummary(tasks);
        } catch (error) {
            console.error('Error fetching tasks:', error);
            tasksListContainer.innerHTML = `
                <div class="empty-state">
                    <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="var(--color-danger)" stroke-width="2">
                        <circle cx="12" cy="12" r="10"></circle>
                        <line x1="12" y1="8" x2="12" y2="12"></line>
                        <line x1="12" y1="16" x2="12.01" y2="16"></line>
                    </svg>
                    <p>Failed to load tasks. Please try refreshing.</p>
                </div>
            `;
        }
    }

    function renderPlannerTasks(tasks) {
        tasksListContainer.innerHTML = '';
        
        // Update task counts in sub-header bar
        const totalCount = tasks.length;
        const completedCount = tasks.filter(t => t.completed === 1).length;
        const pendingCount = totalCount - completedCount;
        
        plannerTasksCount.textContent = `Showing ${totalCount} tasks (${pendingCount} pending, ${completedCount} completed)`;
        const percentage = totalCount > 0 ? (completedCount / totalCount * 100) : 0;
        plannerProgressFill.style.width = `${percentage}%`;

        if (tasks.length === 0) {
            tasksListContainer.innerHTML = `
                <div class="empty-state">
                    <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                        <circle cx="12" cy="12" r="10"></circle>
                        <line x1="8" y1="12" x2="16" y2="12"></line>
                    </svg>
                    <h3>No Tasks Found</h3>
                    <p>We couldn't find any tasks matching your current filters. Try resetting filters or adding a new task!</p>
                </div>
            `;
            return;
        }

        tasks.forEach(task => {
            const isCompleted = task.completed === 1;
            const card = document.createElement('div');
            card.className = `task-card ${isCompleted ? 'completed-task-card' : ''}`;
            card.setAttribute('data-id', task.id);

            card.innerHTML = `
                <div class="task-card-top">
                    <label class="checkbox-container">
                        <input type="checkbox" class="task-toggle-checkbox" data-id="${task.id}" ${isCompleted ? 'checked' : ''}>
                        <span class="checkmark"></span>
                    </label>
                    
                    <div class="card-badges">
                        <span class="badge priority-${task.priority}">${task.priority}</span>
                    </div>
                </div>
                
                <div class="task-card-content">
                    <h3 class="task-card-title">${escapeHTML(task.title)}</h3>
                    <p class="task-card-description">${escapeHTML(task.description || 'No description provided.')}</p>
                </div>
                
                <div class="task-card-bottom">
                    <div class="task-date-display">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
                            <line x1="16" y1="2" x2="16" y2="6"></line>
                            <line x1="8" y1="2" x2="8" y2="6"></line>
                            <line x1="3" y1="10" x2="21" y2="10"></line>
                        </svg>
                        <span>${formatTaskDateReadable(task.date)}</span>
                    </div>
                    
                    <div class="task-actions">
                        <button class="btn-card-action btn-edit" title="Edit Task" data-id="${task.id}">
                            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                                <path d="M18.5 2.5a2.121 2.121 0 1 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
                            </svg>
                        </button>
                        <button class="btn-card-action btn-delete" title="Delete Task" data-id="${task.id}">
                            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <polyline points="3 6 5 6 21 6"></polyline>
                                <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                                <line x1="10" y1="11" x2="10" y2="17"></line>
                                <line x1="14" y1="11" x2="14" y2="17"></line>
                            </svg>
                        </button>
                    </div>
                </div>
            `;

            // Bind checkbox events for dynamically created checkboxes
            card.querySelector('.task-toggle-checkbox').addEventListener('change', async (e) => {
                const isChecked = e.target.checked;
                await toggleTaskCompletion(task.id, isChecked);
                fetchTasksAndRender(); // Re-render to reflect style updates
            });

            // Bind edit/delete click handlers
            card.querySelector('.btn-edit').addEventListener('click', () => openTaskModal(task));
            card.querySelector('.btn-delete').addEventListener('click', () => openDeleteModal(task));

            tasksListContainer.appendChild(card);
        });
    }

    // Renders the mini listing of upcoming dates on the dashboard panel
    function updateUpcomingDatesSummary(allTasks) {
        upcomingDatesList.innerHTML = '';
        const todayStr = getLocalDateString(new Date());
        
        // Group tasks by upcoming dates
        const dateGroups = {};
        allTasks.forEach(task => {
            if (task.date > todayStr) {
                dateGroups[task.date] = (dateGroups[task.date] || 0) + 1;
            }
        });

        const sortedDates = Object.keys(dateGroups).sort();

        if (sortedDates.length === 0) {
            upcomingDatesList.innerHTML = `<p class="empty-state-text">No upcoming tasks scheduled.</p>`;
            return;
        }

        // Display up to 4 upcoming dates
        sortedDates.slice(0, 4).forEach(date => {
            const count = dateGroups[date];
            const row = document.createElement('div');
            row.className = 'upcoming-date-row';
            row.innerHTML = `
                <span class="upcoming-date-text">${formatTaskDateReadable(date)}</span>
                <span class="upcoming-date-badge">${count} Task${count > 1 ? 's' : ''}</span>
            `;
            upcomingDatesList.appendChild(row);
        });
    }

    // Date formatting helper for UI cards (e.g. June 17, 2026 or Today/Tomorrow)
    function formatTaskDateReadable(dateStr) {
        const todayStr = getLocalDateString(new Date());
        const tomorrow = new Date();
        tomorrow.setDate(tomorrow.getDate() + 1);
        const tomorrowStr = getLocalDateString(tomorrow);
        
        if (dateStr === todayStr) return "Today";
        if (dateStr === tomorrowStr) return "Tomorrow";

        // Parse YYYY-MM-DD to avoid timezone shifting issues
        const parts = dateStr.split('-');
        const dateObj = new Date(parts[0], parts[1] - 1, parts[2]);
        
        return dateObj.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
    }

    /* ==========================================================================
       CRUD MUTATION WORKFLOWS (API ENDPOINTS CALLS)
       ========================================================================== */

    async function toggleTaskCompletion(taskId, isChecked) {
        try {
            const response = await fetch(`/api/tasks/${taskId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ completed: isChecked ? 1 : 0 })
            });

            if (response.ok) {
                const statusStr = isChecked ? 'completed' : 're-opened';
                showToast(`Task marked as ${statusStr}!`, 'success');
            } else {
                throw new Error('Server returned error status');
            }
        } catch (error) {
            console.error('Error toggling task completion:', error);
            showToast('Failed to update task completion.', 'danger');
            fetchTasksAndRender(); // restore state on error
        }
    }

    async function handleTaskFormSubmit(e) {
        e.preventDefault();
        
        const taskId = taskIdField.value;
        const title = taskTitleField.value.trim();
        const description = taskDescField.value.trim();
        const date = taskDateField.value;
        const priority = taskPriorityField.value;
        const completed = taskCompletedCheckbox.checked ? 1 : 0;

        if (!title) {
            showToast('Title is required!', 'warning');
            return;
        }

        const payload = { title, description, date, priority };
        if (taskId) {
            payload.completed = completed;
        }

        const url = taskId ? `/api/tasks/${taskId}` : '/api/tasks';
        const method = taskId ? 'PUT' : 'POST';

        try {
            const response = await fetch(url, {
                method: method,
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (response.ok) {
                showToast(taskId ? 'Task updated successfully!' : 'New task added!', 'success');
                closeTaskModal();
                fetchTasksAndRender();
            } else {
                const data = await response.json();
                showToast(data.error || 'Operation failed.', 'danger');
            }
        } catch (error) {
            console.error('Error submitting form:', error);
            showToast('Something went wrong. Please try again.', 'danger');
        }
    }

    // Deletes a task after confirmation modal approved
    async function deleteConfirmed() {
        if (!state.deleteTargetId) return;

        try {
            const response = await fetch(`/api/tasks/${state.deleteTargetId}`, {
                method: 'DELETE'
            });

            if (response.ok) {
                showToast('Task deleted successfully.', 'success');
                closeDeleteModal();
                fetchTasksAndRender();
            } else {
                showToast('Failed to delete task.', 'danger');
            }
        } catch (error) {
            console.error('Error deleting task:', error);
            showToast('An error occurred. Check backend logs.', 'danger');
        }
    }

    /* ==========================================================================
       MODALS OPEN/CLOSE WORKFLOWS
       ========================================================================== */

    function openTaskModal(task = null) {
        taskModal.classList.add('open');
        taskTitleField.focus();

        if (task) {
            // Edit Mode Configuration
            modalTitle.textContent = "Edit Task";
            taskIdField.value = task.id;
            taskTitleField.value = task.title;
            taskDescField.value = task.description || '';
            taskDateField.value = task.date;
            taskPriorityField.value = task.priority;
            modalCompletedGroup.style.display = 'block';
            taskCompletedCheckbox.checked = task.completed === 1;
        } else {
            // Create Mode Configuration
            modalTitle.textContent = "Create New Task";
            taskIdField.value = '';
            taskForm.reset();
            
            // Re-populate default date with today
            taskDateField.value = getLocalDateString(new Date());
            modalCompletedGroup.style.display = 'none';
            taskCompletedCheckbox.checked = false;
        }
    }

    function closeTaskModal() {
        taskModal.classList.remove('open');
        taskForm.reset();
    }

    function openDeleteModal(task) {
        state.deleteTargetId = task.id;
        deletePreviewContent.innerHTML = `
            <strong>${escapeHTML(task.title)}</strong>
            <span class="preview-date">Scheduled: ${formatTaskDateReadable(task.date)}</span>
        `;
        deleteModal.classList.add('open');
    }

    function closeDeleteModal() {
        deleteModal.classList.remove('open');
        state.deleteTargetId = null;
    }

    /* ==========================================================================
       FILTERS, SEARCH & TAGS MANAGEMENT
       ========================================================================== */

    function handleSearchInput() {
        const val = searchInput.value.trim();
        state.filters.search = val;
        clearSearchBtn.style.display = val ? 'block' : 'none';
        
        // Debounce search slightly to avoid excessive API requests
        clearTimeout(state.searchDebounceTimer);
        state.searchDebounceTimer = setTimeout(() => {
            fetchTasksAndRender();
        }, 300);
    }

    function handleDateFilterChange(e) {
        const val = e.target.value;
        state.filters.date = val;
        
        if (val === 'custom') {
            filterDateCustom.style.display = 'block';
            state.filters.customDate = filterDateCustom.value;
        } else {
            filterDateCustom.style.display = 'none';
            state.filters.customDate = '';
        }
        
        fetchTasksAndRender();
    }

    function handleCustomDateChange(e) {
        state.filters.customDate = e.target.value;
        fetchTasksAndRender();
    }

    function handlePriorityFilterChange(e) {
        state.filters.priority = e.target.value;
        fetchTasksAndRender();
    }

    function handleStatusFilterChange(e) {
        state.filters.status = e.target.value;
        fetchTasksAndRender();
    }

    // Reset filters to default state
    function resetFilters() {
        state.filters = {
            date: 'all',
            customDate: '',
            priority: 'all',
            status: 'all',
            search: ''
        };

        // Reset inputs values
        filterDate.value = 'all';
        filterDateCustom.style.display = 'none';
        filterDateCustom.value = getLocalDateString(new Date());
        filterPriority.value = 'all';
        filterStatus.value = 'all';
        searchInput.value = '';
        clearSearchBtn.style.display = 'none';

        fetchTasksAndRender();
        showToast('All filters cleared!', 'success');
    }

    // Render badge tags indicating active filters
    function renderFilterTags() {
        tagsList.innerHTML = '';
        let hasActiveFilters = false;

        // Date Filter tags
        if (state.filters.date !== 'all') {
            hasActiveFilters = true;
            let label = `Time: ${state.filters.date}`;
            if (state.filters.date === 'custom' && state.filters.customDate) {
                label = `Date: ${formatTaskDateReadable(state.filters.customDate)}`;
            }
            createTagElement(label, () => {
                state.filters.date = 'all';
                filterDate.value = 'all';
                filterDateCustom.style.display = 'none';
                fetchTasksAndRender();
            });
        }

        // Priority Filter tags
        if (state.filters.priority !== 'all') {
            hasActiveFilters = true;
            createTagElement(`Priority: ${state.filters.priority}`, () => {
                state.filters.priority = 'all';
                filterPriority.value = 'all';
                fetchTasksAndRender();
            });
        }

        // Status Filter tags
        if (state.filters.status !== 'all') {
            hasActiveFilters = true;
            createTagElement(`Status: ${state.filters.status}`, () => {
                state.filters.status = 'all';
                filterStatus.value = 'all';
                fetchTasksAndRender();
            });
        }

        // Search tag
        if (state.filters.search) {
            hasActiveFilters = true;
            createTagElement(`Search: "${state.filters.search}"`, () => {
                state.filters.search = '';
                searchInput.value = '';
                clearSearchBtn.style.display = 'none';
                fetchTasksAndRender();
            });
        }

        // Toggle tags panel display
        activeTagsContainer.style.display = hasActiveFilters ? 'flex' : 'none';
        btnClearFilters.style.display = hasActiveFilters ? 'block' : 'none';
    }

    function createTagElement(label, onRemoveCallback) {
        const tag = document.createElement('div');
        tag.className = 'filter-tag';
        tag.innerHTML = `
            <span>${escapeHTML(label)}</span>
            <button aria-label="Remove filter">&times;</button>
        `;
        tag.querySelector('button').addEventListener('click', onRemoveCallback);
        tagsList.appendChild(tag);
    }

    /* ==========================================================================
       UTILITY FUNCTIONS
       ========================================================================== */

    // Basic HTML escaping helper to prevent XSS issues
    function escapeHTML(str) {
        if (!str) return '';
        return str.replace(/[&<>'"]/g, 
            tag => ({
                '&': '&amp;',
                '<': '&lt;',
                '>': '&gt;',
                "'": '&#39;',
                '"': '&quot;'
            }[tag] || tag)
        );
    }

    // Kickstart Adishi's dayplan UI
    init();
});
