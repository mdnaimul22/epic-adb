# ADB Read-Only Commands

## Device Information
```bash
adb shell getprop ro.build.version.release    # Android version
adb shell getprop ro.product.model            # Device model
adb shell getprop ro.product.manufacturer     # Manufacturer
adb shell getprop ro.serialno                 # Serial number
adb shell getprop                             # All system properties
```

## Location
```bash
adb shell dumpsys location | grep "last location" | grep "fused" | head -n 1 | sed -E 's/.*\[fused ([0-9.]+),([0-9.]+).*/\1,\2/'
```

## Battery
```bash
adb shell dumpsys battery                     # Full battery info
adb shell dumpsys battery | grep level        # Battery level only
adb shell dumpsys battery | grep temperature  # Battery temperature
```

## Network
```bash
adb shell ip addr show wlan0                  # IP address
adb shell dumpsys wifi | grep -E "mWifiInfo|SSID"  # WiFi info
adb shell dumpsys connectivity                # Network status
```

## Display
```bash
adb shell wm size                             # Screen resolution
adb shell wm density                          # Screen density
adb shell dumpsys display | grep mScreenState # Screen on/off status
```

## Memory & CPU
```bash
adb shell cat /proc/meminfo                   # Memory info
adb shell cat /proc/cpuinfo                   # CPU info
adb shell dumpsys meminfo                     # Memory usage
```

## Apps & Processes
```bash
adb shell pm list packages                    # All installed packages
adb shell pm list packages -3                 # Third-party apps only
adb shell dumpsys window | grep mCurrentFocus # Current foreground app
adb shell dumpsys activity services           # Running services
adb shell ps                                  # Running processes
```

## Sensors
```bash
adb shell dumpsys sensorservice               # All sensor data
```

## Telephony
```bash
adb shell dumpsys telephony.registry          # Phone, carrier, signal
adb shell getprop | grep gsm                  # SIM card info
```

## Audio
```bash
adb shell dumpsys audio                       # Audio info & volume levels
```

## Clipboard
```bash
adb shell cmd clipboard get-text              # Current clipboard content
```

## Storage
```bash
adb shell df -h                               # Disk space usage
adb shell ls /sdcard/                         # List files
```

## System Status
```bash
adb shell uptime                              # Device uptime
adb shell date                                # Current date/time
adb shell dumpsys power                       # Power state info
```

## Notifications
```bash
adb shell dumpsys notification                # Recent notifications
```

## Screenshots
```bash
adb shell screencap /sdcard/screenshot.png    # Take screenshot
adb pull /sdcard/screenshot.png               # Download to computer
```