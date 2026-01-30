from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
from beeai_framework.agents.requirement import RequirementAgent
from beeai_framework.backend import ChatModel
from beeai_framework.memory import UnconstrainedMemory

app = FastAPI()

# Create BeeAI Creative Agent
creative_agent = RequirementAgent(
    name="CreativeAgent",
    llm=ChatModel.from_name(
        os.environ.get("CREATIVE_AGENT_MODEL", "openai:LLM_model"),
        base_url="http://nginx:80/v1",
        api_key="sk-dummy-key", # NGINX injects the real key
        stream=False,
    ),
    tools=[], 
    memory=UnconstrainedMemory(),
    role="You are a Creative Fantasy Agent. You see the world through a lens of magic, wonder, and epic storytelling.",
    instructions=[
        "Your goal is to interpret the object description as if it were an artifact, creature, or scene from a fantasy world.",
        "Provide 3 creative/fantasy ideas or interpretations based on the description.",
        "Use evocative, magical, and descriptive language.",
        "Format output clearly with 'Fantasy Interpretations:'."
    ]
)

class AgentRequest(BaseModel):
    description: str

@app.post("/analyze")
async def analyze(request: AgentRequest):
    try:
        # Run the agent
        # Force [COMPLEXITY:C] tag so Proxy routes to gpt-4o for creativity
        response = await creative_agent.run(f"[COMPLEXITY:C] Analyze this object description: {request.description}")
        return {"analysis": response.last_message.text, "agent": "creative"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=80)
