from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from beeai_framework.agents.requirement import RequirementAgent
from beeai_framework.backend import ChatModel
from beeai_framework.memory import UnconstrainedMemory
from supervisor_tools import CallVLMTool, CallAgentTool, PrintLabelTool, _list_available_images, analyze_complexity_logic
from beeai_framework.emitter import Emitter
import os
import json
import sys
import base64
import uuid

class ProcessRequest(BaseModel):
    message: str = None
    image_base64: str = None

app = FastAPI()

IMAGES_DIR = "/app/images"
if not os.path.exists(IMAGES_DIR):
    os.makedirs(IMAGES_DIR)

# Dynamic image list helper
def get_images_section():
    if os.path.exists(IMAGES_DIR):
        available_images = _list_available_images()
        image_list = "\n".join([f"  - {img}" for img in available_images])
        return f"AVAILABLE IMAGES (located in {IMAGES_DIR}):\n{image_list}\n"
    return f"AVAILABLE IMAGES: Check {IMAGES_DIR} directory for image files.\n"

# AGNOSTIC MODEL PLACEHOLDER
AI_MODEL = "LLM_MODEL"

# Instantiate Agent
supervisor_agent = RequirementAgent(
    name="SupervisorAgent",
    llm=ChatModel.from_name(
        f"openai:{AI_MODEL}", 
        base_url="http://nginx:80/v1",
        api_key="sk-dummy-key",
        stream=False,
    ),
    tools=[CallVLMTool(), CallAgentTool(), PrintLabelTool()],
    memory=UnconstrainedMemory(),
    role="You are the Supervisor Agent. You orchestrate the entire labeling process.",
    instructions=[
        "GENERAL INSTRUCTIONS:",
        "  - The user's query complexity has been pre-analyzed and provided as a tag [COMPLEXITY:X] at the start of the message.",
        "  - Use this tag to guide your response style.",
        "  - You may receive a file path for an image in the prompt (e.g. 'File is available at: upload_xyz.png').",
        "  - TRUST this path. Even if it is not in the initial 'Available Images' list, IT EXISTS.",
        "",
        "WORKFLOW 1 - General Chat / Simple Greetings (e.g. 'hello'):",
        "  - Respond politely and directly.",
        "",
        "WORKFLOW 2 - Print Image by Name (e.g. 'print hello world'):",
        "  - Map name to file and use 'PrintLabel' with image_path.",
        "",
        "WORKFLOW 3 - Full Analysis / Fortune Cookie (Default for Images or Descriptions):",
        "  Step 1: IF an image filename is provided, CALL 'CallVLM' tool with that image path.",
        "  Step 2: CALL 'CallAgent' tool with type='creative' and pass the VLM description as context.",
        "  Step 3: CALL 'CallAgent' tool with type='fun' and pass the VLM description as context.",
        "  Step 4: CREATE a short motivational phrase (max 40 chars) using the Creative and Fun responses.",
        "  Step 5: CALL 'PrintLabel' tool with content=<your_phrase> and image_path=''",
        "  Step 6: STOP and return a summary.",
        "  CRITICAL: Keep the phrase VERY SHORT (max 40 characters). After calling PrintLabel, you MUST stop immediately.",
        "IMPORTANT:",
        "  - Always use the output from Creative and Fun agents to craft the final text.",
        "  - STRICT LIMIT: 40 characters max for the printed label text.",
        "  - Keep it SHORT and SIMPLE - words must fit on 2 lines without cutting."
    ]
)

# --- Event Listeners for Debugging ---
@supervisor_agent.emitter.on("start")
async def on_start(event, *args):
    print(f"\n[DEBUG] Agent STARTED processing.", flush=True)

@supervisor_agent.emitter.on("tool_start")
async def on_tool_start(event, *args):
    print(f"\n[DEBUG] Agent CALLING TOOL...", flush=True)
    try:
        if hasattr(event, 'data') and 'tool' in event.data:
             tool_name = event.data['tool'].name
             print(f"  -> Tool: {tool_name}", flush=True)
             if 'input' in event.data:
                 print(f"  -> Input: {event.data['input']}", flush=True)
    except:
        pass

@supervisor_agent.emitter.on("tool_success")
async def on_tool_success(event, *args):
    print(f"\n[DEBUG] Tool Execution SUCCESS.", flush=True)
    try:
        if hasattr(event, 'data') and 'output' in event.data:
             print(f"  -> Output: {event.data['output']}", flush=True)
    except:
        pass

@supervisor_agent.emitter.on("tool_error")
async def on_tool_error(event, *args):
    print(f"\n[DEBUG] Tool Execution FAILED.", flush=True)
    try:
         if hasattr(event, 'data') and 'error' in event.data:
             print(f"  -> Error: {event.data['error']}", flush=True)
    except:
        pass

@app.post("/process")
async def process_image(request: ProcessRequest):
    try:
        # Clear Memory for Stateless Interaction by replacing the memory instance
        try:
             # Try to replace the memory object directly
             supervisor_agent.memory = UnconstrainedMemory()
             print(f"[DEBUG] Memory Replaced with new instance.", flush=True)
        except Exception as mem_err:
             print(f"[DEBUG] Failed to replace memory: {mem_err}", flush=True)


        # Save image if provided
        uploaded_image_path = None
        if request.image_base64:
            try:
                # Create a unique filename for this upload
                filename = f"upload_{uuid.uuid4().hex[:8]}.png"
                file_path = os.path.join(IMAGES_DIR, filename)
                
                with open(file_path, "wb") as f:
                    f.write(base64.b64decode(request.image_base64))
                
                uploaded_image_path = filename
                print(f"[Supervisor] Image saved to {file_path}", flush=True)
            except Exception as e:
                print(f"[Supervisor] Failed to save image: {e}", flush=True)

        # Determine prompt content
        analysis_text = request.message if request.message else "Process image"
        
        message_content = ""
        if uploaded_image_path:
            message_content = f"Process this image. File is available at: {uploaded_image_path}"
            if request.message:
                message_content += f"\nUser Message: {request.message}"
        else:
            message_content = request.message

        if not message_content:
             raise HTTPException(status_code=400, detail="Either image_base64 or message must be provided")

        print(f"\n{'='*60}", flush=True)
        print(f"[Supervisor] New Request Received", flush=True)
        print(f"[Supervisor] User Message: {analysis_text}", flush=True)

        # 1. PRE-PROCESS: Analyze Complexity manually
        if "image" in analysis_text.lower() or uploaded_image_path:
             complexity_tag = "[COMPLEXITY:C]"
        else:
             complexity_tag = analyze_complexity_logic(analysis_text)
             
        print(f"[Supervisor] Complexity Analysis: {complexity_tag}", flush=True)

        # 2. Prepend tag to the prompt
        final_prompt = f"{complexity_tag} {message_content}"
        print(f"[Supervisor] Full Prompt Constructed. Starting Agent...", flush=True)

        # 3. Run Agent
        response = await supervisor_agent.run(final_prompt)
        
        last_message_text = "Processing completed."
        if response and hasattr(response, 'last_message') and response.last_message:
            if hasattr(response.last_message, 'text'):
                last_message_text = response.last_message.text
            elif hasattr(response.last_message, 'content'):
                last_message_text = str(response.last_message.content)
        
        print(f"[Supervisor] Final Response: {last_message_text}", flush=True)
        print(f"{'='*60}\n", flush=True)
        
        return {
            "status": "completed",
            "summary": last_message_text
        }
            
    except Exception as e:
        import traceback
        print(f"[Supervisor] CRITICAL ERROR: {e}\n{traceback.format_exc()}", file=sys.stderr, flush=True)
        raise HTTPException(status_code=500, detail=f"Chat Model error: {str(e)}")

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    print("[Supervisor] Server Starting...", flush=True)
    uvicorn.run(app, host="0.0.0.0", port=80)
