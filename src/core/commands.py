"""
ADB Command Library - Categorized by impact
Standardized using Pydantic V2 Models
Restored 43 features from backup metadata
"""

from typing import List
from src.schema.models import ADBCommandModel, ADBCategoryModel

# Define all command categories ordered by impact
COMMAND_CATEGORIES: List[ADBCategoryModel] = [
    # ANIMATION SETTINGS (3 commands)
    ADBCategoryModel(
        id="animation_settings",
        name="Animation Settings",
        description="Adjust or disable system animations for faster UI response and reduced battery consumption",
        impact="high",
        commands=[
            ADBCommandModel(
                name="Window Animation Scale",
                description="Controls animation when opening/closing apps",
                enable_cmd="shell settings put global window_animation_scale 1.0",
                disable_cmd="shell settings put global window_animation_scale 0.0",
                get_cmd="shell settings get global window_animation_scale",
                explanation="Disabling window animations makes your device feel significantly faster by removing the visual delay when opening or closing applications.",
                impact="high"
            ),
            ADBCommandModel(
                name="Transition Animation Scale",
                description="Controls animation when switching between apps",
                enable_cmd="shell settings put global transition_animation_scale 1.0",
                disable_cmd="shell settings put global transition_animation_scale 0.0",
                get_cmd="shell settings get global transition_animation_scale",
                explanation="Moving between apps becomes instant when transition animations are disabled.",
                impact="high"
            ),
            ADBCommandModel(
                name="Animator Duration Scale",
                description="Controls how long animations play before transitioning",
                enable_cmd="shell settings put global animator_duration_scale 1.0",
                disable_cmd="shell settings put global animator_duration_scale 0.0",
                get_cmd="shell settings get global animator_duration_scale",
                explanation="Setting animator scale to 0 eliminates waiting for system animations to complete.",
                impact="high"
            ),
        ]
    ),
    
    # BACKGROUND PROCESSES (1 command)
    ADBCategoryModel(
        id="background_processes",
        name="Kill Background Apps",
        description="Manage and terminate background processes to free up RAM and CPU resources",
        impact="high",
        commands=[
            ADBCommandModel(
                name="Trim All Caches",
                description="Clear app caches to free up storage and improve performance",
                enable_cmd="",
                disable_cmd="shell am send-trim-memory -d all COMPLETE",
                explanation="Sends TRIM_MEMORY_COMPLETE signal to all background apps, forcing them to release cached memory immediately.",
                impact="high"
            ),
        ]
    ),
    
    # FIXED PERFORMANCE (1 command)
    ADBCategoryModel(
        id="fixed_performance",
        name="Fixed Performance Mode",
        description="Lock CPU and GPU to maximum performance, disabling thermal throttling",
        impact="high",
        commands=[
            ADBCommandModel(
                name="Fixed Performance Mode",
                description="Enable sustained high performance (may cause heating)",
                enable_cmd="shell cmd power set-fixed-performance-mode-enabled true",
                disable_cmd="shell cmd power set-fixed-performance-mode-enabled false",
                get_cmd="shell dumpsys power | grep mFixedPerformanceModeEnabled",
                explanation="Disables thermal throttling to provide maximum performance for demanding tasks.",
                impact="high"
            ),
        ]
    ),
    
    # RAM PLUS (2 commands)
    ADBCategoryModel(
        id="ram_plus",
        name="Disable RAM Plus",
        description="Disable virtual RAM expansion to improve performance and save battery",
        impact="high",
        commands=[
            ADBCommandModel(
                name="ZRAM (Virtual RAM)",
                description="Disable compressed RAM (may improve performance on some devices)",
                enable_cmd="shell settings put global zram_enabled 1",
                disable_cmd="shell settings put global zram_enabled 0",
                get_cmd="shell settings get global zram_enabled",
                explanation="ZRAM uses CPU cycles to compress memory. Disabling it may reduce CPU overhead on powerful devices.",
                impact="high"
            ),
            ADBCommandModel(
                name="RAM Expansion",
                description="Disable RAM expansion feature (Samsung/some OEMs)",
                enable_cmd="shell settings put global ram_expand_size_list 4",
                disable_cmd="shell settings put global ram_expand_size_list 0",
                get_cmd="shell settings get global ram_expand_size_list",
                explanation="Using storage as virtual memory is slower than physical RAM. Disabling it can improve system responsiveness.",
                impact="high"
            ),
        ]
    ),
    
    # REFRESH RATE (4 commands)
    ADBCategoryModel(
        id="refresh_rate",
        name="Refresh Rate & Display",
        description="Adjust screen refresh rate, window blur, and transparency for better performance",
        impact="medium",
        commands=[
            ADBCommandModel(
                name="Peak Refresh Rate",
                description="Set maximum screen refresh rate (e.g., 120Hz)",
                enable_cmd="shell settings put system peak_refresh_rate 120.0",
                disable_cmd="shell settings put system peak_refresh_rate 60.0",
                get_cmd="shell settings get system peak_refresh_rate",
                explanation="Higher refresh rates provide smoother visuals but consume more battery.",
                impact="medium"
            ),
            ADBCommandModel(
                name="Minimum Refresh Rate",
                description="Set minimum screen refresh rate",
                enable_cmd="shell settings put system min_refresh_rate 120.0",
                disable_cmd="shell settings put system min_refresh_rate 60.0",
                get_cmd="shell settings get system min_refresh_rate",
                explanation="Constant refresh rate maintains smoothness but prevents power saving during idle.",
                impact="medium"
            ),
            ADBCommandModel(
                name="Window Blur Effects",
                description="Disable blur effects on windows and backgrounds",
                enable_cmd="shell settings put global disable_window_blurs 0",
                disable_cmd="shell settings put global disable_window_blurs 1",
                get_cmd="shell settings get global disable_window_blurs",
                explanation="Reducing transparency and blur effects significantly lowers GPU processing requirements.",
                impact="medium"
            ),
            ADBCommandModel(
                name="Reduce Transparency",
                description="Reduce transparency effects for better performance",
                enable_cmd="shell settings put global accessibility_reduce_transparency 0",
                disable_cmd="shell settings put global accessibility_reduce_transparency 1",
                get_cmd="shell settings get global accessibility_reduce_transparency",
                explanation="Transparency effects add rendering overhead. Disabling them helps lower-end GPUs.",
                impact="medium"
            ),
        ]
    ),
    
    # APP LAUNCH SPEED (4 commands)
    ADBCategoryModel(
        id="app_launch_speed",
        name="Speed Up App Launch",
        description="Optimize app startup process for faster launch times",
        impact="medium",
        commands=[
            ADBCommandModel(
                name="Rakuten Denwa Service",
                description="Disable Rakuten phone service (if present)",
                enable_cmd="shell settings put system rakuten_denwa 1",
                disable_cmd="shell settings put system rakuten_denwa 0",
                get_cmd="shell settings get system rakuten_denwa",
                explanation="Disables Rakuten phone service which may slow down app launches on devices with this service installed.",
                impact="medium"
            ),
            ADBCommandModel(
                name="Security Reports",
                description="Disable automatic security report sending",
                enable_cmd="shell settings put system send_security_reports 1",
                disable_cmd="shell settings put system send_security_reports 0",
                get_cmd="shell settings get system send_security_reports",
                explanation="Prevents the system from automatically sending security reports, reducing background activity during app launches.",
                impact="medium"
            ),
            ADBCommandModel(
                name="App Error Reporting",
                description="Disable automatic app error reporting",
                enable_cmd="shell settings put secure send_action_app_error 1",
                disable_cmd="shell settings put secure send_action_app_error 0",
                get_cmd="shell settings get secure send_action_app_error",
                explanation="Disables automatic error reporting which can slow down app startup, especially when apps crash or encounter errors.",
                impact="medium"
            ),
            ADBCommandModel(
                name="Activity Start Logging",
                description="Disable activity start logging",
                enable_cmd="shell settings put global activity_starts_logging_enabled 1",
                disable_cmd="shell settings put global activity_starts_logging_enabled 0",
                get_cmd="shell settings get global activity_starts_logging_enabled",
                explanation="Disables logging of app activity starts, reducing overhead during app launches.",
                impact="medium"
            ),
        ]
    ),
    
    # GAME OPTIMIZATION SAMSUNG (4 commands)
    ADBCategoryModel(
        id="game_optimization_samsung",
        name="Game Optimization (Samsung)",
        description="Disable Samsung's Game Optimizing Service features that may throttle performance",
        impact="medium",
        commands=[
            ADBCommandModel(
                name="Game SDK",
                description="Disable Samsung Game SDK reporting",
                enable_cmd="shell settings put secure gamesdk_version 1",
                disable_cmd="shell settings put secure gamesdk_version 0",
                get_cmd="shell settings get secure gamesdk_version",
                explanation="Samsung's Game SDK can throttle performance. Disabling it may prioritize raw speed.",
                impact="medium",
                samsung_only=True
            ),
            ADBCommandModel(
                name="Game Home",
                description="Disable Samsung Game Launcher home",
                enable_cmd="shell settings put secure game_home_enable 1",
                disable_cmd="shell settings put secure game_home_enable 0",
                get_cmd="shell settings get secure game_home_enable",
                explanation="Turning off Game Launcher components can save system resources.",
                impact="medium",
                samsung_only=True
            ),
            ADBCommandModel(
                name="Game Bixby Block",
                description="Block Bixby during gaming",
                enable_cmd="shell settings put secure game_bixby_block 0",
                disable_cmd="shell settings put secure game_bixby_block 1",
                get_cmd="shell settings get secure game_bixby_block",
                explanation="Prevents Bixby from activating during sessions, avoiding accidental triggers.",
                impact="medium",
                samsung_only=True
            ),
            ADBCommandModel(
                name="Game Auto Temperature Control",
                description="Disable auto temperature throttling for games",
                enable_cmd="shell settings put secure game_auto_temperature_control 1",
                disable_cmd="shell settings put secure game_auto_temperature_control 0",
                get_cmd="shell settings get secure game_auto_temperature_control",
                explanation="Disables thermal throttling specifically for Gaming. Use with caution for potential heating.",
                impact="medium",
                samsung_only=True
            ),
        ]
    ),
    
    # AUDIO QUALITY (2 commands)
    ADBCategoryModel(
        id="audio_quality",
        name="Audio Quality Enhancement",
        description="Enable advanced audio processing for better sound quality",
        impact="medium",
        commands=[
            ADBCommandModel(
                name="K2HD Audio Effect",
                description="Enable K2HD audio enhancement",
                enable_cmd="shell settings put system k2hd_effect 1",
                disable_cmd="shell settings put system k2hd_effect 0",
                get_cmd="shell settings get system k2hd_effect",
                explanation="K2HD (K2 High Definition) upsamples audio output to improve sound clarity.",
                impact="medium"
            ),
            ADBCommandModel(
                name="Tube Amp Effect",
                description="Enable tube amplifier audio characteristics",
                enable_cmd="shell settings put system tube_amp_effect 1",
                disable_cmd="shell settings put system tube_amp_effect 0",
                get_cmd="shell settings get system tube_amp_effect",
                explanation="Simulates analog tube amplifier sound for a warmer audio profile.",
                impact="medium"
            ),
        ]
    ),
    
    # TOUCH LATENCY (4 commands)
    ADBCategoryModel(
        id="touchscreen_latency",
        name="Touchscreen Response",
        description="Reduce touch latency and improve touchscreen responsiveness",
        impact="medium",
        commands=[
            ADBCommandModel(
                name="Long Press Timeout",
                description="Reduce long-press delay for faster response",
                enable_cmd="shell settings put secure long_press_timeout 500",
                disable_cmd="shell settings put secure long_press_timeout 250",
                get_cmd="shell settings get secure long_press_timeout",
                explanation="Shortens the time required to register long-press actions.",
                impact="medium"
            ),
            ADBCommandModel(
                name="Multi-Press Timeout",
                description="Reduce multi-tap detection timeout",
                enable_cmd="shell settings put secure multi_press_timeout 500",
                disable_cmd="shell settings put secure multi_press_timeout 250",
                get_cmd="shell settings get secure multi_press_timeout",
                explanation="Decreases waiting time for multiple taps like double-taps.",
                impact="medium"
            ),
            ADBCommandModel(
                name="Tap Duration Threshold",
                description="Minimize tap duration requirement",
                enable_cmd="shell settings put secure tap_duration_threshold 0.1",
                disable_cmd="shell settings put secure tap_duration_threshold 0.0",
                get_cmd="shell settings get secure tap_duration_threshold",
                explanation="Allows more instantaneous registration of single taps.",
                impact="medium"
            ),
            ADBCommandModel(
                name="Touch Blocking Period",
                description="Minimize touch blocking period",
                enable_cmd="shell settings put secure touch_blocking_period 0.1",
                disable_cmd="shell settings put secure touch_blocking_period 0.0",
                get_cmd="shell settings get secure touch_blocking_period",
                explanation="Removes the delay after certain touch interactions.",
                impact="medium"
            ),
        ]
    ),
    
    # SYSTEM OPTIMIZATION (4 commands)
    ADBCategoryModel(
        id="system_optimization",
        name="System Optimization",
        description="Core system optimizations for graphics and processing",
        impact="low",
        commands=[
            ADBCommandModel(
                name="Force OpenGL",
                description="Force GPU rendering using OpenGL",
                enable_cmd="shell setprop debug.force-opengl 1",
                disable_cmd="shell setprop debug.force-opengl 0",
                get_cmd="shell getprop debug.force-opengl",
                explanation="Can improve performance in certain graphics-heavy UI components.",
                impact="low"
            ),
            ADBCommandModel(
                name="GPU VSync",
                description="Force vertical sync using GPU",
                enable_cmd="shell setprop debug.hwc.force_gpu_vsync 1",
                disable_cmd="shell setprop debug.hwc.force_gpu_vsync 0",
                get_cmd="shell getprop debug.hwc.force_gpu_vsync",
                explanation="Improves synchronization between frame generation and display.",
                impact="low"
            ),
            ADBCommandModel(
                name="Multicore Packet Scheduler",
                description="Enable parallel network processing",
                enable_cmd="shell settings put system multicore_packet_scheduler 1",
                disable_cmd="shell settings put system multicore_packet_scheduler 0",
                get_cmd="shell settings get system multicore_packet_scheduler",
                explanation="Utilizes multiple CPU cores for network parsing.",
                impact="low"
            ),
            ADBCommandModel(
                name="Enhanced CPU Responsiveness",
                description="Samsung Enhanced CPU Responsiveness",
                enable_cmd="shell settings put global sem_enhanced_cpu_responsiveness 1",
                disable_cmd="shell settings put global sem_enhanced_cpu_responsiveness 0",
                get_cmd="shell settings get global sem_enhanced_cpu_responsiveness",
                explanation="Allows extreme CPU spike performance for Samsung devices.",
                impact="low",
                samsung_only=True
            ),
        ]
    ),
    
    # PRIVATE DNS (2 commands)
    ADBCategoryModel(
        id="private_dns",
        name="Private DNS & AdBlocking",
        description="Configure secure DNS and ad-blocking capabilities",
        impact="low",
        commands=[
            ADBCommandModel(
                name="Private DNS Mode",
                description="Enable/disable hostname-based private DNS",
                enable_cmd="shell settings put global private_dns_mode hostname",
                disable_cmd="shell settings put global private_dns_mode off",
                get_cmd="shell settings get global private_dns_mode",
                explanation="Enabling Private DNS encrypts your requests for better security.",
                impact="low"
            ),
            ADBCommandModel(
                name="AdGuard DNS",
                description="Use AdGuard DNS for blocking network ads",
                enable_cmd="shell settings put global private_dns_specifier dns.adguard.com",
                disable_cmd="shell settings put global private_dns_specifier ''",
                get_cmd="shell settings get global private_dns_specifier",
                explanation="Sets the specific DNS server to AdGuard to block network ads.",
                impact="low"
            ),
        ]
    ),
    
    # NETWORK PERFORMANCE (7 commands)
    ADBCategoryModel(
        id="network_performance",
        name="Network Performance",
        description="Optimization of WiFi, Cellular, and background scanning",
        impact="low",
        commands=[
            ADBCommandModel(
                name="WiFi Power Save",
                description="Maintain WiFi at full power (Disable power save)",
                enable_cmd="shell settings put global wifi_power_save 1",
                disable_cmd="shell settings put global wifi_power_save 0",
                get_cmd="shell settings get global wifi_power_save",
                explanation="Ensures WiFi doesn't throttle down, maintaining faster connections.",
                impact="low"
            ),
            ADBCommandModel(
                name="Cellular on Boot",
                description="Ensure data is active immediately on boot",
                enable_cmd="shell settings put global enable_cellular_on_boot 1",
                disable_cmd="shell settings put global enable_cellular_on_boot 0",
                get_cmd="shell settings get global enable_cellular_on_boot",
                explanation="Starts cellular radio immediately during the boot sequence.",
                impact="low"
            ),
            ADBCommandModel(
                name="Mobile Data Always On",
                description="Keep mobile data active even when connected to WiFi",
                enable_cmd="shell settings put global mobile_data_always_on 1",
                disable_cmd="shell settings put global mobile_data_always_on 0",
                get_cmd="shell settings get global mobile_data_always_on",
                explanation="Allows instantaneous switching from WiFi to Cellular data.",
                impact="low"
            ),
            ADBCommandModel(
                name="Tether Offload",
                description="Enable hardware tethering offload",
                enable_cmd="shell settings put global tether_offload_disabled 0",
                disable_cmd="shell settings put global tether_offload_disabled 1",
                get_cmd="shell settings get global tether_offload_disabled",
                explanation="Uses dedicated networking hardware for better hotspots.",
                impact="low"
            ),
            ADBCommandModel(
                name="BLE Scan Always Enabled",
                description="Reduce Bluetooth LE passive background scanning",
                enable_cmd="shell settings put global ble_scan_always_enabled 1",
                disable_cmd="shell settings put global ble_scan_always_enabled 0",
                get_cmd="shell settings get global ble_scan_always_enabled",
                explanation="Controls whether Bluetooth constantly scans for nearby devices.",
                impact="low"
            ),
            ADBCommandModel(
                name="Network Scoring UI",
                description="Disable system network analytics UI",
                enable_cmd="shell settings put global network_scoring_ui_enabled 1",
                disable_cmd="shell settings put global network_scoring_ui_enabled 0",
                get_cmd="shell settings get global network_scoring_ui_enabled",
                explanation="Disables background UI overhead for network quality scoring.",
                impact="low"
            ),
            ADBCommandModel(
                name="Network Recommendations",
                description="Disable automatic network suggestions",
                enable_cmd="shell settings put global network_recommendations_enabled 1",
                disable_cmd="shell settings put global network_recommendations_enabled 0",
                get_cmd="shell settings get global network_recommendations_enabled",
                explanation="Prevents constant background scanning for 'better' open networks.",
                impact="low"
            ),
        ]
    ),
    
    # POWER MANAGEMENT (5 commands)
    ADBCategoryModel(
        id="power_management",
        name="Power Management",
        description="Control adaptive battery and background app restrictions",
        impact="low",
        commands=[
            ADBCommandModel(
                name="Intelligent Sleep Mode",
                description="Sensor-based sleep control",
                enable_cmd="shell settings put system intelligent_sleep_mode 1",
                disable_cmd="shell settings put system intelligent_sleep_mode 0",
                get_cmd="shell settings get system intelligent_sleep_mode",
                explanation="Disabling sensor checks can save minor CPU overhead.",
                impact="low"
            ),
            ADBCommandModel(
                name="Adaptive Sleep",
                description="Screen attention settings",
                enable_cmd="shell settings put secure adaptive_sleep 1",
                disable_cmd="shell settings put secure adaptive_sleep 0",
                get_cmd="shell settings get secure adaptive_sleep",
                explanation="Controls whether the screen stays on only when you look at it.",
                impact="low"
            ),
            ADBCommandModel(
                name="App Restrictions",
                description="Aggressively limit background apps",
                enable_cmd="shell settings put global app_restriction_enabled true",
                disable_cmd="shell settings put global app_restriction_enabled false",
                get_cmd="shell settings get global app_restriction_enabled",
                explanation="Forces background processes to sleep faster to save battery.",
                impact="low"
            ),
            ADBCommandModel(
                name="Automatic Power Save",
                description="Force-disable auto power save activation",
                enable_cmd="shell settings put global automatic_power_save_mode 1",
                disable_cmd="shell settings put global automatic_power_save_mode 0",
                get_cmd="shell settings get global automatic_power_save_mode",
                explanation="Allows keeping device at full speed even on low battery.",
                impact="low"
            ),
            ADBCommandModel(
                name="Adaptive Battery Management",
                description="Device learning battery optimization",
                enable_cmd="shell settings put global adaptive_battery_management_enabled 1",
                disable_cmd="shell settings put global adaptive_battery_management_enabled 0",
                get_cmd="shell settings get global adaptive_battery_management_enabled",
                explanation="Controls the AI-based battery management algorithm.",
                impact="low"
            ),
        ]
    )
]

def get_categories_json():
    """Serialize categories for API usage"""
    return [cat.model_dump() for cat in COMMAND_CATEGORIES]
