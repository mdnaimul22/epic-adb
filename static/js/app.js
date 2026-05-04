/**
 * adb-turbo EPIC — Frontend Application
 * Based on working backup, adapted for Epic Bento UI
 */

// ============================================
// Global State
// ============================================
const state = {
    selectedDevice: null,
    deviceInfo: null,
    categories: [],
    adbAvailable: false,
    refreshInterval: null,
    autoRefreshEnabled: true
};
window.appState = state; // Expose globally for Alpine.js components

const API_BASE = window.location.origin;

// ============================================
// API Helper
// ============================================
async function apiRequest(endpoint, options = {}) {
    try {
        const response = await fetch(`${API_BASE}${endpoint}`, {
            headers: { 'Content-Type': 'application/json', ...options.headers },
            ...options
        });
        const result = await response.json();
        if (!response.ok || !result.success) {
            throw new Error(result.error || 'Request failed');
        }
        return result.data || result;
    } catch (error) {
        console.error('API request failed:', error);
        throw error;
    }
}

// ============================================
// Notification System — sub-bar right slide
// ============================================
let _notifTimer = null;
let _notifTimer2 = null;

function notify(message, type = 'info', duration = 5000) {
    const bar = document.getElementById('notif-bar');
    const icon = document.getElementById('notif-icon');
    const text = document.getElementById('notif-text');
    if (!bar) return;

    const icons = { success: '✓', error: '✗', warning: '⚠', info: 'ℹ' };

    // Strip any leading icon/symbol chars from the message to prevent duplication
    // e.g. "✓ Animation enabled" → "Animation enabled"
    const cleanMsg = message.replace(/^[✓✗⚠ℹ·\-–—]\s*/, '').trimStart();

    // Clear any pending timers
    if (_notifTimer) { clearTimeout(_notifTimer); _notifTimer = null; }
    if (_notifTimer2) { clearTimeout(_notifTimer2); _notifTimer2 = null; }

    // Reset to off-screen-right state instantly (no transition)
    bar.style.transition = 'none';
    bar.className = 'notif-bar';
    void bar.offsetWidth; // force reflow

    // Set content & type
    icon.textContent = icons[type] || 'ℹ';
    text.textContent = cleanMsg;
    bar.classList.add(`notif--${type}`);

    // Restore transition then slide in
    bar.style.transition = '';
    bar.classList.add('notif--visible');

    // Auto-hide after duration
    _notifTimer = setTimeout(() => {
        bar.classList.remove('notif--visible');
        bar.classList.add('notif--exit');
        _notifTimer2 = setTimeout(() => { bar.className = 'notif-bar'; }, 450);
    }, duration);
}

// Alias — keeps all existing logToConsole() calls working
function logToConsole(message, type = 'info') {
    // Skip noisy internal messages
    const silent = ['Reading current toggle states', 'Auto-refresh', 'Collapsed all', 'Expanded all'];
    if (silent.some(s => message.startsWith(s))) return;
    notify(message, type);
}



// ============================================
// Status Pill Helper
// ============================================
function setStatusPill(text, type = 'info') {
    const textEl = document.getElementById('device-status-text');
    const dot = document.getElementById('status-dot');
    if (textEl) textEl.textContent = text;
    if (dot) {
        const colors = { success: '#34d399', error: '#f87171', warning: '#fbbf24', info: '#60a5fa' };
        dot.style.background = colors[type] || colors.info;
        dot.style.animation = type === 'success' ? 'none' : '';
    }
}

// ============================================
// ADB Check
// ============================================
async function checkADB() {
    try {
        const result = await apiRequest('/api/check-adb');
        if (result.available) {
            state.adbAvailable = true;
            setStatusPill('ADB Ready', 'success');
            logToConsole('ADB is available and ready', 'success');
            await checkDevices();
        } else {
            state.adbAvailable = false;
            setStatusPill('ADB Not Found', 'error');
            logToConsole('ADB not found. Please install ADB.', 'error');
        }
    } catch (error) {
        setStatusPill('ADB Error', 'error');
        logToConsole(`Error checking ADB: ${error.message}`, 'error');
    }
}

// ============================================
// Device Check
// ============================================
async function checkDevices() {
    try {
        const result = await apiRequest('/api/devices');
        const devices = result.devices || [];
        const count = document.getElementById('connected-devices');
        if (count) count.textContent = devices.length;

        if (devices.length > 0) {
            setStatusPill(`✅ ${devices.length} device(s) connected`, 'success');
            logToConsole(`Found ${devices.length} connected device(s)`, 'success');
        } else {
            setStatusPill('No Devices Found', 'warning');
            logToConsole('No devices connected. Please connect a device.', 'warning');
        }
    } catch (error) {
        setStatusPill('Device Error', 'error');
        logToConsole(`Error checking devices: ${error.message}`, 'error');
    }
}

// ============================================
// Device Management
// ============================================
async function refreshDevices() {
    logToConsole('Refreshing device list...', 'info');
    try {
        const result = await apiRequest('/api/devices');
        const devices = result.devices || [];

        const select = document.getElementById('device-select');
        select.innerHTML = '<option value="">Select a device...</option>';

        devices.forEach(device => {
            const option = document.createElement('option');
            option.value = device.id;
            option.textContent = `${device.model} (${device.id})`;
            select.appendChild(option);
        });

        select.disabled = devices.length === 0;
        const count = document.getElementById('connected-devices');
        if (count) count.textContent = devices.length;

        logToConsole(`Found ${devices.length} device(s)`, 'success');

        await checkDevices();

        // Auto-select: try last device, then first available
        const lastDevice = localStorage.getItem('lastSelectedDevice');
        if (lastDevice && devices.some(d => d.id === lastDevice)) {
            select.value = lastDevice;
            await onDeviceSelected();
        } else if (devices.length === 1) {
            select.value = devices[0].id;
            await onDeviceSelected();
        }

    } catch (error) {
        logToConsole(`Error refreshing devices: ${error.message}`, 'error');
    }
}

async function onDeviceSelected() {
    const select = document.getElementById('device-select');
    const deviceId = select.value;

    if (!deviceId) {
        state.selectedDevice = null;
        state.deviceInfo = null;
        document.getElementById('device-info').style.display = 'none';
        document.getElementById('device-details-card').style.display = 'none';
        stopAutoRefresh();

        // Notify Alpine components
        window.dispatchEvent(new CustomEvent('device-selected', { detail: null }));
        window.dispatchEvent(new CustomEvent('device-info-loaded', { detail: { deviceId: null, info: null } }));
        return;
    }

    state.selectedDevice = deviceId;
    localStorage.setItem('lastSelectedDevice', deviceId);

    await loadDeviceInfo(deviceId);

    // Display handled by Alpine x-show
    startAutoRefresh();

    // Notify Alpine components that a device has been selected
    window.dispatchEvent(new CustomEvent('device-selected', { detail: deviceId }));
}

async function loadDeviceInfo(deviceId, silent = false) {
    try {
        const result = await apiRequest(`/api/device-info/${deviceId}`);
        state.deviceInfo = result;
        window.dispatchEvent(new CustomEvent('device-info-loaded', { detail: { deviceId, info: result } }));

        // Update info bar
        const modelEl = document.getElementById('device-model');
        const mfgEl = document.getElementById('device-manufacturer');
        const androidEl = document.getElementById('device-android');
        const locationEl = document.getElementById('device-location');

        if (modelEl) modelEl.textContent = result.model || '—';
        if (mfgEl) mfgEl.textContent = result.manufacturer || '—';
        if (androidEl) androidEl.textContent = `Android ${result.android_version || '—'} (SDK ${result.sdk_version || '—'})`;

        if (locationEl) {
            if (result.location && result.location.available) {
                const lat = result.location.latitude.toFixed(6);
                const lon = result.location.longitude.toFixed(6);
                locationEl.innerHTML = `<a href="https://www.google.com/maps?q=${lat},${lon}" target="_blank" rel="noopener">${lat}, ${lon} 🗺️</a>`;
            } else {
                locationEl.textContent = '';
            }
        }

        document.getElementById('device-info').style.display = 'flex';

        if (result.details) {
            document.getElementById('device-details-card').style.display = 'block';
        }

    } catch (error) {
        logToConsole(`Error loading device info: ${error.message}`, 'error');
    }
}



// ============================================
// Auto-Refresh
// ============================================
function startAutoRefresh() {
    stopAutoRefresh();
    if (state.autoRefreshEnabled && state.selectedDevice) {
        state.refreshInterval = setInterval(async () => {
            if (state.selectedDevice) await refreshDeviceDetails();
        }, 60000);
        logToConsole('Auto-refresh enabled (every 60s)', 'info');
    }
}

function stopAutoRefresh() {
    if (state.refreshInterval) {
        clearInterval(state.refreshInterval);
        state.refreshInterval = null;
    }
}

async function refreshDeviceDetails() {
    if (!state.selectedDevice) return;
    try {
        const result = await apiRequest(`/api/device-info/${state.selectedDevice}`);
        // Notify Alpine systemStatus component with fresh data
        window.dispatchEvent(new CustomEvent('device-info-loaded', { detail: { deviceId: state.selectedDevice, info: result } }));

        const locationEl = document.getElementById('device-location');
        if (locationEl && result.location && result.location.available) {
            const lat = result.location.latitude.toFixed(6);
            const lon = result.location.longitude.toFixed(6);
            locationEl.innerHTML = `<a href="https://www.google.com/maps?q=${lat},${lon}" target="_blank" rel="noopener">${lat}, ${lon} 🗺️</a>`;
        }
    } catch (error) {
        console.debug('Auto-refresh failed:', error);
    }
}

function toggleAutoRefresh() {
    state.autoRefreshEnabled = !state.autoRefreshEnabled;
    const indicator = document.getElementById('refresh-indicator');
    const icon = document.getElementById('auto-refresh-icon');
    if (state.autoRefreshEnabled) {
        if (indicator) indicator.classList.remove('paused');
        if (icon) icon.textContent = '⏸';
        startAutoRefresh();
        logToConsole('Auto-refresh enabled', 'info');
    } else {
        if (indicator) indicator.classList.add('paused');
        if (icon) icon.textContent = '▶';
        stopAutoRefresh();
        logToConsole('Auto-refresh paused', 'info');
    }
    localStorage.setItem('autoRefreshEnabled', state.autoRefreshEnabled);
}

// ============================================
// Theme System
// ============================================
const THEMES = [
    {
        name: 'Matrix',
        icon: '💻',
        vars: {
            '--c-bg': '#050d0a', '--c-surface': '#071510', '--c-surface2': '#0a1c15', '--c-surface3': '#0f2a1e',
            '--c-border': 'rgba(0,255,136,0.15)', '--c-border2': 'rgba(0,255,136,0.28)',
            '--c-primary': '#00ff88', '--c-primary-d': '#00cc6a', '--c-secondary': '#4ecdc4', '--c-accent': '#7fff00',
            '--c-text': '#00ff88', '--c-muted': '#7fffd4', '--c-dim': '#2a8c5e',
            '--glow': '0 0 16px rgba(0,255,136,0.25)'
        }
    },
    {
        name: 'Indigo Night',
        icon: '🌌',
        vars: {
            '--c-bg': '#0a0f1e', '--c-surface': '#0f172a', '--c-surface2': '#1a2235', '--c-surface3': '#1e2d45',
            '--c-border': 'rgba(99,102,241,0.15)', '--c-border2': 'rgba(99,102,241,0.28)',
            '--c-primary': '#818cf8', '--c-primary-d': '#6366f1', '--c-secondary': '#c084fc', '--c-accent': '#22d3ee',
            '--c-text': '#e2e8f0', '--c-muted': '#94a3b8', '--c-dim': '#64748b',
            '--glow': '0 0 16px rgba(129,140,248,0.25)'
        }
    },
    {
        name: 'Midnight Purple',
        icon: '🔮',
        vars: {
            '--c-bg': '#0d0a1a', '--c-surface': '#14102a', '--c-surface2': '#1e1838', '--c-surface3': '#281f48',
            '--c-border': 'rgba(168,85,247,0.15)', '--c-border2': 'rgba(168,85,247,0.28)',
            '--c-primary': '#a855f7', '--c-primary-d': '#9333ea', '--c-secondary': '#e879f9', '--c-accent': '#f472b6',
            '--c-text': '#f0e7ff', '--c-muted': '#b8a4d6', '--c-dim': '#7c6a9b',
            '--glow': '0 0 16px rgba(168,85,247,0.25)'
        }
    },
    {
        name: 'Ocean Depth',
        icon: '🌊',
        vars: {
            '--c-bg': '#071520', '--c-surface': '#0c1e30', '--c-surface2': '#132d45', '--c-surface3': '#193a58',
            '--c-border': 'rgba(14,165,233,0.15)', '--c-border2': 'rgba(14,165,233,0.28)',
            '--c-primary': '#38bdf8', '--c-primary-d': '#0ea5e9', '--c-secondary': '#67e8f9', '--c-accent': '#2dd4bf',
            '--c-text': '#e0f2fe', '--c-muted': '#7dd3fc', '--c-dim': '#3a7ca5',
            '--glow': '0 0 16px rgba(56,189,248,0.25)'
        }
    },
    {
        name: 'Clear Ice',
        icon: '🧊',
        vars: {
            '--c-bg': '#c8d8ea', '--c-surface': '#d8e8f4', '--c-surface2': '#e4f0fb', '--c-surface3': '#ccdde9',
            '--c-border': 'rgba(60,110,170,0.25)', '--c-border2': 'rgba(60,110,170,0.45)',
            '--c-primary': '#1d4ed8', '--c-primary-d': '#1e40af', '--c-secondary': '#0369a1', '--c-accent': '#0284c7',
            '--c-text': '#0f172a', '--c-muted': '#334155', '--c-dim': '#64748b',
            '--c-success': '#15803d', '--c-warning': '#b45309', '--c-danger': '#b91c1c', '--c-info': '#0369a1',
            '--glow': '0 0 16px rgba(29,78,216,0.18)'
        }
    }
];
let currentTheme = 0;

function applyTheme(index) {
    const theme = THEMES[index];
    const root = document.documentElement;
    for (const [k, v] of Object.entries(theme.vars)) root.style.setProperty(k, v);
    const btn = document.getElementById('themeBtn');
    if (btn) {
        btn.textContent = theme.icon;
        btn.title = `Theme: ${theme.name}`;
    }
    localStorage.setItem('epic-adb-theme', index);
}

// Wire theme button
document.addEventListener('DOMContentLoaded', () => {
    const btn = document.getElementById('themeBtn');
    if (btn) {
        btn.addEventListener('click', () => {
            currentTheme = (currentTheme + 1) % THEMES.length;
            applyTheme(currentTheme);
            logToConsole(`Theme: ${THEMES[currentTheme].name}`, 'info');
        });
    }
});

// Apply saved theme immediately (default = 0 = Matrix)
(function() {
    const saved = parseInt(localStorage.getItem('epic-adb-theme') || '0', 10);
    currentTheme = saved < THEMES.length ? saved : 0;
    applyTheme(currentTheme);
})();

// ============================================
// Initialization
// ============================================
async function init() {
    logToConsole('Initializing adb-turbo EPIC...', 'info');

    const savedAutoRefresh = localStorage.getItem('autoRefreshEnabled');
    if (savedAutoRefresh !== null) state.autoRefreshEnabled = savedAutoRefresh === 'true';

    const indicator = document.getElementById('refresh-indicator');
    const icon = document.getElementById('auto-refresh-icon');
    if (!state.autoRefreshEnabled) {
        if (indicator) indicator.classList.add('paused');
        if (icon) icon.textContent = '▶';
    }

    await checkADB();
    await refreshDevices();

    const select = document.getElementById('device-select');
    if (select) select.addEventListener('change', onDeviceSelected);

    logToConsole('Application ready! ⚡', 'success');
}

// Start
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}
