// noVNC variables
let rfb = null;

// Initialize VNC connection
function initVNC(vncPort) {
    // Use noVNC to connect to VNC server
    const status = document.getElementById('connectionStatus');
    
    // Connect to localhost:vncPort
    const vncServer = `localhost:${vncPort}`;
    
    try {
        rfb = new RFB(
            document.getElementById('vnc'),
            `wss://${window.location.hostname}:${vncPort}`,
            {}
        );

        rfb.addEventListener("connect", onVNCConnect);
        rfb.addEventListener("disconnect", onVNCDisconnect);
        rfb.addEventListener("error", onVNCError);

    } catch (error) {
        console.error('Error initializing VNC:', error);
        status.innerHTML = `<i class="bi bi-exclamation-circle"></i> Connection Error`;
    }
}

function onVNCConnect(event) {
    const status = document.getElementById('connectionStatus');
    status.classList.add('connected');
    status.style.display = 'none';
    console.log('Connected to VNC server');
}

function onVNCDisconnect(event) {
    const status = document.getElementById('connectionStatus');
    status.classList.remove('connected');
    status.style.display = 'flex';
    status.innerHTML = '<i class="bi bi-x-circle"></i> Disconnected';
    console.log('Disconnected from VNC server');
}

function onVNCError(error) {
    const status = document.getElementById('connectionStatus');
    status.innerHTML = '<i class="bi bi-exclamation-circle"></i> Connection Error';
    console.error('VNC Error:', error);
}

// Refresh workspace status
async function refreshWorkspaceStatus() {
    try {
        const response = await fetch(`/api/workspace/${encodeURIComponent(workspaceName)}`);
        const data = await response.json();
        const workspace = data.workspace;

        const badge = document.getElementById('statusBadge');
        badge.textContent = workspace.current_status;
        badge.className = `status-badge ${workspace.current_status}`;
    } catch (error) {
        console.error('Error refreshing status:', error);
    }
}

// Load container logs
async function loadLogs() {
    const container = document.getElementById('logsContainer');
    const content = document.getElementById('logsContent');

    if (container.style.display === 'none') {
        try {
            const response = await fetch(`/api/workspace/${encodeURIComponent(workspaceName)}/logs`);
            const data = await response.json();
            content.textContent = data.logs || 'No logs available';
            container.style.display = 'block';
        } catch (error) {
            console.error('Error loading logs:', error);
            content.textContent = 'Error loading logs';
            container.style.display = 'block';
        }
    } else {
        container.style.display = 'none';
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
            window.location.href = '/';
        } else {
            alert('Error: ' + (data.error || 'Failed to delete workspace'));
        }
    } catch (error) {
        console.error('Error deleting workspace:', error);
        alert('Error deleting workspace');
    }
}

// Refresh status periodically
setInterval(refreshWorkspaceStatus, 5000);
