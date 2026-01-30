import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import base64
import io
from PIL import Image

try:
    from niimprint import SerialTransport, BluetoothTransport, PrinterClient
except ImportError:
    raise ImportError(
        "niimprint library not found. Install it with: "
        "pip install -e ./niimprint  or  pip install git+https://github.com/AndBondStyle/niimprint.git"
    )

# Helper functions for printer models
def get_max_width_for_model(model: str) -> int:
    """Get maximum width in pixels for a printer model."""
    if model in ("b1", "b18", "b21"):
        return 384
    elif model in ("d11", "d110"):
        return 96
    else:
        raise ValueError(f"Unknown printer model: {model}")

def get_max_density_for_model(model: str) -> int:
    """Get maximum density for a printer model."""
    if model in ("b18", "d11", "d110"):
        return 3
    else:
        return 5

def create_transport(conn_type: str, address: str = None):
    """Create a transport connection to the printer."""
    if conn_type == "bluetooth":
        if not address:
            raise ValueError("Bluetooth MAC address is required for bluetooth connection")
        address = address.upper()
        return BluetoothTransport(address)
    elif conn_type == "usb":
        port = address if address else "auto"
        return SerialTransport(port=port)
    else:
        raise ValueError(f"Invalid connection type: {conn_type}")

app = FastAPI(title="Niimbot Printer Bridge")

class PrintRequest(BaseModel):
    image_base64: str
    model: str = "b1"
    connection: str = "usb"
    address: str | None = None
    density: int = 5
    rotation: int = 0
    paper_type: int = 1  # Paper type for label size (1=50x30mm)

@app.post("/print")
async def print_label(request: PrintRequest):
    try:
        # Decode image
        image_data = base64.b64decode(request.image_base64)
        image = Image.open(io.BytesIO(image_data))
        
        # Rotate if needed
        if request.rotation != 0:
            image = image.rotate(-request.rotation, expand=True)
            
        # Validate width
        max_width = get_max_width_for_model(request.model)
        if image.width > max_width:
             aspect_ratio = image.height / image.width
             new_height = int(max_width * aspect_ratio)
             image = image.resize((max_width, new_height), Image.Resampling.LANCZOS)
        
        # Connect
        transport = create_transport(request.connection, request.address)
        printer = PrinterClient(transport)
        
        # Print using standard method
        # Note: This sets label_type(1) which is 50x15mm, so on 50x30mm paper
        # it will only print the top half
        density = min(request.density, get_max_density_for_model(request.model))
        printer.print_image(image, density=density)
        
        return {"status": "success", "message": "Label printed successfully"}
        
    except Exception as e:
        import traceback
        error_msg = f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"
        print(f"[PRINT ERROR] {error_msg}", flush=True)
        raise HTTPException(status_code=500, detail=error_msg)

@app.get("/status")
async def get_status(model: str = "b1", connection: str = "usb", address: str | None = None):
    try:
        transport = create_transport(connection, address)
        printer = PrinterClient(transport)
        status = printer.heartbeat()
        return {"status": "connected", "details": status}
    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    print("Printer Bridge running on http://0.0.0.0:8001")
    # Listen on 0.0.0.0 to allow access from Docker (via host.docker.internal)
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")
