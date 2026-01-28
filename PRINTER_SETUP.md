# Niimbot Printer Setup Guide

## How to Connect Your Printer

### Option 1: USB Connection (Recommended)

1. **Connect the printer via USB cable**
   - Plug the USB cable into your Niimbot printer
   - Connect the other end to your computer

2. **Verify the connection**
   ```bash
   # Run this command to list available ports
   python niimprint_agent.py
   ```
   Then ask: "List available serial ports" or "Check printer status"

3. **Test the connection**
   Ask the agent: "Check if my printer is connected"

### Option 2: Bluetooth Connection

1. **Pair your printer**
   - Turn on the printer
   - Open your system Bluetooth settings
   - Find your Niimbot printer (e.g., "B21-XXXX")
   - Note down the MAC address (e.g., "AA:BB:CC:DD:EE:FF")
   - **Important**: After pairing, DISCONNECT it in system settings
     (The app needs direct Bluetooth access)

2. **Use with the agent**
   When printing, specify the MAC address:
   - "Print /path/to/image.png via bluetooth at AA:BB:CC:DD:EE:FF"

## Agent Capabilities

The agent now has **4 tools** to help you:

### 1. **PrintImage** - Print labels
   - "Print /path/to/label.png"
   - "Print image.png with density 5"
   - "Print label.png rotated 90 degrees"

### 2. **GetPrinterStatus** - Check connection
   - "Check if printer is connected"
   - "Is my printer ready?"
   - "Check printer status"

### 3. **ListSerialPorts** - Find USB ports
   - "List available serial ports"
   - "What USB ports do I have?"
   - "Find my printer port"

### 4. **GetPrinterInfo** - Get printer details
   - "Check battery level"
   - "What's the firmware version?"
   - "Show printer serial number"

## Common Use Cases

### Before Your First Print

1. **Check connection:**
   ```
   You: Check if my printer is connected
   ```

2. **List ports (if needed):**
   ```
   You: List available serial ports
   ```

3. **Check battery:**
   ```
   You: What's the battery level?
   ```

4. **Print a test:**
   ```
   You: Print /Users/me/Desktop/test.png
   ```

### Troubleshooting

#### "No serial ports detected"

On macOS:
- Make sure the USB cable is properly connected
- Try unplugging and reconnecting the printer
- Check if the printer appears in System Information > USB

On Linux:
- Add your user to the dialout group:
  ```bash
  sudo usermod -a -G dialout $USER
  # Log out and back in
  ```

#### "Permission denied on serial port"

```bash
# macOS/Linux
sudo chmod 666 /dev/ttyACM0  # Replace with your port
```

#### Bluetooth not working

1. Make sure printer is paired in system Bluetooth
2. **Disconnect** from system Bluetooth (don't remove pairing)
3. Use the MAC address with the agent
4. Format: "Print image.png via bluetooth at AA:BB:CC:DD:EE:FF"

## Supported Printers

- **Niimbot B1** - 384px width (48mm)
- **Niimbot B18** - 384px width (48mm)
- **Niimbot B21** - 384px width (48mm) ← Most common
- **Niimbot D11** - 96px width (12mm)
- **Niimbot D110** - 96px width (12mm)

## Image Requirements

- **Format**: PNG, JPEG, or any PIL-supported format
- **Width**: 
  - B-series: Max 384 pixels (48mm at 203 DPI)
  - D-series: Max 96 pixels (12mm at 203 DPI)
- **Height**: Any (printer feeds continuous roll)
- **Color**: Will be converted to black & white

## Quick Test

Try these commands in sequence:

```
You: List available serial ports
Agent: [Shows available ports like /dev/ttyACM0]

You: Check printer status
Agent: [Shows printer is connected and ready]

You: Check battery level
Agent: [Shows battery percentage]

You: Print /path/to/your/image.png
Agent: [Prints the label]
```
