#!/bin/bash
# Start printer bridge in background
python3 printer_bridge.py > /dev/null 2>&1 &
echo "Printer Bridge running on http://0.0.0.0:8001 (PID: $!)"
