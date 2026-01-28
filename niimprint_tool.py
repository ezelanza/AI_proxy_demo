#!/usr/bin/env python3
"""
Niimprint Direct Tool - Simple CLI for Niimbot Label Printers

This is a standalone Python tool that can be called directly by agents or scripts.
Unlike the MCP server, this doesn't require a persistent background process.

Usage:
    python niimprint_tool.py print --image label.png --model b21
    python niimprint_tool.py info --model b21 --info-type battery
    python niimprint_tool.py status --model b21
    python niimprint_tool.py rfid --model b21
    python niimprint_tool.py list-ports
"""

import argparse
import base64
import io
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

try:
    from PIL import Image
    from niimprint import BluetoothTransport, PrinterClient, SerialTransport
    from niimprint.printer import InfoEnum
    NIIMPRINT_AVAILABLE = True
except ImportError as e:
    NIIMPRINT_AVAILABLE = False
    print(f"Error: Required libraries not installed: {e}")
    print("Run: ./install.sh")
    sys.exit(1)

# BeeAI Framework imports (only needed when used as a tool)
try:
    from beeai_framework.context import RunContext
    from beeai_framework.emitter import Emitter
    from beeai_framework.tools import JSONToolOutput, Tool, ToolRunOptions
    from pydantic import BaseModel, Field
    BEEAI_AVAILABLE = True
except ImportError:
    BEEAI_AVAILABLE = False


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


def cmd_print(args):
    """Print an image to the printer."""
    model = args.model.lower()
    conn_type = args.connection.lower()
    address = args.address
    density = args.density
    rotation = args.rotation
    
    # Validate density for model
    max_density = get_max_density_for_model(model)
    if density > max_density:
        print(f"Warning: Density adjusted to {max_density} for model {model}")
        density = max_density
    
    # Load image
    if args.image:
        if not Path(args.image).exists():
            return {"error": f"Image file not found: {args.image}"}
        image = Image.open(args.image)
    elif args.image_base64:
        image_data = base64.b64decode(args.image_base64)
        image = Image.open(io.BytesIO(image_data))
    else:
        return {"error": "Either --image or --image-base64 must be provided"}
    
    # Rotate image if requested
    if rotation != 0:
        image = image.rotate(-rotation, expand=True)
    
    # Validate image width
    max_width = get_max_width_for_model(model)
    if image.width > max_width:
        return {
            "error": f"Image width ({image.width}px) exceeds maximum for {model.upper()} ({max_width}px)"
        }
    
    # Create transport and printer client
    try:
        transport = create_transport(conn_type, address)
        printer = PrinterClient(transport)
        
        # Print image
        printer.print_image(image, density=density)
        
        return {
            "success": True,
            "message": f"Printed {image.width}x{image.height}px image to {model.upper()}",
            "image_size": {"width": image.width, "height": image.height},
            "model": model.upper(),
            "density": density
        }
    except Exception as e:
        return {"error": str(e)}


def cmd_info(args):
    """Get printer information."""
    model = args.model.lower()
    conn_type = args.connection.lower()
    address = args.address
    info_type = args.info_type.upper()
    
    # Map info_type to InfoEnum
    info_enum_map = {
        "DENSITY": InfoEnum.DENSITY,
        "PRINTSPEED": InfoEnum.PRINTSPEED,
        "LABELTYPE": InfoEnum.LABELTYPE,
        "LANGUAGETYPE": InfoEnum.LANGUAGETYPE,
        "AUTOSHUTDOWNTIME": InfoEnum.AUTOSHUTDOWNTIME,
        "DEVICETYPE": InfoEnum.DEVICETYPE,
        "SOFTVERSION": InfoEnum.SOFTVERSION,
        "BATTERY": InfoEnum.BATTERY,
        "DEVICESERIAL": InfoEnum.DEVICESERIAL,
        "HARDVERSION": InfoEnum.HARDVERSION,
    }
    
    if info_type not in info_enum_map:
        return {"error": f"Invalid info_type: {info_type}"}
    
    try:
        transport = create_transport(conn_type, address)
        printer = PrinterClient(transport)
        info_value = printer.get_info(info_enum_map[info_type])
        
        return {
            "success": True,
            "info_type": info_type,
            "value": info_value,
            "model": model.upper()
        }
    except Exception as e:
        return {"error": str(e)}


def cmd_rfid(args):
    """Get RFID information."""
    model = args.model.lower()
    conn_type = args.connection.lower()
    address = args.address
    
    try:
        transport = create_transport(conn_type, address)
        printer = PrinterClient(transport)
        rfid_info = printer.get_rfid()
        
        if rfid_info is None:
            return {"success": True, "rfid_detected": False}
        
        return {
            "success": True,
            "rfid_detected": True,
            "uuid": rfid_info['uuid'],
            "barcode": rfid_info['barcode'],
            "serial": rfid_info['serial'],
            "used_length_mm": rfid_info['used_len'],
            "total_length_mm": rfid_info['total_len'],
            "type": rfid_info['type']
        }
    except Exception as e:
        return {"error": str(e)}


def cmd_status(args):
    """Get printer status."""
    model = args.model.lower()
    conn_type = args.connection.lower()
    address = args.address
    
    try:
        transport = create_transport(conn_type, address)
        printer = PrinterClient(transport)
        status = printer.heartbeat()
        
        return {
            "success": True,
            "closing_state": status.get("closingstate"),
            "power_level": status.get("powerlevel"),
            "paper_state": status.get("paperstate"),
            "rfid_read_state": status.get("rfidreadstate"),
            "model": model.upper()
        }
        
    except Exception as e:
        return {"error": str(e)}


def cmd_list_ports(args):
    """List available serial ports."""
    from serial.tools.list_ports import comports as list_comports
    
    try:
        ports = list(list_comports())
        
        if not ports:
            return {"success": True, "ports": []}
        
        port_list = []
        for port, desc, hwid in ports:
            port_list.append({
                "port": port,
                "description": desc,
                "hardware_id": hwid
            })
        
        return {"success": True, "ports": port_list}
    except Exception as e:
        return {"error": str(e)}


# ============================================================================
# BeeAI Tool Class (for agent integration)
# ============================================================================

if BEEAI_AVAILABLE:
    class PrintImageInput(BaseModel):
        """Input schema for printing images."""
        image_path: str = Field(description="Absolute path to the image file to print")
        model: str = Field(description="Printer model: b1, b18, b21, d11, or d110", default="b21")
        density: int = Field(description="Print density from 1 to 5 (higher = darker)", default=5, ge=1, le=5)
        rotation: int = Field(description="Image rotation in degrees: 0, 90, 180, or 270", default=0)
        connection: str = Field(description="Connection type: usb or bluetooth", default="usb")
        address: str | None = Field(
            description="Bluetooth MAC address or serial port. Leave empty for USB auto-detection.",
            default=None
        )


    class PrintImageTool(Tool[PrintImageInput, ToolRunOptions, JSONToolOutput]):
        """Simple tool for printing images to Niimbot printers."""
        
        name = "PrintImage"
        description = (
            "Print an image to a Niimbot label printer. "
            "Supports B1, B18, B21, D11, D110 models via USB or Bluetooth. "
            "Max width: B-series: 384px (48mm), D-series: 96px (12mm). "
            "Resolution: 8 pixels/mm (203 DPI)."
        )
        input_schema = PrintImageInput
        
        def __init__(self, script_path: str | None = None, options: dict[str, Any] | None = None) -> None:
            super().__init__(options)
            self.script_path = script_path or str(Path(__file__).resolve())
        
        def _create_emitter(self) -> Emitter:
            return Emitter.root().child(
                namespace=["tool", "niimprint", "print"],
                creator=self,
            )
        
        async def _run(
            self,
            input: PrintImageInput,
            options: ToolRunOptions | None,
            context: RunContext
        ) -> JSONToolOutput:
            """Execute the print command."""
            import asyncio
            
            cmd = [
                "python", self.script_path, "--json", "print",
                "--model", input.model,
                "--connection", input.connection,
                "--image", input.image_path,
                "--density", str(input.density),
                "--rotation", str(input.rotation)
            ]
            
            if input.address:
                cmd.extend(["--address", input.address])
            
            try:
                # Use async subprocess with timeout (printing can take time)
                proc = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30.0)
                
                stdout_text = stdout.decode()
                stderr_text = stderr.decode()
                
                # Log the raw output for debugging
                if proc.returncode != 0:
                    error_output = stderr_text or stdout_text
                    return JSONToolOutput({
                        "error": error_output,
                        "success": False,
                        "command": " ".join(cmd),
                        "returncode": proc.returncode
                    })
                
                output_data = json.loads(stdout_text)
                # Add debug info to successful prints too
                if not output_data.get("success"):
                    output_data["command"] = " ".join(cmd)
                    output_data["stdout"] = stdout_text
                    output_data["stderr"] = stderr_text
                return JSONToolOutput(output_data)
                
            except asyncio.TimeoutError:
                return JSONToolOutput({
                    "error": "Print command timed out after 30 seconds",
                    "success": False,
                    "command": " ".join(cmd),
                    "suggestion": "Printing took too long. Check if printer is responding."
                })
            except json.JSONDecodeError as e:
                return JSONToolOutput({
                    "error": f"Failed to parse JSON output: {str(e)}",
                    "raw_stdout": stdout_text if 'stdout_text' in locals() else "No output",
                    "raw_stderr": stderr_text if 'stderr_text' in locals() else "No error",
                    "command": " ".join(cmd),
                    "success": False
                })
            except Exception as e:
                return JSONToolOutput({
                    "error": f"Unexpected error: {str(e)}",
                    "error_type": type(e).__name__,
                    "command": " ".join(cmd),
                    "success": False
                })


    class GetPrinterStatusInput(BaseModel):
        """Input schema for getting printer status."""
        model: str = Field(description="Printer model: b1, b18, b21, d11, or d110", default="b21")
        connection: str = Field(description="Connection type: usb or bluetooth", default="usb")
        address: str | None = Field(
            description="Bluetooth MAC address or serial port. Leave empty for USB auto-detection.",
            default=None
        )


    class GetPrinterStatusTool(Tool[GetPrinterStatusInput, ToolRunOptions, JSONToolOutput]):
        """Tool for checking printer status and connectivity."""
        
        name = "GetPrinterStatus"
        description = (
            "Check if the Niimbot printer is connected and get its status. "
            "Returns paper state, power level, cover state. Use this to verify printer connectivity."
        )
        input_schema = GetPrinterStatusInput
        
        def __init__(self, script_path: str | None = None, options: dict[str, Any] | None = None) -> None:
            super().__init__(options)
            self.script_path = script_path or str(Path(__file__).resolve())
        
        def _create_emitter(self) -> Emitter:
            return Emitter.root().child(
                namespace=["tool", "niimprint", "status"],
                creator=self,
            )
        
        async def _run(
            self,
            input: GetPrinterStatusInput,
            options: ToolRunOptions | None,
            context: RunContext
        ) -> JSONToolOutput:
            """Execute the status command."""
            import asyncio
            
            cmd = [
                "python", self.script_path, "--json", "status",
                "--model", input.model,
                "--connection", input.connection
            ]
            
            if input.address:
                cmd.extend(["--address", input.address])
            
            try:
                proc = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=15.0)
                
                if proc.returncode != 0:
                    error_output = stderr.decode() or stdout.decode()
                    return JSONToolOutput({"error": error_output, "success": False})
                
                output_data = json.loads(stdout.decode())
                return JSONToolOutput(output_data)
            except (asyncio.TimeoutError, json.JSONDecodeError, Exception) as e:
                return JSONToolOutput({"error": str(e), "success": False})


    class ListSerialPortsInput(BaseModel):
        """Input schema for listing serial ports."""
        pass


    class ListSerialPortsTool(Tool[ListSerialPortsInput, ToolRunOptions, JSONToolOutput]):
        """Tool for listing available serial ports."""
        
        name = "ListSerialPorts"
        description = (
            "List all available USB serial ports on the system. "
            "Use this to find the printer's port when connecting via USB."
        )
        input_schema = ListSerialPortsInput
        
        def __init__(self, script_path: str | None = None, options: dict[str, Any] | None = None) -> None:
            super().__init__(options)
            self.script_path = script_path or str(Path(__file__).resolve())
        
        def _create_emitter(self) -> Emitter:
            return Emitter.root().child(
                namespace=["tool", "niimprint", "list_ports"],
                creator=self,
            )
        
        async def _run(
            self,
            input: ListSerialPortsInput,
            options: ToolRunOptions | None,
            context: RunContext
        ) -> JSONToolOutput:
            """Execute the list-ports command."""
            import asyncio
            
            cmd = ["python", self.script_path, "--json", "list-ports"]
            
            try:
                proc = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=10.0)
                
                if proc.returncode != 0:
                    error_output = stderr.decode() or stdout.decode()
                    return JSONToolOutput({"error": error_output, "success": False})
                
                output_data = json.loads(stdout.decode())
                return JSONToolOutput(output_data)
            except (asyncio.TimeoutError, json.JSONDecodeError, Exception) as e:
                return JSONToolOutput({"error": str(e), "success": False})


    class GetPrinterInfoInput(BaseModel):
        """Input schema for getting printer information."""
        info_type: str = Field(
            description="Type of info: battery, softversion, hardversion, deviceserial, devicetype, density, printspeed, labeltype"
        )
        model: str = Field(description="Printer model: b1, b18, b21, d11, or d110", default="b21")
        connection: str = Field(description="Connection type: usb or bluetooth", default="usb")
        address: str | None = Field(
            description="Bluetooth MAC address or serial port. Leave empty for USB auto-detection.",
            default=None
        )


    class CheckConnectionInput(BaseModel):
        """Input schema for checking printer connection."""
        pass


    class CheckConnectionTool(Tool[CheckConnectionInput, ToolRunOptions, JSONToolOutput]):
        """Tool for checking if printer is connected and ready."""
        
        name = "CheckConnection"
        description = (
            "Check if the printer is connected and responding. "
            "Use this to verify printer is ready before attempting to print."
        )
        input_schema = CheckConnectionInput
        
        def __init__(self, script_path: str | None = None, options: dict[str, Any] | None = None) -> None:
            super().__init__(options)
            self.script_path = script_path or str(Path(__file__).resolve())
        
        def _create_emitter(self) -> Emitter:
            return Emitter.root().child(
                namespace=["tool", "niimprint", "check_connection"],
                creator=self,
            )
        
        async def _run(
            self,
            input: CheckConnectionInput,
            options: ToolRunOptions | None,
            context: RunContext
        ) -> JSONToolOutput:
            """Check printer connection."""
            # Get printer config from environment
            import os
            import asyncio
            
            printer_model = os.getenv("PRINTER_MODEL", "b1")
            printer_port = os.getenv("PRINTER_PORT", "/dev/cu.B1-H917122400")
            
            # Try to get device info to test if printer responds
            cmd = [
                "python", self.script_path, "--json", "info",
                "--model", printer_model,
                "--address", printer_port,
                "--info-type", "devicetype"
            ]
            
            try:
                # Use async subprocess with timeout
                proc = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=15.0)
                
                if proc.returncode != 0:
                    return JSONToolOutput({
                        "connected": False,
                        "error": "Could not communicate with printer",
                        "suggestion": "Make sure printer is turned ON and USB cable is connected"
                    })
                
                output_data = json.loads(stdout.decode())
                if output_data.get("success"):
                    return JSONToolOutput({
                        "connected": True,
                        "model": printer_model.upper(),
                        "port": printer_port,
                        "status": "Printer is ready"
                    })
                else:
                    error = output_data.get("error", "Unknown error")
                    suggestion = "Make sure printer is turned ON" if "NoneType" in error else "Check printer connection"
                    return JSONToolOutput({
                        "connected": False,
                        "error": error,
                        "suggestion": suggestion
                    })
                    
            except asyncio.TimeoutError:
                return JSONToolOutput({
                    "connected": False,
                    "error": "Connection check timed out",
                    "suggestion": "Printer may be off or not responding. Turn it on and wait 10 seconds."
                })
            except json.JSONDecodeError:
                return JSONToolOutput({
                    "connected": False,
                    "error": "Failed to parse printer response"
                })
            except Exception as e:
                return JSONToolOutput({
                    "connected": False,
                    "error": str(e),
                    "suggestion": "Check printer connection"
                })


    class GetPrinterInfoTool(Tool[GetPrinterInfoInput, ToolRunOptions, JSONToolOutput]):
        """Tool for getting specific printer information."""
        
        name = "GetPrinterInfo"
        description = (
            "Get specific information from the printer like battery level, firmware version, "
            "serial number, or device type. Useful for checking printer details."
        )
        input_schema = GetPrinterInfoInput
        
        def __init__(self, script_path: str | None = None, options: dict[str, Any] | None = None) -> None:
            super().__init__(options)
            self.script_path = script_path or str(Path(__file__).resolve())
        
        def _create_emitter(self) -> Emitter:
            return Emitter.root().child(
                namespace=["tool", "niimprint", "info"],
                creator=self,
            )
        
        async def _run(
            self,
            input: GetPrinterInfoInput,
            options: ToolRunOptions | None,
            context: RunContext
        ) -> JSONToolOutput:
            """Execute the info command."""
            import asyncio
            
            cmd = [
                "python", self.script_path, "--json", "info",
                "--model", input.model,
                "--connection", input.connection,
                "--info-type", input.info_type.lower()
            ]
            
            if input.address:
                cmd.extend(["--address", input.address])
            
            try:
                proc = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=15.0)
                
                if proc.returncode != 0:
                    error_output = stderr.decode() or stdout.decode()
                    return JSONToolOutput({"error": error_output, "success": False})
                
                output_data = json.loads(stdout.decode())
                return JSONToolOutput(output_data)
            except (asyncio.TimeoutError, json.JSONDecodeError, Exception) as e:
                return JSONToolOutput({"error": str(e), "success": False})


def main():
    parser = argparse.ArgumentParser(
        description="Niimprint Direct Tool - Control Niimbot Label Printers",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Print a label:
    %(prog)s print --image label.png --model b21 --density 5
  
  Check battery:
    %(prog)s info --model b21 --info-type battery
  
  Get printer status:
    %(prog)s status --model b21
  
  Read RFID tag:
    %(prog)s rfid --model b21
  
  List USB ports:
    %(prog)s list-ports
        """
    )
    
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output results in JSON format'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Print command
    print_parser = subparsers.add_parser('print', help='Print an image')
    print_parser.add_argument('--model', required=True, choices=['b1', 'b18', 'b21', 'd11', 'd110'],
                             help='Printer model')
    print_parser.add_argument('--connection', default='usb', choices=['usb', 'bluetooth'],
                             help='Connection type')
    print_parser.add_argument('--address', help='Bluetooth MAC or serial port path')
    print_parser.add_argument('--image', help='Path to image file')
    print_parser.add_argument('--image-base64', help='Base64 encoded image')
    print_parser.add_argument('--density', type=int, default=5, choices=range(1, 6),
                             help='Print density (1-5)')
    print_parser.add_argument('--rotation', type=int, default=0, choices=[0, 90, 180, 270],
                             help='Image rotation (degrees clockwise)')
    
    # Info command
    info_parser = subparsers.add_parser('info', help='Get printer information')
    info_parser.add_argument('--model', required=True, choices=['b1', 'b18', 'b21', 'd11', 'd110'])
    info_parser.add_argument('--connection', default='usb', choices=['usb', 'bluetooth'])
    info_parser.add_argument('--address', help='Bluetooth MAC or serial port path')
    info_parser.add_argument('--info-type', required=True,
                            choices=['density', 'printspeed', 'labeltype', 'languagetype',
                                   'autoshutdowntime', 'devicetype', 'softversion', 'battery',
                                   'deviceserial', 'hardversion'],
                            help='Type of information to retrieve')
    
    # RFID command
    rfid_parser = subparsers.add_parser('rfid', help='Read RFID tag')
    rfid_parser.add_argument('--model', required=True, choices=['b1', 'b18', 'b21', 'd11', 'd110'])
    rfid_parser.add_argument('--connection', default='usb', choices=['usb', 'bluetooth'])
    rfid_parser.add_argument('--address', help='Bluetooth MAC or serial port path')
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Get printer status')
    status_parser.add_argument('--model', required=True, choices=['b1', 'b18', 'b21', 'd11', 'd110'])
    status_parser.add_argument('--connection', default='usb', choices=['usb', 'bluetooth'])
    status_parser.add_argument('--address', help='Bluetooth MAC or serial port path')
    
    # List ports command
    subparsers.add_parser('list-ports', help='List available serial ports')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Execute command
    if args.command == 'print':
        result = cmd_print(args)
    elif args.command == 'info':
        result = cmd_info(args)
    elif args.command == 'rfid':
        result = cmd_rfid(args)
    elif args.command == 'status':
        result = cmd_status(args)
    elif args.command == 'list-ports':
        result = cmd_list_ports(args)
    else:
        result = {"error": f"Unknown command: {args.command}"}
    
    # Output result
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        if "error" in result:
            print(f"Error: {result['error']}")
            sys.exit(1)
        elif result.get("success"):
            if args.command == 'print':
                print(f"✓ {result['message']}")
            elif args.command == 'info':
                print(f"{result['info_type']}: {result['value']}")
            elif args.command == 'rfid':
                if result['rfid_detected']:
                    print(f"RFID Tag Detected:")
                    print(f"  UUID: {result['uuid']}")
                    print(f"  Barcode: {result['barcode']}")
                    print(f"  Serial: {result['serial']}")
                    print(f"  Used: {result['used_length_mm']}mm / {result['total_length_mm']}mm")
                else:
                    print("No RFID tag detected")
            elif args.command == 'status':
                print(f"Printer Status:")
                if result['closing_state'] is not None:
                    print(f"  Closing State: {result['closing_state']}")
                if result['power_level'] is not None:
                    print(f"  Power Level: {result['power_level']}")
                if result['paper_state'] is not None:
                    print(f"  Paper State: {result['paper_state']}")
                if result['rfid_read_state'] is not None:
                    print(f"  RFID State: {result['rfid_read_state']}")
            elif args.command == 'list-ports':
                if result['ports']:
                    print("Available Serial Ports:")
                    for port in result['ports']:
                        print(f"  {port['port']}: {port['description']}")
                else:
                    print("No serial ports detected")
        else:
            print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
