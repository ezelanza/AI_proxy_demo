# Print Error: 'NoneType' object has no attribute 'data'

## The Problem

Your printer responds to connection checks but fails when trying to print:
- ✅ CheckConnection works
- ❌ Print fails with `'NoneType' object has no attribute 'data'`

This means the printer connection needs to be "warmed up" for printing operations.

## Quick Fix (Try This First!)

### **Press the FEED button on your printer**

1. Look for the **FEED** button on your Niimbot B1 (usually on top)
2. Press it **once** - this will feed out a blank piece of paper
3. Wait **5-10 seconds**
4. Try printing again: `You: print test`

**Why this works:** The feed button wakes up the printer's print mechanism and establishes a proper connection.

## Alternative Solutions

### Option 1: Power Cycle
1. Turn OFF the printer
2. Wait 10 seconds
3. Turn it back ON
4. Wait 10 seconds
5. Press FEED button once
6. Try printing

### Option 2: Disconnect/Reconnect USB
1. Unplug USB cable
2. Wait 5 seconds
3. Plug it back in
4. Wait 5 seconds
5. Press FEED button once
6. Try printing

### Option 3: Test Print Manually

Test if your printer can print at all:

```bash
cd /Users/emlanza/Pocket_printer
source venv/bin/activate

# After pressing FEED button, try this:
python niimprint_tool.py --json print \
  --model b1 \
  --address /dev/cu.B1-H917122400 \
  --connection usb \
  --image images/test.png \
  --density 5
```

**Expected result:**
```json
{
  "success": true,
  "message": "Printed 384x60px image to B1",
  ...
}
```

## Understanding the Error

The `'NoneType' object has no attribute 'data'` error happens when:
- Printer is detected but print mechanism isn't ready
- Connection exists but data channel isn't established
- Printer needs to be "woken up" with a feed command

## Your Current Status

✅ **Working:**
- Port detected: `/dev/cu.B1-H917122400`
- Printer responds to info queries
- Connection check passes

❌ **Not Working:**
- Print command fails with NoneType error

🔧 **Solution:** Press FEED button to wake up printer!

## Still Not Working?

If pressing FEED doesn't help:

1. **Check paper roll:**
   - Is paper loaded?
   - Is there enough paper?
   - Is cover closed properly?

2. **Check printer state:**
   - Is printer warm (just turned on)?
   - Did you recently use it?
   - Try waiting 1-2 minutes after turning on

3. **Test with smallest image:**
   ```bash
   python niimprint_tool.py print \
     --model b1 \
     --address /dev/cu.B1-H917122400 \
     --image images/test.png
   ```

## Summary

**Most Common Fix:** Press the FEED button on your printer, wait 5 seconds, then try printing again.

The printer needs to "warm up" its print mechanism before it can accept print jobs!
