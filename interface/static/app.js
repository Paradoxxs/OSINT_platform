// Tab management
function switchTab(tabName) {
    // Hide all tabs
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });

    // Show selected tab
    document.getElementById(tabName + '-tab').classList.add('active');
    event.target.closest('.tab-btn').classList.add('active');

    // Load content
    if (tabName === 'active') {
        loadWorkspaces();
    } else {
        loadServices();
    }
}

// Load workspaces
async function loadWorkspaces() {
    try {
        const response = await fetch('/api/workspaces');
        const data = await response.json();
        
        const grid = document.getElementById('workspaces-grid');
        grid.innerHTML = '';

        if (data.workspaces.length === 0) {
            grid.innerHTML = '<p class="text-muted" style="grid-column: 1/-1;">No active workspaces. Create one from the "Available Services" tab.</p>';
            return;
        }

        data.workspaces.forEach(ws => {
            const card = createWorkspaceCard(ws);
            grid.appendChild(card);
        });
    } catch (error) {
        console.error('Error loading workspaces:', error);
    }
}

// Create workspace card
function createWorkspaceCard(workspace) {
    const card = document.createElement('div');
    card.className = 'card workspace-card';
    
    const statusClass = workspace.current_status === 'running' ? 'running' : 'stopped';
    
    card.innerHTML = `
        <div class="workspace-card-header">
            <div class="workspace-card-title">${escapeHtml(workspace.name)}</div>
            <span class="status-badge ${statusClass}">${workspace.current_status}</span>
        </div>
        <div class="workspace-card-meta">
            <div class="workspace-card-meta-item">
                <span>Service:</span>
                <span>${escapeHtml(workspace.service)}</span>
            </div>
            <div class="workspace-card-meta-item">
                <span>Created:</span>
                <span>${new Date(workspace.created).toLocaleDateString()}</span>
            </div>
            <div class="workspace-card-meta-item">
                <span>Last Accessed:</span>
                <span>${new Date(workspace.last_accessed).toLocaleDateString()}</span>
            </div>
            ${workspace.web_port ? `
            <div class="workspace-card-meta-item">
                <span>Web Port:</span>
                <span><code>${workspace.web_port}</code></span>
            </div>
            ` : ''}
        </div>
        <div class="workspace-card-actions">
            ${workspace.current_status === 'running' ? `
                <a href="http://localhost:${workspace.web_port}" target="_blank" class="btn btn-primary btn-sm" style="flex: 1;">
                    <i class="bi bi-box-arrow-up-right"></i>
                    Connect
                </a>
            ` : `
                <button class="btn btn-secondary btn-sm" style="flex: 1;" disabled>
                    <i class="bi bi-lock"></i>
                    Stopped
                </button>
            `}
            <button class="btn btn-secondary btn-sm" onclick="showWorkspaceDetails('${workspace.name}')">
                <i class="bi bi-info-circle"></i>
            </button>
            <button class="btn btn-danger btn-sm" onclick="deleteWorkspace('${workspace.name}')">
                <i class="bi bi-trash"></i>
            </button>
        </div>
    `;
    
    return card;
}

// Load services
async function loadServices() {
    try {
        const response = await fetch('/api/services');
        const data = await response.json();
        
        const grid = document.getElementById('services-grid');
        grid.innerHTML = '';

        data.services.forEach(service => {
            const card = createServiceCard(service);
            grid.appendChild(card);
        });
    } catch (error) {
        console.error('Error loading services:', error);
    }
}

// Create service card
function createServiceCard(service) {
    const card = document.createElement('div');
    card.className = 'card service-card';
    
    card.innerHTML = `
        <div class="service-icon">${service.icon || '🐳'}</div>
        <div class="service-name">${escapeHtml(service.name)}</div>
        <div class="service-image">${escapeHtml(service.image)}</div>
        <button class="btn btn-primary" onclick="openNewWorkspaceModal('${service.name}')">
            <i class="bi bi-plus-circle"></i>
            Launch
        </button>
    `;
    
    return card;
}

// Modal functions
function openNewWorkspaceModal(serviceName = null) {
    const modal = document.getElementById('newWorkspaceModal');
    const serviceSelect = document.getElementById('serviceSelect');
    const workspaceName = document.getElementById('workspaceName');
    
    // Load services into dropdown
    fetch('/api/services')
        .then(res => res.json())
        .then(data => {
            serviceSelect.innerHTML = '<option value="">Choose a service...</option>';
            data.services.forEach(service => {
                const option = document.createElement('option');
                option.value = service.name;
                option.textContent = service.name;
                if (serviceName && service.name === serviceName) {
                    option.selected = true;
                }
                serviceSelect.appendChild(option);
            });
        });
    
    workspaceName.value = '';
    modal.classList.add('active');
}

function closeNewWorkspaceModal() {
    document.getElementById('newWorkspaceModal').classList.remove('active');
}

function closeDetailsModal() {
    document.getElementById('workspaceDetailsModal').classList.remove('active');
}

// Create workspace
async function createWorkspace() {
    const serviceSelect = document.getElementById('serviceSelect');
    const workspaceName = document.getElementById('workspaceName');
    
    const service = serviceSelect.value;
    const name = workspaceName.value || undefined;

    if (!service) {
        alert('Please select a service');
        return;
    }

    // Validate custom name if provided
    if (name && !/^[a-zA-Z0-9_-]+$/.test(name)) {
        alert('Workspace name can only contain letters, numbers, dashes, and underscores');
        return;
    }

    try {
        const btn = document.querySelector('button[onclick="createWorkspace()"]');
        if (btn) {
            btn.disabled = true;
            btn.innerHTML = '<i class="bi bi-hourglass-split"></i> Creating...';
        }

        const response = await fetch('/api/workspace/create', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                service: service,
                name: name
            })
        });

        const data = await response.json();

        if (response.ok) {
            closeNewWorkspaceModal();
            showNotification(data.message, 'success');
            await new Promise(resolve => setTimeout(resolve, 2000)); // Wait 2 seconds for container to stabilize
            loadWorkspaces();
            // Switch to active tab
            document.querySelector('[onclick="switchTab(\'active\')"]').click();
        } else {
            showNotification(data.error || 'Failed to create workspace', 'error');
            console.error('Error response:', data);
        }
    } catch (error) {
        console.error('Error creating workspace:', error);
        showNotification(`Network error: ${error.message}`, 'error');
    } finally {
        const btn = document.querySelector('button[onclick="createWorkspace()"]');
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = '<i class="bi bi-plus-circle"></i> Create Workspace';
        }
    }
}

// Delete workspace
async function deleteWorkspace(workspaceName) {
    if (!confirm(`Delete workspace "${workspaceName}"? This action cannot be undone.`)) {
        return;
    }

    try {
        const response = await fetch(`/api/workspace/${encodeURIComponent(workspaceName)}/delete`, {
            method: 'POST'
        });

        const data = await response.json();

        if (response.ok) {
            showNotification(data.message, 'success');
            loadWorkspaces();
        } else {
            showNotification(data.error || 'Failed to delete workspace', 'error');
        }
    } catch (error) {
        console.error('Error deleting workspace:', error);
        showNotification('Error deleting workspace', 'error');
    }
}

// Show workspace details
async function showWorkspaceDetails(workspaceName) {
    try {
        const response = await fetch(`/api/workspace/${encodeURIComponent(workspaceName)}`);
        const data = await response.json();
        const workspace = data.workspace;

        const modal = document.getElementById('workspaceDetailsModal');
        document.getElementById('detailsTitle').textContent = workspace.name;
        
        const content = document.getElementById('detailsContent');
        content.innerHTML = `
            <div class="form-group">
                <label>Workspace Name</label>
                <input type="text" class="form-control" value="${escapeHtml(workspace.name)}" readonly>
            </div>
            <div class="form-group">
                <label>Service</label>
                <input type="text" class="form-control" value="${escapeHtml(workspace.service)}" readonly>
            </div>
            <div class="form-group">
                <label>Status</label>
                <input type="text" class="form-control" value="${workspace.current_status}" readonly>
            </div>
            <div class="form-group">
                <label>Created</label>
                <input type="text" class="form-control" value="${new Date(workspace.created).toLocaleString()}" readonly>
            </div>
            <div class="form-group">
                <label>Web Interface Port</label>
                <input type="text" class="form-control" value="${workspace.web_port}" readonly>
            </div>
            <div class="form-group">
                <label>Access URL</label>
                <input type="text" class="form-control" value="${workspace.web_url}" readonly>
            </div>
            ${workspace.web_url ? `
            <div class="form-group">
                <a href="${workspace.web_url}" target="_blank" class="btn btn-primary" style="width: 100%; text-align: center;">
                    <i class="bi bi-box-arrow-up-right"></i>
                    Open Web Interface
                </a>
            </div>
            ` : ''}
        `;
        
        modal.classList.add('active');
    } catch (error) {
        console.error('Error loading workspace details:', error);
        showNotification('Error loading details', 'error');
    }
}

// Refresh workspaces
function refreshWorkspaces() {
    loadWorkspaces();
    showNotification('Workspaces refreshed', 'success');
}

// Notification system
function showNotification(message, type = 'info', duration = 5000) {
    // Create a simple notification (you could enhance this)
    const notification = document.createElement('div');
    const maxWidth = Math.min(400, window.innerWidth - 40);
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 1rem 1.5rem;
        background: ${type === 'success' ? '#10b981' : type === 'error' ? '#ef4444' : '#6366f1'};
        color: white;
        border-radius: 0.375rem;
        z-index: 2000;
        animation: slideIn 0.3s ease;
        max-width: ${maxWidth}px;
        word-wrap: break-word;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
        font-size: 0.9rem;
        line-height: 1.4;
    `;
    notification.textContent = message;
    document.body.appendChild(notification);

    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, duration);
}

// Utility: Escape HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Load initial data
document.addEventListener('DOMContentLoaded', () => {
    loadWorkspaces();
});
