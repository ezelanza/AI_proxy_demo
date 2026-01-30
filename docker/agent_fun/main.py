from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
from beeai_framework.agents.requirement import RequirementAgent
from beeai_framework.backend import ChatModel
from beeai_framework.memory import UnconstrainedMemory

app = FastAPI()

# Create BeeAI Fun Agent
fun_agent = RequirementAgent(
    name="FunAgent",
    llm=ChatModel.from_name(
        os.environ.get("FUN_AGENT_MODEL", "openai:LLM_model"),
        base_url="http://nginx:80/v1",
        api_key="sk-dummy-key", # NGINX injects the real key
        stream=False,
    ),
    tools=[], 
    memory=UnconstrainedMemory(),
    role="You are a Fun Agent. You are a comedian and a prankster.",
    instructions=[
        "Your goal is to roast, joke about, or find the funny side of the object description.",
        "Provide 3 funny ideas, jokes, or roasts based on the description.",
        "Be witty and humorous.",
        "Format output clearly with 'Fun Ideas:'."
    ]
)

class AgentRequest(BaseModel):
    description: str

@app.post("/analyze")
async def analyze(request: AgentRequest):
    try:
        # Run the agent
        # Force [COMPLEXITY:C] tag so Proxy routes to gpt-4o for better humor
        response = await fun_agent.run(f"[COMPLEXITY:C] Analyze this object description: {request.description}")
        return {"analysis": response.last_message.text, "agent": "fun"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=80)
