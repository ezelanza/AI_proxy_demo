# Get your Real Fortune trhough AI Proxy

AI-powered label printing system using Docker microservices with NGINX as an AI Gateway.

## Quick Start

1. **Setup Python environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   pip install -e ./niimprint
   ```

2. **Set OpenAI API key:**
   ```bash
   export OPENAI_API_KEY="sk-..."
   ```

3. **Configure printer (if needed):**
   Edit `.env` file:
   ```bash
   PRINTER_ADDRESS=/dev/cu.usbmodemXXX  # Your printer port or leave empty for auto-detect
   PRINTER_MODEL=b1                      # Your printer model: b1, b18, b21, d11, d110
   ```
   Find your printer port: `ls /dev/cu.* | grep -i usb`

4. **Start printer bridge:**
   ```bash
   ./start_printer_bridge.sh
   ```
   Or manually: `python3 printer_bridge.py > /dev/null 2>&1 &`
   You should see: "Printer Bridge running on http://0.0.0.0:8001"

5. **Start Docker services (new terminal):**
   ```bash
   docker-compose up -d --build --quiet-pull
   ```
   Check status: `docker-compose ps`

6. **Chat with supervisor (new terminal):**
   ```bash
   python3 client_test.py
   ```

## Usage Examples

```
You: print hello world
```

Get your phrase fortune with an image as input 
```
You: /image image_input_1.jpeg
```

## Requirements

- Docker & Docker Compose
- Python 3.11+
- Niimbot printer
- OpenAI API key
