#!/bin/bash
echo "👁‍🗨 LIA // FORENSIC SCAN STARTING..."
echo "------------------------------------"

echo "[1] USB DEVICES (Looking for HID Emulators/Keyloggers):"
lsusb | grep -v "Hub"
echo ""

echo "[2] NON-NATIVE DRIVERS (External kernel modules):"
# Ищем модули, которые загружены не из стандартной директории ядра
lsmod | awk '{print $1}' | xargs modinfo 2>/dev/null | grep -E "filename|author|description" | grep -v "kernel/"
echo ""

echo "[3] NETWORK INTERFACES (Checking for hidden bridges/tunnels):"
ip addr show | grep -E "eth|wlan|tun|tap|bridge"
echo ""

echo "[4] LOADED MODULES WITHOUT SIGNATURE (Stealth check):"
for mod in $(lsmod | tail -n +2 | awk '{print $1}'); do
    if ! modinfo "$mod" | grep -q "signature"; then
        echo "WARNING: Module [$mod] is NOT signed!"
    fi
done

echo "------------------------------------"
echo "SCAN COMPLETE. REPORT BACK TO ARCHITECT."
