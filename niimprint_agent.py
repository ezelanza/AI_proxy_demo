#!/usr/bin/env python3
"""
Simple Niimbot Printer Agent - Just Print!

A minimal agent with a single tool for printing labels.
"""

import asyncio
import os
import sys

from dotenv import load_dotenv

from beeai_framework.agents.requirement import RequirementAgent
from beeai_framework.backend import ChatModel
from beeai_framework.memory import UnconstrainedMemory

# Import the tools
from niimprint_tool import PrintImageTool, CheckConnectionTool
from tool.scracthpad import ScratchpadTool

# Load environment variables from .env file
load_dotenv()


# ============================================================================
# Agent Creation
# ============================================================================

def create_niimprint_agent(
    model: str = "openai:gpt-4o"
) -> RequirementAgent:
    """
    Create a simple agent for printing to Niimbot printers.
    
    Args:
        model: LLM model to use (default: "openai:gpt-4o")
    
    Returns:
        Configured RequirementAgent with PrintImage tool
    """
    # Get printer configuration from environment
    printer_model = os.getenv("PRINTER_MODEL", "b1")
    printer_port = os.getenv("PRINTER_PORT", "/dev/cu.B1-H917122400")
    
    # Create agent with all tools
    agent = RequirementAgent(
        name="NiimprintAgent",
        llm=ChatModel.from_name(model, stream=True),
        tools=[CheckConnectionTool(), PrintImageTool(), ScratchpadTool()],
        memory=UnconstrainedMemory(),
        role="You are a helpful assistant that prints labels and remembers things.",
        instructions=[
            f"You have a B1 printer at {printer_port}.",
            "Available images: images/hello_world.png, images/test.png",
            f"ALWAYS use: model='{printer_model}', connection='usb', address='{printer_port}', density=5",
            "When user says 'print test' -> use images/test.png",
            "When user says 'print hello world' -> use images/hello_world.png",
            "BEFORE printing, call CheckConnection tool to verify printer is ready.",
            "Use scratchpad to remember user preferences, names, or anything they tell you.",
            "When user asks to remember something: scratchpad operation='write' content='thing to remember'",
            "To recall what you know: scratchpad operation='read'",
            "If print fails with 'NoneType' error, tell user the suggestion provided.",
        ],
    )
    
    return agent


# ============================================================================
# Main Interactive Loop
# ============================================================================

async def main():
    """Main interactive loop for the agent."""
    print("=" * 60)
    print("Niimbot B1 Printer Agent")
    print("=" * 60)
    print()
    
    # Create agent
    llm_model = os.getenv("LLM_MODEL", "openai:gpt-4o")
    agent = create_niimprint_agent(model=llm_model)
    
    # Check printer connection using the tool
    print("Checking printer connection...")
    response = await agent.run("Check if the printer is connected")
    
    # Parse the response to see if printer is ready
    result_text = response.last_message.text.lower()
    if "not" in result_text or "error" in result_text or "turn on" in result_text:
        print(f"\n{response.last_message.text}")
        print("\n" + "=" * 60)
        print("Cannot start: Printer not ready")
        print("Turn on your printer and try again.")
        print("=" * 60)
        sys.exit(1)
    
    print(f"✓ {response.last_message.text}\n")
    
    print("Try: 'print test' or 'print hello world'")
    print("Type 'quit' to stop.")
    print("=" * 60)
    print()
    print("Agent ready!\n")
    
    # Interactive loop
    while True:
        try:
            user_input = input("You: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ["quit", "exit", "q"]:
                print("Goodbye!")
                break
            
            print("\nAgent: ", end="", flush=True)
            
            # Run agent
            response = await agent.run(user_input)
            
            # Print response
            print(response.last_message.text)
            print()
            
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}")
            print()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nGoodbye!")
        sys.exit(0)
