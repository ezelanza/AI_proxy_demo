# Niimprint Bee AI Agent

A Bee AI framework agent for controlling Niimbot label printers through natural language.

## Features

- 🖨️ **Print labels** from images (PNG, JPEG, etc.)
- 🔋 **Check printer info** (battery, firmware, serial number)
- 📊 **Get printer status** (paper loaded, cover state, power level)
- 🏷️ **Read RFID tags** from label rolls
- 🔌 **List USB ports** for connection
- 💬 **Natural language interface** powered by Bee AI framework

## Supported Printers

- Niimbot B1 (384px/~48mm width)
- Niimbot B18 (384px/~48mm width)
- Niimbot B21 (384px/~48mm width)
- Niimbot D11 (96px/~12mm width)
- Niimbot D110 (96px/~12mm width)

## Installation

### 1. Install niimprint library

```bash
git clone https://github.com/AndBondStyle/niimprint.git
cd niimprint
pip install -e .
cd ..
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

Create a `.env` file in the project directory:

```bash
cp .env.example .env
```

Then edit `.env` and add your OpenAI API key:

```bash
OPENAI_API_KEY=your_openai_api_key_here
```

The agent uses OpenAI's GPT-4o by default. You can optionally override the model:

```bash
# In .env file
LLM_MODEL=openai:gpt-4o-mini  # Use a different OpenAI model
LLM_MODEL=anthropic:claude-sonnet-4  # Use Anthropic (requires ANTHROPIC_API_KEY)
LLM_MODEL=ollama:granite3.3  # Use local Ollama
```

## Usage

### Interactive Mode

Run the agent in interactive mode:

```bash
python niimprint_agent.py
```

Then chat with it naturally:

```
You: Check the battery level of my B21 printer
Agent: Let me check the battery level... The battery is at 85%.

You: Print /path/to/label.png to my printer
Agent: Printing your image... Done! Successfully printed 240x120px image.

You: What serial ports are available?
Agent: I found these serial ports:
  - /dev/ttyACM0: USB Serial Device
  - /dev/ttyUSB0: FTDI USB Serial
```

### Programmatic Use

Use the agent in your own code:

```python
import asyncio
from niimprint_agent import create_niimprint_agent

async def main():
    # Create agent (uses model from .env or default)
    agent = create_niimprint_agent()
    
    # Or specify a custom model
    agent = create_niimprint_agent(model="openai:gpt-4o-mini")
    
    # Run a task
    response = await agent.run(
        "Print /Users/me/label.png to my B21 printer with density 5"
    )
    
    print(response.last_message.text)

asyncio.run(main())
```

### Direct CLI Tool

You can also use the CLI tool directly without the agent:

```bash
# Print an image
python niimprint_tool.py print --image label.png --model b21 --json

# Check battery
python niimprint_tool.py info --model b21 --info-type battery --json

# List ports
python niimprint_tool.py list-ports --json
```

## Example Prompts

- **"Check if my printer needs charging"** → Uses GetPrinterInfo tool with battery info
- **"Print label.png to my B21 printer"** → Uses PrintImage tool
- **"Is my printer ready to print?"** → Uses GetPrinterStatus tool
- **"What USB ports do I have?"** → Uses ListSerialPorts tool
- **"Read the RFID tag from my label roll"** → Uses GetRFIDInfo tool
- **"Print this image at high density"** → Uses PrintImage with density=5

## Configuration

### LLM Models

The default model is `openai:gpt-4o`. You can override it in your `.env` file:

```bash
# .env
LLM_MODEL=openai:gpt-4o-mini       # OpenAI (default: gpt-4o)
LLM_MODEL=anthropic:claude-sonnet-4  # Anthropic (requires ANTHROPIC_API_KEY)
LLM_MODEL=ollama:granite3.3         # Local Ollama
```

Or set via environment variable at runtime:

```bash
export LLM_MODEL="openai:gpt-4o-mini"
python niimprint_agent.py
```

### Printer Connection

- **USB (default)**: Auto-detects the serial port
- **USB (specific port)**: Specify port in prompt or use `--address /dev/ttyACM0`
- **Bluetooth**: Requires MAC address in prompt or `--address AA:BB:CC:DD:EE:FF`

## Project Structure

```
/Users/emlanza/Pocket_printer/
├── niimprint_agent.py      # Bee AI framework agent
├── niimprint_tool.py       # CLI tool (called by agent)
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables (API keys)
├── .env.example            # Template for .env
└── README.md              # This file
```

## How It Works

1. **User Input**: You provide natural language commands
2. **Agent Processing**: RequirementAgent analyzes the request
3. **Tool Selection**: Agent selects appropriate tool(s)
4. **Tool Execution**: Tools call `niimprint_tool.py` CLI
5. **Result Parsing**: JSON results are processed
6. **Natural Response**: Agent formats response in natural language

## Troubleshooting

### "No serial ports detected"

Run `python niimprint_tool.py list-ports` to see available ports.

On Linux, add your user to the `dialout` group:
```bash
sudo usermod -a -G dialout $USER
# Log out and back in
```

### "Permission denied" on serial port

```bash
sudo chmod 666 /dev/ttyACM0  # Replace with your port
```

### Bluetooth issues

1. Find correct MAC address:
   ```bash
   bluetoothctl
   scan on
   # Note addresses shown
   info AA:BB:CC:DD:EE:FF  # Should show "UUID: Serial Port"
   ```

2. Make sure printer is NOT connected in system Bluetooth settings

### Image too wide

- B1/B18/B21: Max 384px (~48mm)
- D11/D110: Max 96px (~12mm)
- Resolution: 8 pixels per mm (203 DPI)

## Requirements

- Python 3.11+
- Bee AI Framework
- niimprint library
- Niimbot printer (B1/B18/B21/D11/D110)
- OpenAI API key (default) or other LLM provider credentials

## License

MIT License

## Credits

- **niimprint library**: [AndBondStyle/niimprint](https://github.com/AndBondStyle/niimprint)
- **Bee AI Framework**: [i-am-bee/beeai-framework](https://github.com/i-am-bee/beeai-framework)
