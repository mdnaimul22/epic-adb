document.addEventListener('alpine:init', () => {
    Alpine.data('dnsTester', () => ({
        results: [
            { name: "Cloudflare", latency_ms: null },
            { name: "Google", latency_ms: null },
            { name: "AdGuard", latency_ms: null },
            { name: "Quad9", latency_ms: null },
            { name: "OpenDNS", latency_ms: null }
        ],
        isLoading: false,
        error: null,
        deviceId: null,

        init() {
            setTimeout(() => {
                if (window.appState && window.appState.selectedDevice && !this.deviceId) {
                    this.handleDeviceSelection(window.appState.selectedDevice);
                }
            }, 100);
        },

        get bestResult() {
            if (this.results.length === 0) return null;
            return [...this.results].sort((a, b) => (a.latency_ms ?? 9999) - (b.latency_ms ?? 9999))[0];
        },

        handleDeviceSelection(id) {
            this.deviceId = id;
            if (!this.deviceId) {
                this.results.forEach(r => r.latency_ms = null);
                return;
            }
            
            const cached = sessionStorage.getItem(`dnsTestRun_${this.deviceId}`);
            if (cached) {
                try {
                    const parsed = JSON.parse(cached);
                    if (Array.isArray(parsed) && parsed.length > 0) {
                        this.results = parsed;
                        return;
                    } else {
                        // Clear invalid cache
                        sessionStorage.removeItem(`dnsTestRun_${this.deviceId}`);
                    }
                } catch(e) {}
            }
            
            this.runTest();
        },

        async runTest() {
            if (!this.deviceId) return;
            this.isLoading = true;
            this.error = null;
            this.results.forEach(r => r.latency_ms = null);
            logToConsole('Starting DNS latency test…', 'info');
            try {
                const response = await fetch(`${window.location.origin}/api/dns/test`, {
                    headers: { 'Content-Type': 'application/json' }
                });
                const result = await response.json();
                if (!response.ok || !result.success) throw new Error(result.error || 'Request failed');
                
                if (result.data && result.data.results) {
                    this.results = result.data.results;
                    sessionStorage.setItem(`dnsTestRun_${this.deviceId}`, JSON.stringify(this.results));
                } else {
                    this.error = 'No data returned.';
                }
            } catch (err) {
                this.error = err.message;
                logToConsole(`DNS test failed: ${err.message}`, 'error');
            } finally {
                this.isLoading = false;
            }
        },

        async applyDns(host) {
            if (!this.deviceId) return;
            logToConsole(`Applying DNS: ${host}...`, 'info');
            try {
                const response = await fetch(`${window.location.origin}/api/dns/apply`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ device_id: this.deviceId, hostname: host })
                });
                const result = await response.json();
                if (!response.ok || !result.success) throw new Error(result.error || 'Request failed');
                logToConsole(`✓ DNS applied successfully`, 'success');
            } catch (err) {
                logToConsole(`✗ Failed to apply DNS: ${err.message}`, 'error');
            }
        },

        async resetDns() {
            if (!this.deviceId) return;
            if (!confirm('Are you sure you want to reset DNS settings?')) return;
            logToConsole('Resetting DNS settings...', 'info');
            try {
                const response = await fetch(`${window.location.origin}/api/dns/reset`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ device_id: this.deviceId })
                });
                const result = await response.json();
                if (!response.ok || !result.success) throw new Error(result.error || 'Request failed');
                logToConsole('✓ DNS settings reset to default', 'success');
            } catch (err) {
                logToConsole(`✗ Reset failed: ${err.message}`, 'error');
            }
        },

        getTier(ms) {
            return ms == null ? 'none' : ms < 30 ? 'exc' : ms < 80 ? 'good' : ms < 150 ? 'fair' : 'poor';
        },
        
        getLatClass(tier) {
            return { exc:'lat-exc', good:'lat-good', fair:'lat-fair', poor:'lat-poor' }[tier] || 'lat-none';
        },
        
        getBdgClass(tier) {
            return { exc:'badge-exc', good:'badge-good', fair:'badge-fair', poor:'badge-poor' }[tier] || '';
        },
        
        getLabel(tier) {
            return { exc:'Excellent', good:'Good', fair:'Fair', poor:'Poor' }[tier] || tier;
        }
    }));

    Alpine.data('profileManager', () => ({
        deviceId: null,
        deviceInfo: null,
        backups: [],
        isLoading: false,

        init() {
            setTimeout(() => {
                if (window.appState && window.appState.selectedDevice && window.appState.deviceInfo && !this.deviceId) {
                    this.handleDeviceLoaded({ deviceId: window.appState.selectedDevice, info: window.appState.deviceInfo });
                }
            }, 100);
        },

        handleDeviceLoaded(data) {
            this.deviceId = data.deviceId;
            this.deviceInfo = data.info;
            if (this.deviceId && this.deviceInfo) {
                this.loadBackups();
            } else {
                this.backups = [];
            }
        },

        async loadBackups() {
            if (!this.deviceId || !this.deviceInfo) return;
            try {
                const response = await fetch(`${window.location.origin}/api/profiles?manufacturer=${encodeURIComponent(this.deviceInfo.manufacturer)}&model=${encodeURIComponent(this.deviceInfo.model)}`);
                const result = await response.json();
                if (result.success) {
                    this.backups = result.data.backups || [];
                }
            } catch (err) {
                console.error('Failed to load backups:', err);
            }
        },

        async applyPreset(presetId) {
            if (!this.deviceId) return;
            logToConsole(`Applying preset: ${presetId}...`, 'info');
            try {
                const response = await fetch(`${window.location.origin}/api/profiles/apply-preset`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ device_id: this.deviceId, preset_name: presetId })
                });
                const result = await response.json();
                if (!response.ok || !result.success) throw new Error(result.error || 'Request failed');
                
                logToConsole(`✓ Preset applied successfully`, 'success');
                // Refresh command states via global event
                window.dispatchEvent(new CustomEvent('refresh-command-states', { detail: this.deviceId }));
            } catch (err) {
                logToConsole(`✗ Preset failed: ${err.message}`, 'error');
            }
        },

        async backupCurrentSettings() {
            if (!this.deviceId || !this.deviceInfo) return;
            logToConsole('Creating backup...', 'info');
            try {
                const response = await fetch(`${window.location.origin}/api/profiles`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        device_id: this.deviceId,
                        manufacturer: this.deviceInfo.manufacturer,
                        model: this.deviceInfo.model
                    })
                });
                const result = await response.json();
                if (!response.ok || !result.success) throw new Error(result.error || 'Request failed');
                
                const settingsCount = result.data.profile.settings ? Object.keys(result.data.profile.settings).length : 0;
                logToConsole(`✓ Backup created: ${settingsCount} settings saved`, 'success');
                this.loadBackups();
            } catch (err) {
                logToConsole(`✗ Backup failed: ${err.message}`, 'error');
            }
        },

        async deleteBackup(index) {
            if (!this.deviceInfo) return;
            try {
                const response = await fetch(`${window.location.origin}/api/profiles?manufacturer=${encodeURIComponent(this.deviceInfo.manufacturer)}&model=${encodeURIComponent(this.deviceInfo.model)}&backup_index=${index}`, {
                    method: 'DELETE'
                });
                const result = await response.json();
                if (!response.ok || !result.success) throw new Error(result.error || 'Request failed');
                
                logToConsole(`✓ Backup ${index + 1} deleted`, 'success');
                this.loadBackups();
            } catch (err) {
                logToConsole(`✗ Delete failed: ${err.message}`, 'error');
            }
        },

        async restoreBackup(index) {
            if (!this.deviceId || !this.deviceInfo) return;
            if (!confirm(`Restore backup ${index + 1}? This will change your device settings.`)) return;
            
            logToConsole(`Restoring backup ${index + 1}...`, 'info');
            try {
                const response = await fetch(`${window.location.origin}/api/profiles/restore`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        device_id: this.deviceId,
                        manufacturer: this.deviceInfo.manufacturer,
                        model: this.deviceInfo.model,
                        backup_index: index
                    })
                });
                const result = await response.json();
                if (!response.ok || !result.success) throw new Error(result.error || 'Request failed');
                
                const res = result.data.results;
                logToConsole(`✓ Restore complete: ${res.success.length} success, ${res.failed.length} failed`, 'success');
                window.dispatchEvent(new CustomEvent('refresh-command-states', { detail: this.deviceId }));
            } catch(e) {
                logToConsole(`Restore failed: ${e.message}`, 'error');
            }
        },

        exportBackup(index) {
            if (!this.deviceInfo) return;
            fetch(`${window.location.origin}/api/profiles/export?manufacturer=${encodeURIComponent(this.deviceInfo.manufacturer)}&model=${encodeURIComponent(this.deviceInfo.model)}&backup_index=${index}`)
                .then(res => res.json())
                .then(result => {
                    if(!result.success) throw new Error(result.error);
                    const dataStr = JSON.stringify(result.data.profile, null, 2);
                    const url = URL.createObjectURL(new Blob([dataStr], { type: 'application/json' }));
                    const link = document.createElement('a');
                    link.href = url;
                    link.download = `adb-turbo-profile-${this.deviceInfo.model}-${Date.now()}.json`;
                    link.click();
                    URL.revokeObjectURL(url);
                    logToConsole('✓ Profile exported successfully', 'success');
                })
                .catch(err => logToConsole(`✗ Export failed: ${err.message}`, 'error'));
        },

        async renameBackup(index, newName) {
            if (!this.deviceId || !this.deviceInfo) return;
            if (!newName) return;
            try {
                const response = await fetch(`${window.location.origin}/api/profiles`, {
                    method: 'PATCH',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        device_id: this.deviceId,
                        manufacturer: this.deviceInfo.manufacturer,
                        model: this.deviceInfo.model,
                        backup_index: index,
                        new_name: newName
                    })
                });
                const result = await response.json();
                if (!response.ok || !result.success) throw new Error(result.error || 'Request failed');
                
                logToConsole(`Backup renamed: ${newName}`, 'success');
                this.loadBackups();
            } catch (err) {
                logToConsole(`Rename failed: ${err.message}`, 'error');
            }
        },
        
        showImportDialog() {
            // Keep it simple: dispatch event to vanilla JS for now, or implement a basic file picker here.
            // Since it requires a DOM file input, let's create one dynamically.
            if (!this.deviceId) return;
            
            const input = document.createElement('input');
            input.type = 'file';
            input.accept = '.json';
            input.onchange = (e) => {
                const file = e.target.files[0];
                if (!file) return;
                const reader = new FileReader();
                reader.onload = async (re) => {
                    try {
                        const profileData = JSON.parse(re.target.result);
                        const response = await fetch(`${window.location.origin}/api/profiles/import`, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                device_id: this.deviceId,
                                manufacturer: this.deviceInfo.manufacturer,
                                model: this.deviceInfo.model,
                                profile: profileData
                            })
                        });
                        const result = await response.json();
                        if (!response.ok || !result.success) throw new Error(result.error || 'Request failed');
                        logToConsole('✓ Profile imported successfully', 'success');
                        this.loadBackups();
                    } catch (err) {
                        logToConsole(`✗ Import failed: ${err.message}`, 'error');
                    }
                };
                reader.readAsText(file);
            };
            input.click();
        }
    }));

    Alpine.data('commandCore', () => ({
        categories: [],
        searchQuery: '',
        expandAll: true,
        deviceId: null,
        isSamsung: false,
        states: {},

        async init() {
            await this.loadCategories();
        },

        handleDeviceSelection(detail) {
            if (!detail) {
                this.deviceId = null;
                this.isSamsung = false;
                this.states = {};
                return;
            }

            // Handle both simple ID string and detailed info object
            if (typeof detail === 'string') {
                this.deviceId = detail;
            } else if (detail.deviceId) {
                this.deviceId = detail.deviceId;
                if (detail.info) {
                    this.isSamsung = detail.info.manufacturer?.toLowerCase() === 'samsung';
                }
            }

            if (this.deviceId) {
                this.loadCommandStates(this.deviceId);
            }
        },

        async loadCategories() {
            try {
                const result = await apiRequest('/api/categories');
                this.categories = result.categories || [];
                // Update stats
                const totalCommands = this.categories.reduce((sum, cat) => sum + cat.commands.length, 0);
                const highImpact = this.categories.filter(cat => cat.impact === 'high').length;
                const totalEl = document.getElementById('total-commands');
                const hiEl = document.getElementById('high-impact');
                if (totalEl) totalEl.textContent = totalCommands;
                if (hiEl) hiEl.textContent = highImpact;

                logToConsole(`Loaded ${this.categories.length} command categories`, 'success');
            } catch (error) {
                logToConsole(`Error loading categories: ${error.message}`, 'error');
            }
        },

        async loadCommandStates(deviceId, silent = false) {
            try {
                if (!silent) logToConsole('Reading current toggle states from device...', 'info');
                const result = await apiRequest(`/api/command-states/${deviceId}`);
                if (result && result.states) {
                    this.states = result.states;
                    if (!silent) {
                        const updatedCount = Object.keys(result.states).length;
                        logToConsole(`✓ Loaded ${updatedCount} toggle states from device`, 'success');
                    }
                }
            } catch (error) {
                if (!silent) logToConsole(`Error loading command states: ${error.message}`, 'error');
            }
        },

        getCategoryIcon(categoryId) {
            const icons = {
                animation_settings: '⚡', background_processes: '🔄', fixed_performance: '🚀',
                ram_plus: '💾', refresh_rate: '🖥️', app_launch_speed: '⏱️',
                game_optimization_samsung: '🎮', audio_quality: '🔊', touchscreen_latency: '👆',
                system_optimization: '⚙️', private_dns: '🔒', network_performance: '📡', power_management: '🔋'
            };
            return icons[categoryId] || '📋';
        },

        filteredCategories() {
            const q = this.searchQuery.toLowerCase().trim();
            if (!q) return this.categories;

            return this.categories.map(cat => {
                const matchedCommands = cat.commands.filter(cmd => 
                    cmd.name.toLowerCase().includes(q) || 
                    (cmd.description || '').toLowerCase().includes(q)
                );
                return { ...cat, commands: matchedCommands };
            }).filter(cat => cat.commands.length > 0);
        },

        toggleExpandAll() {
            this.expandAll = !this.expandAll;
        },

        async toggleCommand(command) {
            if (!this.deviceId) {
                logToConsole('Please select a device first', 'warning');
                return;
            }

            const isActive = this.states[command.name] === true;
            const action = isActive ? 'disable' : 'enable';
            const cmd = isActive ? command.disable_cmd : command.enable_cmd;

            if (!cmd) {
                logToConsole(`No ${action} command available for ${command.name}`, 'warning');
                return;
            }

            this.states[command.name] = 'loading';

            try {
                await apiRequest('/api/execute', {
                    method: 'POST',
                    body: JSON.stringify({ device_id: this.deviceId, command: cmd, action })
                });

                // Optimistically update
                this.states[command.name] = !isActive;
                logToConsole(`${command.name}: ${action}d`, 'success');
                
                // Verify state
                setTimeout(() => this.loadCommandStates(this.deviceId, true), 500);
            } catch (error) {
                logToConsole(`${command.name} failed: ${error.message}`, 'error');
                this.states[command.name] = isActive; // Revert
            }
        }
    }));

    Alpine.data('systemStatus', () => ({
        details: null,

        handleDeviceInfo(detail) {
            this.details = detail?.info?.details || null;
        },

        get groups() {
            if (!this.details) return [];
            const d = this.details;
            const groups = [];

            if (d.battery) {
                groups.push({
                    title: '🔋', label: 'Battery', data: d.battery, keys: [
                        { key: 'level', label: 'Level', suffix: '%', ico: '🔋', bar: true, color: v => +v < 20 ? 'danger' : +v < 50 ? 'warn' : 'good' },
                        { key: 'temperature', label: 'Temp', ico: '🌡️' },
                        { key: 'health', label: 'Health', ico: '💚' },
                        { key: 'status', label: 'Status', ico: '⚡' }
                    ]
                });
            }

            if (d.network?.ip_address) {
                groups.push({
                    title: '📡', label: 'Network', data: d.network, keys: [
                        { key: 'ip_address', label: 'IP', ico: '🌐', valColor: 'accent' }
                    ]
                });
            }

            if (d.display) {
                groups.push({
                    title: '🖥️', label: 'Display', data: d.display, keys: [
                        { key: 'resolution', label: 'Res', ico: '📐', valColor: 'info' },
                        { key: 'density', label: 'DPI', ico: '🔢', valColor: 'info' }
                    ]
                });
            }

            if (d.memory) {
                groups.push({
                    title: '💾', label: 'Memory', data: d.memory, keys: [
                        { key: 'total', label: 'Total', ico: '💾' },
                        { key: 'available', label: 'Free', ico: '🟢', color: v => parseInt(v) < 512 ? 'warn' : 'good' }
                    ]
                });
            }

            if (d.cpu) {
                groups.push({
                    title: '⚙️', label: 'CPU', data: d.cpu, keys: [
                        { key: 'cores', label: 'Cores', ico: '⚙️', valColor: 'info' },
                        { key: 'hardware', label: 'HW', ico: '🔩' }
                    ]
                });
            }

            if (d.storage) {
                groups.push({
                    title: '💿', label: 'Storage', data: d.storage, keys: [
                        { key: 'total', label: 'Total', ico: '💿' },
                        { key: 'used', label: 'Used', ico: '📊' },
                        { key: 'available', label: 'Free', ico: '🟢' }
                    ]
                });
            }

            if (d.uptime) groups.push({ title: '⏱️', label: 'System', data: { uptime: d.uptime }, keys: [{ key: 'uptime', label: 'Up', ico: '⏱️' }] });
            if (d.current_app) groups.push({ title: '📱', label: 'Active', data: { app: d.current_app }, keys: [{ key: 'app', label: 'App', ico: '📱', valColor: 'accent' }] });

            return groups;
        },

        getValColor(item, raw) {
            if (item.color) return `reg-row__val--${item.color(raw)}`;
            if (item.valColor) return `reg-row__val--${item.valColor}`;
            return '';
        }
    }));
});
