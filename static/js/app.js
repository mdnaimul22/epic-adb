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
    collapsedSections: new Set(),
    refreshInterval: null,
    autoRefreshEnabled: true
};

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
let _notifTimer  = null;
let _notifTimer2 = null;

function notify(message, type = 'info', duration = 5000) {
    const bar  = document.getElementById('notif-bar');
    const icon = document.getElementById('notif-icon');
    const text = document.getElementById('notif-text');
    if (!bar) return;

    const icons = { success: '✓', error: '✗', warning: '⚠', info: 'ℹ' };

    // Strip any leading icon/symbol chars from the message to prevent duplication
    // e.g. "✓ Animation enabled" → "Animation enabled"
    const cleanMsg = message.replace(/^[✓✗⚠ℹ·\-–—]\s*/, '').trimStart();

    // Clear any pending timers
    if (_notifTimer)  { clearTimeout(_notifTimer);  _notifTimer  = null; }
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

function clearConsole() { /* no-op — console removed */ }

// ============================================
// Section Collapse
// ============================================
function toggleSection(sectionId) {
    const section = document.getElementById(sectionId);
    if (!section) return;
    const content = section.querySelector('.card__content');
    if (!content) return;

    if (content.classList.contains('collapsed')) {
        content.classList.remove('collapsed');
        section.classList.remove('collapsed');
        state.collapsedSections.delete(sectionId);
    } else {
        content.classList.add('collapsed');
        section.classList.add('collapsed');
        state.collapsedSections.add(sectionId);
    }
    localStorage.setItem('collapsedSections', JSON.stringify([...state.collapsedSections]));
}

function loadCollapsedSections() {
    const saved = localStorage.getItem('collapsedSections');
    if (!saved) return;
    try {
        JSON.parse(saved).forEach(sectionId => {
            state.collapsedSections.add(sectionId);
            const section = document.getElementById(sectionId);
            if (section) {
                const content = section.querySelector('.card__content');
                if (content) {
                    content.classList.add('collapsed');
                    section.classList.add('collapsed');
                }
            }
        });
    } catch (e) {
        console.error('Failed to load collapsed sections:', e);
    }
}

// ============================================
// Status Pill Helper
// ============================================
function setStatusPill(text, type = 'info') {
    const textEl = document.getElementById('device-status-text');
    const dot    = document.getElementById('status-dot');
    if (textEl) textEl.textContent = text;
    if (dot) {
        const colors = { success:'#34d399', error:'#f87171', warning:'#fbbf24', info:'#60a5fa' };
        dot.style.background = colors[type] || colors.info;
        dot.style.animation  = type === 'success' ? 'none' : '';
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
        document.getElementById('dns-card').style.display = 'none';
        updateProfilesUIState(false);
        stopAutoRefresh();
        return;
    }

    state.selectedDevice = deviceId;
    localStorage.setItem('lastSelectedDevice', deviceId);

    await loadDeviceInfo(deviceId);

    document.getElementById('profiles-card').style.display = 'block';
    document.getElementById('dns-card').style.display = 'block';
    updateProfilesUIState(true);
    await loadBackupsList();
    startAutoRefresh();

    // Auto DNS speed test — runs in background, non-blocking
    runDnsTest();
}

async function loadDeviceInfo(deviceId, silent = false) {
    try {
        const result = await apiRequest(`/api/device-info/${deviceId}`);
        state.deviceInfo = result;

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
            displayDeviceDetails(result.details);
            document.getElementById('device-details-card').style.display = 'block';
        }

        filterCommandsByDevice(result.is_samsung);
        await loadCommandStates(deviceId, silent);

    } catch (error) {
        logToConsole(`Error loading device info: ${error.message}`, 'error');
    }
}

async function loadCommandStates(deviceId, silent = false) {
    try {
        if (!silent) logToConsole('Reading current toggle states from device...', 'info');
        const result = await apiRequest(`/api/command-states/${deviceId}`);

        if (result && result.states) {
            let updatedCount = 0;
            Object.entries(result.states).forEach(([commandName, isEnabled]) => {
                document.querySelectorAll('.toggle-switch').forEach(toggle => {
                    const command = JSON.parse(toggle.dataset.command);
                    if (command.name === commandName && isEnabled !== null) {
                        isEnabled ? toggle.classList.add('active') : toggle.classList.remove('active');
                        updatedCount++;
                    }
                });
            });
            if (!silent) logToConsole(`✓ Loaded ${updatedCount} toggle states from device`, 'success');
        }
    } catch (error) {
        if (!silent) logToConsole(`Error loading command states: ${error.message}`, 'error');
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
        }, 8000);
        logToConsole('Auto-refresh enabled (every 8s)', 'info');
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
        const locationEl = document.getElementById('device-location');
        if (locationEl && result.location && result.location.available) {
            const lat = result.location.latitude.toFixed(6);
            const lon = result.location.longitude.toFixed(6);
            locationEl.innerHTML = `<a href="https://www.google.com/maps?q=${lat},${lon}" target="_blank" rel="noopener">${lat}, ${lon} 🗺️</a>`;
        }
        if (result.details) displayDeviceDetails(result.details);
        await loadCommandStates(state.selectedDevice, true);
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
// ── Registry: icon-compact rows ──────────────
function displayDeviceDetails(details) {
    const grid = document.getElementById('device-details-grid');
    if (!grid) return;
    grid.innerHTML = '';

    // Per-key configuration: icon, label, color function
    const groups = [
        { title: '🔋', label: 'Battery', data: details.battery, keys: [
            { key:'level',       label:'Level', suffix:'%', ico:'🔋',
              color: v => +v < 20 ? 'danger' : +v < 50 ? 'warn' : 'good',
              bar: true },
            { key:'temperature', label:'Temp',   ico:'🌡️' },
            { key:'health',      label:'Health', ico:'💚' },
            { key:'status',      label:'Status', ico:'⚡' }
        ]},
        { title: '📡', label: 'Network', data: details.network, keys: [
            { key:'ip_address', label:'IP', ico:'🌐', valColor:'accent' }
        ]},
        { title: '🖥️', label: 'Display', data: details.display, keys: [
            { key:'resolution', label:'Res', ico:'📐', valColor:'info' },
            { key:'density',    label:'DPI', ico:'🔢', valColor:'info' }
        ]},
        { title: '💾', label: 'Memory', data: details.memory, keys: [
            { key:'total',     label:'Total', ico:'💾' },
            { key:'available', label:'Free',  ico:'🟢',
              color: v => parseInt(v) < 512 ? 'warn' : 'good' }
        ]},
        { title: '⚙️', label: 'CPU', data: details.cpu, keys: [
            { key:'cores',    label:'Cores', ico:'⚙️', valColor:'info' },
            { key:'hardware', label:'HW',    ico:'🔩' }
        ]},
        { title: '💿', label: 'Storage', data: details.storage, keys: [
            { key:'total',     label:'Total', ico:'💿' },
            { key:'used',      label:'Used',  ico:'📊' },
            { key:'available', label:'Free',  ico:'🟢' }
        ]}
    ];

    if (details.uptime)      groups.push({ title:'⏱️', label:'System', data:{ uptime: details.uptime },    keys:[{ key:'uptime', label:'Up', ico:'⏱️' }] });
    if (details.current_app) groups.push({ title:'📱', label:'Active',  data:{ app: details.current_app }, keys:[{ key:'app',    label:'App', ico:'📱', valColor:'accent' }] });

    const battLevel = details.battery?.level ? +details.battery.level : null;

    groups.forEach(group => {
        if (!group.data) return;
        const validItems = group.keys.filter(k => group.data[k.key]);
        if (!validItems.length) return;

        const groupEl = document.createElement('div');
        groupEl.className = 'reg-group';

        const titleEl = document.createElement('div');
        titleEl.className = 'reg-group__title';
        titleEl.innerHTML = `${group.title} <span style="opacity:.8">${group.label}</span>`;
        groupEl.appendChild(titleEl);

        const rowsEl = document.createElement('div');
        rowsEl.className = 'reg-rows';

        validItems.forEach(item => {
            const raw = group.data[item.key];
            const val = raw + (item.suffix || '');
            const colorClass = item.color
                ? `reg-row__val--${item.color(raw)}`
                : item.valColor ? `reg-row__val--${item.valColor}` : '';

            const row = document.createElement('div');
            row.className = 'reg-row';
            row.innerHTML = `
                <span class="reg-row__ico">${item.ico || ''}</span>
                <span class="reg-row__key">${item.label}</span>
                <span class="reg-row__val ${colorClass}">${val}</span>
            `;
            rowsEl.appendChild(row);

            // Battery mini progress bar (separate element after the row)
            if (item.bar && item.key === 'level' && battLevel !== null) {
                const pct = Math.min(100, Math.max(0, battLevel));
                const fillClass = pct < 20 ? 'reg-bar__fill--danger' : pct < 50 ? 'reg-bar__fill--warn' : '';
                const bar = document.createElement('div');
                bar.className = 'reg-bar';
                bar.innerHTML = `<div class="reg-bar__fill ${fillClass}" style="width:${pct}%"></div>`;
                rowsEl.appendChild(bar);
            }
        });

        groupEl.appendChild(rowsEl);
        grid.appendChild(groupEl);
    });
}

function filterCommandsByDevice(isSamsung) {
    document.querySelectorAll('.toggle-switch').forEach(t => t.classList.remove('disabled'));
    document.querySelectorAll('.command-item').forEach(c => {
        c.style.opacity = '1';
        c.style.pointerEvents = 'auto';
    });
    document.querySelectorAll('.command-item.samsung-only').forEach(cmd => {
        if (!isSamsung) {
            cmd.style.opacity = '0.5';
            cmd.style.pointerEvents = 'none';
            const toggle = cmd.querySelector('.toggle-switch');
            if (toggle) toggle.classList.add('disabled');
        }
    });
}

// ============================================
// Command Categories
// ============================================
async function loadCategories() {
    try {
        const result = await apiRequest('/api/categories');
        state.categories = result.categories || [];
        renderCategories();

        const totalCommands = state.categories.reduce((sum, cat) => sum + cat.commands.length, 0);
        const highImpact = state.categories.filter(cat => cat.impact === 'high').length;
        const totalEl = document.getElementById('total-commands');
        const hiEl = document.getElementById('high-impact');
        if (totalEl) totalEl.textContent = totalCommands;
        if (hiEl) hiEl.textContent = highImpact;

        logToConsole(`Loaded ${state.categories.length} command categories`, 'success');
    } catch (error) {
        logToConsole(`Error loading categories: ${error.message}`, 'error');
    }
}

function renderCategories() {
    const container = document.getElementById('categories-container');
    if (!container) return;
    container.innerHTML = '';
    state.categories.forEach((category, index) => {
        container.appendChild(createCategoryGroup(category, index));
    });
}

// Dense table-style category group
function createCategoryGroup(category, index) {
    const group = document.createElement('div');
    group.className = 'cat-group';
    group.id = `category-${category.id}`;

    // Sticky header row
    const hdr = document.createElement('div');
    hdr.className = 'cat-group__hdr';

    const arrow = document.createElement('span');
    arrow.className = 'cat-collapse-arrow open';
    arrow.textContent = '▲';

    hdr.innerHTML = `
        <span class="cat-icon">${getCategoryIcon(category.id)}</span>
        <span class="cat-name">${category.name}</span>
        <span class="cat-desc">${category.description}</span>
        <span class="impact-badge impact-badge--${category.impact}">${category.impact}</span>
    `;
    hdr.appendChild(arrow);

    // Rows container
    const rows = document.createElement('div');
    rows.className = 'cmd-rows';
    rows.id = `rows-${category.id}`;

    category.commands.forEach(command => {
        const { row, detail } = createCommandRow(command, category.id);
        rows.appendChild(row);
        rows.appendChild(detail);
    });

    hdr.onclick = () => {
        rows.classList.toggle('hidden');
        arrow.classList.toggle('open');
        arrow.textContent = rows.classList.contains('hidden') ? '▼' : '▲';
    };

    group.appendChild(hdr);
    group.appendChild(rows);
    return group;
}

function getCategoryIcon(categoryId) {
    const icons = {
        animation_settings: '⚡', background_processes: '🔄', fixed_performance: '🚀',
        ram_plus: '💾', refresh_rate: '🖥️', app_launch_speed: '⏱️',
        game_optimization_samsung: '🎮', audio_quality: '🔊', touchscreen_latency: '👆',
        system_optimization: '⚙️', private_dns: '🔒', network_performance: '📡', power_management: '🔋'
    };
    return icons[categoryId] || '📋';
}

// Dense table row (instead of card)
function createCommandRow(command, categoryId) {
    const rowId = `cmd-${categoryId}-${command.name.replace(/\s+/g, '-').toLowerCase()}`;

    const row = document.createElement('div');
    row.className = `cmd-row ${command.samsung_only ? 'samsung-only' : ''}`;
    row.id = rowId;
    row.dataset.name = command.name.toLowerCase();
    row.dataset.desc = (command.description || '').toLowerCase();

    const nameEl = document.createElement('span');
    nameEl.className = 'cmd-row__name';
    nameEl.innerHTML = command.name + (command.samsung_only ? ' <span class="samsung-badge">⚡ Samsung</span>' : '');

    const descEl = document.createElement('span');
    descEl.className = 'cmd-row__desc';
    descEl.textContent = command.description || '';

    const actions = document.createElement('div');
    actions.className = 'cmd-row__actions';

    const expandBtn = document.createElement('button');
    expandBtn.className = 'expand-btn';
    expandBtn.textContent = 'Details';
    expandBtn.onclick = () => {
        const d = document.getElementById(`${rowId}-detail`);
        if (d) d.classList.toggle('hidden');
    };

    const toggle = createToggleSwitch(command, categoryId);

    actions.appendChild(expandBtn);
    actions.appendChild(toggle);

    row.appendChild(nameEl);
    row.appendChild(descEl);
    row.appendChild(actions);

    // Detail expansion row
    const detail = document.createElement('div');
    detail.className = 'cmd-detail-row hidden';
    detail.id = `${rowId}-detail`;
    let detailHtml = `<div>${command.explanation}</div>`;
    if (command.disable_cmd) detailHtml += `<div class="cmd-code">disable: adb ${command.disable_cmd}</div>`;
    if (command.enable_cmd)  detailHtml += `<div class="cmd-code">enable:  adb ${command.enable_cmd}</div>`;
    detail.innerHTML = detailHtml;

    return { row, detail };
}

function toggleAllDetails() {
    const allDetails = document.querySelectorAll('.cmd-detail-row');
    const btn = document.getElementById('expand-collapse-text');
    if (!allDetails.length) return;
    const anyVisible = Array.from(allDetails).some(d => !d.classList.contains('hidden'));
    if (anyVisible) {
        allDetails.forEach(d => d.classList.add('hidden'));
        if (btn) btn.textContent = 'Expand All';
    } else {
        allDetails.forEach(d => d.classList.remove('hidden'));
        if (btn) btn.textContent = 'Collapse All';
    }
}

function filterCommands(query) {
    const q = query.toLowerCase().trim();
    document.querySelectorAll('.cmd-row').forEach(row => {
        const match = !q || row.dataset.name?.includes(q) || row.dataset.desc?.includes(q);
        row.classList.toggle('hidden-by-filter', !match);
        // also hide detail if parent hidden
        const detail = document.getElementById(`${row.id}-detail`);
        if (detail && !match) detail.classList.add('hidden');
    });
}

function createToggleSwitch(command, categoryId) {
    const toggle = document.createElement('div');
    toggle.className = state.selectedDevice ? 'toggle-switch' : 'toggle-switch disabled';
    toggle.dataset.command = JSON.stringify(command);
    toggle.dataset.categoryId = categoryId;
    toggle.onclick = () => handleToggle(toggle);

    const slider = document.createElement('div');
    slider.className = 'toggle-switch__slider';
    toggle.appendChild(slider);
    return toggle;
}

async function handleToggle(toggleElement) {
    if (!state.selectedDevice) {
        logToConsole('Please select a device first', 'warning');
        return;
    }
    if (toggleElement.classList.contains('disabled') || toggleElement.classList.contains('loading')) return;

    const command = JSON.parse(toggleElement.dataset.command);
    const isActive = toggleElement.classList.contains('active');
    const action = isActive ? 'disable' : 'enable';
    const cmd = isActive ? command.disable_cmd : command.enable_cmd;

    if (!cmd) {
        logToConsole(`No ${action} command available for ${command.name}`, 'warning');
        return;
    }

    toggleElement.classList.add('loading');

    try {
        // apiRequest() throws on any failure — reaching here means success
        await apiRequest('/api/execute', {
            method: 'POST',
            body: JSON.stringify({ device_id: state.selectedDevice, command: cmd, action })
        });

        toggleElement.classList.toggle('active');
        logToConsole(`${command.name}: ${action}d`, 'success');
    } catch (error) {
        logToConsole(`${command.name} failed: ${error.message}`, 'error');
    } finally {
        toggleElement.classList.remove('loading');
    }
}

// ============================================
// Profile Management
// ============================================
async function backupCurrentSettings() {
    if (!state.selectedDevice || !state.deviceInfo) {
        logToConsole('Please select a device first', 'warning');
        return;
    }
    logToConsole('Backing up device settings...', 'info');
    try {
        const result = await apiRequest('/api/profiles/backup', {
            method: 'POST',
            body: JSON.stringify({ device_id: state.selectedDevice, manufacturer: state.deviceInfo.manufacturer, model: state.deviceInfo.model })
        });
        logToConsole(`✓ Backup created: ${result.profile.settings ? Object.keys(result.profile.settings).length : 0} settings saved`, 'success');
        await loadBackupsList();
    } catch (error) {
        logToConsole(`✗ Backup failed: ${error.message}`, 'error');
    }
}

async function loadBackupsList() {
    if (!state.deviceInfo) return;
    try {
        const result = await apiRequest('/api/profiles/list', {
            method: 'POST',
            body: JSON.stringify({ manufacturer: state.deviceInfo.manufacturer, model: state.deviceInfo.model })
        });
        const backups = result.backups || [];
        const container  = document.getElementById('backups-container');
        const listPanel  = document.getElementById('backups-list');
        const countBadge = document.getElementById('backup-count');

        if (!backups.length) {
            if (listPanel) listPanel.style.display = 'none';
            if (countBadge) countBadge.textContent = '';
            return;
        }

        if (listPanel)  listPanel.style.display = 'block';
        if (countBadge) countBadge.textContent   = `${backups.length}`;
        if (container) {
            container.innerHTML = '';
            backups.forEach((backup, index) => container.appendChild(createBackupItem(backup, index)));
        }
    } catch (error) {
        console.error('Failed to load backups:', error);
    }
}

function toggleProfilesPanel() {
    const body  = document.getElementById('profiles-panel-body');
    const caret = document.getElementById('profiles-caret');
    if (!body) return;
    const hidden = body.style.display === 'none';
    body.style.display = hidden ? '' : 'none';
    if (caret) caret.classList.toggle('open', hidden);
}

function toggleBackupsPanel() {
    const body  = document.getElementById('backups-panel-body');
    const caret = document.getElementById('backups-caret');
    if (!body) return;
    const hidden = body.style.display === 'none';
    body.style.display = hidden ? '' : 'none';
    if (caret) caret.classList.toggle('open', hidden);
}

function createBackupItem(backup, index) {
    const item = document.createElement('div');
    item.className = 'backup-item';

    // Info column
    const infoDiv = document.createElement('div');
    infoDiv.className = 'backup-item__info';

    const date = new Date(backup.timestamp);
    const dateStr = date.toLocaleString('en-US', {
        month: 'short', day: 'numeric',
        hour: '2-digit', minute: '2-digit', hour12: false
    });
    const settingsCount = backup.settings ? Object.keys(backup.settings).length : 0;
    const typeLabel = backup.backup_type === 'automatic' ? 'auto' : (backup.backup_type || 'manual');
    const customName = backup.custom_name || `Backup ${index + 1}`;

    // Name row — with tiny inline edit
    const nameRow = document.createElement('div');
    nameRow.className = 'backup-item__name';
    nameRow.style.display = 'flex';
    nameRow.style.alignItems = 'center';
    nameRow.style.gap = '4px';

    const nameSpan = document.createElement('span');
    nameSpan.textContent = customName;
    nameSpan.style.cssText = 'max-width:90px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;';

    const editBtn = document.createElement('button');
    editBtn.textContent = '✏️';
    editBtn.title = 'Rename backup';
    editBtn.style.cssText = 'background:none;border:none;cursor:pointer;font-size:.6rem;padding:0;opacity:.5;line-height:1;flex-shrink:0;';
    editBtn.onclick = (e) => {
        e.stopPropagation();
        startRenameBackup(index, customName, nameSpan, editBtn);
    };

    nameRow.appendChild(nameSpan);
    nameRow.appendChild(editBtn);

    const metaDiv = document.createElement('div');
    metaDiv.className = 'backup-item__meta';
    metaDiv.textContent = `${dateStr} · ${settingsCount} · ${typeLabel}`;

    infoDiv.appendChild(nameRow);
    infoDiv.appendChild(metaDiv);

    // Actions column — all buttons identical base size
    const actions = document.createElement('div');
    actions.className = 'backup-item__actions';

    const btnBase = 'width:26px;height:22px;display:inline-flex;align-items:center;justify-content:center;border-radius:4px;border:1px solid;cursor:pointer;font-size:.72rem;padding:0;flex-shrink:0;transition:all .15s;';

    const restoreBtn = document.createElement('button');
    restoreBtn.style.cssText = btnBase + 'background:rgba(129,140,248,.15);border-color:rgba(129,140,248,.35);color:#a5b4fc;';
    restoreBtn.textContent = '📥';
    restoreBtn.title = 'Restore this backup';
    restoreBtn.onclick = () => restoreBackup(index);

    const exportBtn = document.createElement('button');
    exportBtn.style.cssText = btnBase + 'background:rgba(99,102,241,.12);border-color:rgba(99,102,241,.3);color:#818cf8;';
    exportBtn.textContent = '📤';
    exportBtn.title = 'Export this backup';
    exportBtn.onclick = () => exportBackup(index);

    const deleteBtn = document.createElement('button');
    deleteBtn.style.cssText = btnBase + 'background:rgba(248,113,113,.1);border-color:rgba(248,113,113,.3);color:#f87171;';
    deleteBtn.textContent = '🗑';
    deleteBtn.title = 'Delete this backup';
    deleteBtn.onclick = () => deleteBackup(index);

    actions.appendChild(restoreBtn);
    actions.appendChild(exportBtn);
    actions.appendChild(deleteBtn);
    item.appendChild(infoDiv);
    item.appendChild(actions);
    return item;
}

function startRenameBackup(index, currentName, nameSpan, editBtn) {
    const input = document.createElement('input');
    input.type = 'text';
    input.value = currentName;
    input.style.cssText = 'width:90px;font-size:.68rem;background:rgba(99,102,241,.12);border:1px solid rgba(99,102,241,.4);color:var(--c-text);border-radius:3px;padding:1px 4px;outline:none;';

    nameSpan.replaceWith(input);
    editBtn.textContent = '✓';
    editBtn.title = 'Save name';
    editBtn.style.opacity = '1';
    input.focus();
    input.select();

    const save = async () => {
        const newName = input.value.trim() || currentName;
        await renameBackup(index, newName);
        nameSpan.textContent = newName;
        input.replaceWith(nameSpan);
        editBtn.textContent = '✏️';
        editBtn.title = 'Rename backup';
        editBtn.style.opacity = '.5';
        editBtn.onclick = (e) => { e.stopPropagation(); startRenameBackup(index, newName, nameSpan, editBtn); };
    };

    input.addEventListener('keydown', (e) => { if (e.key === 'Enter') save(); if (e.key === 'Escape') { input.value = currentName; save(); } });
    editBtn.onclick = (e) => { e.stopPropagation(); save(); };
}

async function renameBackup(index, newName) {
    if (!state.deviceInfo) return;
    try {
        await apiRequest('/api/profiles/rename', {
            method: 'POST',
            body: JSON.stringify({
                manufacturer: state.deviceInfo.manufacturer,
                model: state.deviceInfo.model,
                backup_index: index,
                new_name: newName
            })
        });
        logToConsole(`Backup renamed: ${newName}`, 'success');
    } catch (error) {
        logToConsole(`Rename failed: ${error.message}`, 'error');
    }
}

async function restoreBackup(backupIndex) {
    if (!state.selectedDevice || !state.deviceInfo) { logToConsole('Please select a device first', 'warning'); return; }
    if (!confirm(`Restore backup ${backupIndex + 1}? This will change your device settings.`)) return;

    logToConsole(`Restoring backup ${backupIndex + 1}...`, 'info');
    try {
        const result = await apiRequest('/api/profiles/restore', {
            method: 'POST',
            body: JSON.stringify({ device_id: state.selectedDevice, manufacturer: state.deviceInfo.manufacturer, model: state.deviceInfo.model, backup_index: backupIndex })
        });
        const results = result.results;
        logToConsole(`✓ Restore complete: ${results.success.length} success, ${results.failed.length} failed`, 'success');
        await loadCommandStates(state.selectedDevice, false);
    } catch (error) {
        logToConsole(`✗ Restore failed: ${error.message}`, 'error');
    }
}

async function exportBackup(backupIndex) {
    if (!state.deviceInfo) { logToConsole('Please select a device first', 'warning'); return; }
    try {
        const result = await apiRequest('/api/profiles/export', {
            method: 'POST',
            body: JSON.stringify({ manufacturer: state.deviceInfo.manufacturer, model: state.deviceInfo.model, backup_index: backupIndex })
        });
        const dataStr = JSON.stringify(result.profile, null, 2);
        const url = URL.createObjectURL(new Blob([dataStr], { type: 'application/json' }));
        const link = document.createElement('a');
        link.href = url;
        link.download = `adb-turbo-profile-${state.deviceInfo.model}-${Date.now()}.json`;
        link.click();
        URL.revokeObjectURL(url);
        logToConsole('✓ Profile exported successfully', 'success');
    } catch (error) {
        logToConsole(`✗ Export failed: ${error.message}`, 'error');
    }
}

async function exportProfile() { await exportBackup(0); }

function showRestoreDialog() {
    if (!state.deviceInfo) { logToConsole('Please select a device first', 'warning'); return; }
    const backupsList = document.getElementById('backups-list');
    if (!backupsList || backupsList.style.display === 'none') {
        logToConsole('No backups available. Create a backup first.', 'warning');
        return;
    }
    backupsList.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function showImportDialog() {
    if (!state.selectedDevice) { logToConsole('Please select a device first', 'warning'); return; }

    const overlay = document.createElement('div');
    overlay.className = 'dialog-overlay';
    overlay.onclick = (e) => { if (e.target === overlay) overlay.remove(); };

    const dialog = document.createElement('div');
    dialog.className = 'dialog';
    dialog.innerHTML = `
        <h3 class="dialog__title">Import Profile</h3>
        <p style="color:var(--c-muted); font-size:0.85rem; margin-bottom:1rem;">Select a profile JSON file to import.</p>
        <input type="file" id="profile-file-input" accept=".json" style="display:none">
        <label for="profile-file-input" class="btn btn--secondary" style="cursor:pointer;">📁 Choose File</label>
        <span id="file-label-text" style="font-size:0.75rem; color:var(--c-dim); margin-left:0.5rem;"></span>
        <div class="dialog__actions">
            <button class="btn btn--secondary" onclick="this.closest('.dialog-overlay').remove()">Cancel</button>
            <button class="btn btn--primary" id="import-confirm-btn" disabled>Import</button>
        </div>
    `;

    overlay.appendChild(dialog);
    document.body.appendChild(overlay);

    const fileInput = document.getElementById('profile-file-input');
    const fileLabel = document.getElementById('file-label-text');
    const importBtn = document.getElementById('import-confirm-btn');

    fileInput.onchange = (e) => {
        if (e.target.files[0]) {
            fileLabel.textContent = e.target.files[0].name;
            importBtn.disabled = false;
        }
    };

    importBtn.onclick = async () => {
        const file = fileInput.files[0];
        if (!file) return;
        try {
            const profileData = JSON.parse(await file.text());
            await apiRequest('/api/profiles/import', { method: 'POST', body: JSON.stringify({ profile: profileData, device_id: state.selectedDevice }) });
            logToConsole('✓ Profile imported successfully', 'success');
            overlay.remove();
            await loadBackupsList();
        } catch (error) {
            logToConsole(`✗ Import failed: ${error.message}`, 'error');
        }
    };
}

function updateProfilesUIState(enabled) {
    const profilesCard = document.getElementById('profiles-card');
    if (!profilesCard) return;

    profilesCard.querySelectorAll('.preset-btn, .btn-action').forEach(btn => {
        btn.style.opacity = enabled ? '1' : '0.5';
        btn.style.cursor = enabled ? 'pointer' : 'not-allowed';
        btn.style.pointerEvents = enabled ? '' : 'none';
    });
}

async function applyPreset(presetName) {
    if (!state.selectedDevice) { logToConsole('Please select a device first', 'warning'); return; }

    const presetNames = {
        'high_performance': 'High Performance', 'medium_performance': 'Medium Performance',
        'max_battery': 'Max Battery',          'max_quality': 'Max Quality',
        'recommended': 'Recommended'
    };
    const displayName = presetNames[presetName] || presetName;

    if (!confirm(`Apply "${displayName}" preset? This will change multiple device settings.`)) return;

    logToConsole(`Applying "${displayName}" preset...`, 'info');
    try {
        const result = await apiRequest('/api/profiles/apply-preset', {
            method: 'POST',
            body: JSON.stringify({ device_id: state.selectedDevice, preset_name: presetName })
        });
        const results = result.results;
        logToConsole(`✓ Preset applied: ${results.success.length} settings changed`, 'success');
        if (results.failed.length > 0) logToConsole(`Failed: ${results.failed.map(f => f.name).join(', ')}`, 'warning');
        await loadCommandStates(state.selectedDevice, false);
        logToConsole('Creating auto-backup...', 'info');
        await backupCurrentSettings();
    } catch (error) {
        logToConsole(`✗ Failed to apply preset: ${error.message}`, 'error');
    }
}

// ============================================
// DNS / Network Matrix
// ============================================
function toggleDnsPanel() {
    const body  = document.getElementById('dns-panel-body');
    const caret = document.getElementById('dns-caret');
    if (!body) return;
    const hidden = body.style.display === 'none';
    body.style.display = hidden ? '' : 'none';
    if (caret) caret.classList.toggle('open', hidden);
}

async function runDnsTest() {
    const container = document.getElementById('dns-results-container');
    if (!container) return;
    container.innerHTML = '<div class="dns-empty">🔄 Testing DNS servers…</div>';
    logToConsole('Starting DNS latency test…', 'info');
    try {
        const result = await apiRequest('/api/dns/test');
        if (result && result.results) {
            renderDnsResults(result.results, container);
        } else {
            container.innerHTML = '<div class="dns-empty">No data returned.</div>';
        }
    } catch (error) {
        container.innerHTML = `<div class="dns-empty" style="color:var(--c-danger)">❌ ${error.message}</div>`;
        logToConsole(`DNS test failed: ${error.message}`, 'error');
    }
}

function renderDnsResults(results, container) {
    container.innerHTML = '';
    const sorted = [...results].sort((a, b) => (a.latency_ms ?? 9999) - (b.latency_ms ?? 9999));
    const best = sorted[0];

    sorted.forEach(r => {
        const ms   = r.latency_ms;
        const lat  = ms !== null && ms !== undefined ? `${ms}ms` : 'timeout';
        const tier = ms == null ? 'poor' : ms < 30 ? 'exc' : ms < 80 ? 'good' : ms < 150 ? 'fair' : 'poor';
        const latClass = { exc:'lat-exc', good:'lat-good', fair:'lat-fair', poor:'lat-poor' }[tier] || 'lat-none';
        const bdgClass  = { exc:'badge-exc', good:'badge-good', fair:'badge-fair', poor:'badge-poor' }[tier] || '';
        const labels    = { exc:'Excellent', good:'Good', fair:'Fair', poor:'Poor' };

        const row = document.createElement('div');
        row.className = `dns-row${r === best ? ' dns-row--best' : ''}`;
        row.innerHTML = `
            <span class="dns-row__name">${r.name}</span>
            <span class="dns-row__lat ${latClass}">${lat}</span>
            <span class="dns-row__badge ${bdgClass}">${labels[tier]||tier}</span>
        `;
        container.appendChild(row);
    });

    if (best) {
        const sug = document.createElement('div');
        sug.className = 'dns-suggestion';
        const host = best.doh || best.hostname || best.address || best.name;
        // Left: name + latency | Right: Apply button
        sug.innerHTML = `
            <span>⭐ Best: <strong>${best.name}</strong> <span class="dns-latency">&mdash; ${best.latency_ms}ms</span></span>
            <button class="dns-row__apply" onclick="applyDns('${host}')" style="flex-shrink:0">Apply ⚡</button>
        `;
        container.appendChild(sug);
    }
    logToConsole(`DNS test complete. Best: ${best?.name || 'none'}`, 'success');
}

async function applyDns(hostname) {
    if (!state.selectedDevice) { logToConsole('Please select a device first', 'warning'); return; }
    logToConsole(`Applying DNS: ${hostname}…`, 'info');
    try {
        // Correct endpoint: POST /api/dns/apply
        await apiRequest('/api/dns/apply', {
            method: 'POST',
            body: JSON.stringify({ device_id: state.selectedDevice, hostname })
        });
        logToConsole(`✓ DNS set to: ${hostname}`, 'success');
    } catch (error) {
        logToConsole(`✗ DNS apply failed: ${error.message}`, 'error');
    }
}

async function resetDns() {
    if (!state.selectedDevice) { logToConsole('Please select a device first', 'warning'); return; }
    logToConsole('Resetting DNS to automatic…', 'info');
    try {
        // Correct endpoint: POST /api/dns/reset
        await apiRequest('/api/dns/reset', { method:'POST', body: JSON.stringify({ device_id: state.selectedDevice }) });
        logToConsole('✓ DNS reset to automatic', 'success');
        const c = document.getElementById('dns-results-container');
        if (c) c.innerHTML = '<div class="dns-empty">DNS reset. Tap ⚡ Test to probe again.</div>';
    } catch (error) {
        logToConsole(`✗ DNS reset failed: ${error.message}`, 'error');
    }
}

async function deleteBackup(backupIndex) {
    if (!state.deviceInfo) return;
    try {
        await apiRequest('/api/profiles/delete', {
            method: 'POST',
            body: JSON.stringify({
                manufacturer: state.deviceInfo.manufacturer,
                model: state.deviceInfo.model,
                backup_index: backupIndex
            })
        });
        logToConsole(`✓ Backup ${backupIndex + 1} deleted`, 'success');
        await loadBackupsList();
    } catch (error) {
        logToConsole(`✗ Delete failed: ${error.message}`, 'error');
    }
}

// ============================================
// Initialization
// ============================================
async function init() {
    logToConsole('Initializing adb-turbo EPIC...', 'info');

    loadCollapsedSections();

    const savedAutoRefresh = localStorage.getItem('autoRefreshEnabled');
    if (savedAutoRefresh !== null) state.autoRefreshEnabled = savedAutoRefresh === 'true';

    const indicator = document.getElementById('refresh-indicator');
    const icon = document.getElementById('auto-refresh-icon');
    if (!state.autoRefreshEnabled) {
        if (indicator) indicator.classList.add('paused');
        if (icon) icon.textContent = '▶';
    }

    // Show presets but disabled until device selected
    const profilesCard = document.getElementById('profiles-card');
    if (profilesCard) profilesCard.style.display = 'block';
    updateProfilesUIState(false);

    await checkADB();
    await loadCategories();
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
