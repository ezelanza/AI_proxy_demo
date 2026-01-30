from beeai_framework.tools.tool import Tool
from beeai_framework.tools import JSONToolOutput
from beeai_framework.emitter import Emitter
from pydantic import BaseModel, Field
import requests
import json
import os
import sys
from PIL import Image, ImageDraw, ImageFont
import base64
import io
import textwrap

# Constants
GATEWAY_URL = "http://nginx:80"

# --- Analyze Complexity Logic (Standalone) ---
def analyze_complexity_logic(query: str) -> str:
    # ... (Keep logic)
    try:
        from openai import OpenAI
        client = OpenAI(
            base_url=f"{GATEWAY_URL}/v1",
            api_key="sk-dummy-key",
            default_headers={"X-User": "agent-user"}
        )
        
        response = client.chat.completions.create(
            model="LLM_MODEL", 
            messages=[
                {
                    "role": "system",
                    "content": "Analyze query complexity. Return ONLY one character: 'S' (simple/greeting), 'M' (medium), or 'C' (complex/reasoning)."
                },
                {
                    "role": "user",
                    "content": query
                }
            ],
            max_tokens=5,
            temperature=0.1
        )
        
        content = response.choices[0].message.content.strip().upper()
        marker = "S" 
        if "COMPLEX" in content or " C" in content or content == "C": marker = "C"
        elif "MEDIUM" in content or " M" in content or content == "M": marker = "M"
        else:
            if len(query.split()) > 10: marker = "M"
            else: marker = "S"
        
        return f"[COMPLEXITY:{marker}]"

    except Exception as e:
        print(f"[AnalyzeComplexity] Error: {e}", file=sys.stderr, flush=True)
        return "[COMPLEXITY:M]"

# --- Call VLM Tool ---
class CallVLMInput(BaseModel):
    image_path: str = Field(description="The path to the image file to analyze.")
    prompt: str = Field(description="The prompt to guide the VLM analysis.", default="What is in this image? Provide a brief description.")

class CallVLMTool(Tool):
    name = "CallVLM"
    description = "Sends an image file to a Vision Language Model (VLM) for analysis."
    input_schema = CallVLMInput

    def _create_emitter(self) -> Emitter:
        return Emitter.root()

    async def _run(self, input: CallVLMInput, options=None, context=None):
        print(f"[DEBUG] CallVLMTool._run invoked with path: {input.image_path}", flush=True)
        try:
            image_full_path = os.path.join("/app/images", input.image_path)
            if not os.path.exists(image_full_path):
                 if os.path.exists(input.image_path):
                     image_full_path = input.image_path
                 else:
                    err = f"Image file not found at {input.image_path}"
                    print(f"[DEBUG] CallVLMTool Error: {err}", flush=True)
                    return JSONToolOutput({"error": err})

            # Read and encode to Data URL
            print(f"[DEBUG] Reading image from {image_full_path}", flush=True)
            with open(image_full_path, "rb") as img_file:
                b64_data = base64.b64encode(img_file.read()).decode('utf-8')
            
            ext = os.path.splitext(image_full_path)[1].lower().replace('.', '')
            if ext == "jpg": ext = "jpeg"
            if not ext: ext = "jpeg"
            data_url = f"data:image/{ext};base64,{b64_data}"

            from openai import OpenAI
            client = OpenAI(
                base_url=f"{GATEWAY_URL}/v1",
                api_key="sk-dummy-key",
                default_headers={"X-User": "agent-user"}
            )
            
            print(f"[DEBUG] Sending VLM Request via OpenAI Client...", flush=True)
            response = client.chat.completions.create(
                model="LLM_MODEL", # NGINX rewrites this to gpt-4o based on complexity
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text", 
                                "text": f"[COMPLEXITY:M] {input.prompt}"
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": data_url
                                }
                            }
                        ]
                    }
                ],
                max_tokens=300,
            )
            
            desc = response.choices[0].message.content
            print(f"[DEBUG] VLM Success. Description: {desc[:50]}...", flush=True)
            return JSONToolOutput({"description": desc})

        except Exception as e:
            print(f"[DEBUG] CallVLMTool Exception: {e}", flush=True)
            return JSONToolOutput({"error": str(e)})

# --- Call Agent Tool ---
class CallAgentInput(BaseModel):
    agent_type: str = Field(description="The type of agent to call: 'creative' or 'fun'.")
    context: str = Field(description="The context or information to provide to the agent.")

class CallAgentTool(Tool):
    name = "CallAgent"
    description = "Calls a specialized agent (Creative or Fun) to get specialized feedback."
    input_schema = CallAgentInput

    def _create_emitter(self) -> Emitter:
        return Emitter.root()

    async def _run(self, input: CallAgentInput, options=None, context=None):
        print(f"[DEBUG] CallAgentTool._run invoked for {input.agent_type}", flush=True)
        endpoint = f"{GATEWAY_URL}/agent/{input.agent_type.lower()}/analyze"
        try:
            response = requests.post(
                endpoint,
                json={"description": input.context},
                headers={"X-User": "agent-user"}
            )
            response.raise_for_status()
            return JSONToolOutput(response.json())
        except Exception as e:
            print(f"[DEBUG] CallAgentTool Error: {e}", flush=True)
            return JSONToolOutput({"error": str(e), "endpoint": endpoint})

# --- Print Label Tool ---
class PrintLabelInput(BaseModel):
    content: str = Field(description="The text content to print on the label.")
    image_path: str = Field(description="Optional path to an image file to print. If provided, prints image.", default=None)

class PrintLabelTool(Tool):
    name = "PrintLabel"
    description = "Prints a label with the given content or image."
    input_schema = PrintLabelInput

    def _create_emitter(self) -> Emitter:
        return Emitter.root()

    async def _run(self, input: PrintLabelInput, options=None, context=None):
        print(f"[DEBUG] PrintLabelTool._run invoked. Content: '{input.content}', Image Path: '{input.image_path}'", flush=True)
        bridge_url = "http://host.docker.internal:8001/print"
        
        payload = {}
        try:
            payload["model"] = os.environ.get("PRINTER_MODEL", "b1")
            address = os.environ.get("PRINTER_ADDRESS")
            if address:
                payload["address"] = address
            
            # Set paper type for 50x30mm labels (T50*30)
            # Type 1 = small (50x15mm), Type 2 = medium (50x30mm), Type 3 = large
            payload["paper_type"] = 2

            img_to_save = None

            if input.image_path:
                image_full_path = os.path.join("/app/images", input.image_path)
                if not os.path.exists(image_full_path) and os.path.exists(input.image_path):
                    image_full_path = input.image_path
                    
                if os.path.exists(image_full_path):
                    with Image.open(image_full_path) as img:
                        if img.mode != '1':
                            img = img.convert('1')
                        buffered = io.BytesIO()
                        img.save(buffered, format="PNG")
                        b64_data = base64.b64encode(buffered.getvalue()).decode('utf-8')
                        img_to_save = img.copy()
                        
                    payload["image_base64"] = b64_data
                else:
                     return JSONToolOutput({"status": "error", "message": f"Image not found: {input.image_path}"})
            else:
                # Render Text to Image with proper word wrapping
                img = Image.new('RGB', (300, 100), color=(255, 255, 255))
                d = ImageDraw.Draw(img)
                try:
                    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 22)
                except:
                    font = ImageFont.load_default()
                
                # Word wrap the text properly (no cutting words)
                import textwrap
                lines = textwrap.wrap(input.content, width=20)
                
                # Draw up to 2 lines
                y_position = 25
                for i, line in enumerate(lines[:2]):
                    d.text((10, y_position), line, fill=(0, 0, 0), font=font)
                    y_position += 35
                
                # Save for debugging
                debug_path = "/app/images/last_printed_label.png"
                img.save(debug_path)
                print(f"[DEBUG] Saved generated label to {debug_path}", flush=True)
                
                buffered = io.BytesIO()
                img.save(buffered, format="PNG")
                b64_data = base64.b64encode(buffered.getvalue()).decode('utf-8')
                payload["image_base64"] = b64_data
                payload["model"] = os.environ.get("PRINTER_MODEL", "b1")

            response = requests.post(bridge_url, json=payload, timeout=30)
            if response.status_code == 200:
                print(f"[DEBUG] Print Success", flush=True)
                return JSONToolOutput({"status": "success", "message": "Label printed successfully"})
            else:
                print(f"[DEBUG] Print Bridge Error: {response.status_code} {response.text}", flush=True)
                return JSONToolOutput({"status": "error", "message": f"Bridge returned {response.status_code}: {response.text}"})
        except Exception as e:
            print(f"[DEBUG] Print Tool Exception: {e}", flush=True)
            return JSONToolOutput({"status": "error", "message": f"Failed to call printer bridge or render image: {str(e)}"})

def _list_available_images():
    images_dir = "/app/images"
    if not os.path.exists(images_dir):
        return []
    valid_extensions = {".png", ".jpg", ".jpeg", ".bmp"}
    return [f for f in os.listdir(images_dir) if os.path.splitext(f)[1].lower() in valid_extensions]
