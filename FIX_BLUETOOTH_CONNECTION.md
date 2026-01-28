# Fix Bluetooth Connection Issue

## The Problem

Your printer port `/dev/cu.B1-H917122400` is a **Bluetooth serial port**, but it's not responding to print commands. This happens when the Bluetooth device is "detected" but not properly "bonded" for communication.

## Solution: Unpair and Re-pair the Printer

### Step 1: Forget the Bluetooth Device

1. Open **System Settings** > **Bluetooth**
2. Find your **Niimbot B1** device (might show as "B1-H917122400")
3. Click the **(i)** or **Options** button next to it
4. Click **Forget This Device** or **Remove**
5. Confirm removal

### Step 2: Turn Off Printer
1. Turn OFF your Niimbot B1 printer
2. Wait 10 seconds

### Step 3: Re-pair the Printer

1. Turn ON the printer
2. Wait for it to boot up (10-15 seconds)
3. In System Settings > Bluetooth:
   - Wait for "B1-XXXXXXXX" to appear
   - Click **Connect**
   - Wait for it to say "Connected"

### Step 4: Test the Connection

```bash
cd /Users/emlanza/Pocket_printer
source venv/bin/activate

# Check what port it's using now
python niimprint_tool.py --json list-ports
```

Look for a port like:
- `/dev/cu.B1-H917122400` or
- `/dev/tty.B1-H917122400`

Update your `.env` file with the correct port.

### Step 5: Try Printing Again

```bash
python niimprint_agent.py
```

## Alternative: Use USB Cable Instead

If Bluetooth keeps failing, **use a USB cable**:

1. Turn off Bluetooth on your Mac
2. Connect printer to computer via USB cable
3. Run: `python niimprint_tool.py --json list-ports`
4. Look for a port like `/dev/cu.usbserial-XXXXX` or `/dev/tty.usbserial-XXXXX`
5. Update `.env` with that port
6. Try printing again

**USB is more reliable than Bluetooth for label printers!**

## Why Is This Happening?

macOS Bluetooth can have "half-connected" states where:
- ✅ Device shows as connected
- ✅ Serial port appears (`/dev/cu.B1-*`)
- ❌ But bidirectional communication doesn't work
- ❌ Commands get sent but no responses received

**Unpairing and re-pairing** establishes a proper Bluetooth Serial Port Profile (SPP) connection.

## Still Not Working?

Try this diagnostic:

```bash
cd /Users/emlanza/Pocket_printer
source venv/bin/activate

# Test Bluetooth connection
python -c "
from niimprint import SerialTransport, PrinterClient
transport = SerialTransport(port='/dev/tty.B1-H917122400')
printer = PrinterClient(transport)
try:
    status = printer.heartbeat()
    print(f'✓ Printer responding: {status}')
except Exception as e:
    print(f'✗ Not responding: {e}')
    print('→ Bluetooth connection is not working properly')
    print('→ Try unpairing and re-pairing, or use USB cable')
"
```

**Expected:**
- ✅ `Printer responding: {...}` = Connection works!
- ❌ `Not responding: NoneType` = Need to unpair/repair or use USB

## Quick Decision Tree

1. **Have USB cable?** → Use USB (most reliable)
2. **No USB cable?** → Unpair and re-pair Bluetooth
3. **Still failing?** → Get a USB cable (they're cheap!)

Bluetooth on label printers can be finicky. USB "just works" 99% of the time.
