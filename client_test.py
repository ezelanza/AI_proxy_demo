import requests
import base64
import sys
import os

URL = "http://localhost:8080/supervisor/process"

def send_message(message=None, image_path=None):
    headers = {"Content-Type": "application/json"}
    payload = {}
    
    if message:
        payload["message"] = message
        
    if image_path:
        if not os.path.exists(image_path):
            print(f"Error: File '{image_path}' not found.")
            return
        try:
            with open(image_path, "rb") as image_file:
                payload["image_base64"] = base64.b64encode(image_file.read()).decode('utf-8')
            print(f"[Client] Sending image: {image_path}")
        except Exception as e:
            print(f"Error reading image: {e}")
            return

    if not payload:
        print("Error: Must provide message or image.")
        return

    try:
        response = requests.post(URL, json=payload, headers=headers, timeout=120)
        if response.status_code == 200:
            result = response.json()
            print(f"\n[Supervisor]: {result.get('summary')}\n")
        else:
            print(f"Error {response.status_code}: {response.text}")
            
    except requests.exceptions.Timeout:
        print("Request timed out (this might be normal for long operations)")
    except Exception as e:
        print(f"Connection error: {e}")

def chat_loop():
    print("="*50)
    print("Supervisor Chat Client")
    print("Commands:")
    print("  /image <path>  - Send an image to process")
    print("  /quit          - Exit")
    print("  <text>         - Send text message")
    print("="*50)
    print("Connected to Supervisor\n")
    
    while True:
        try:
            user_input = input("You: ").strip()
            if not user_input:
                continue
                
            if user_input.lower() in ['/quit', '/exit']:
                break
                
            if user_input.startswith('/image '):
                parts = user_input.split(' ', 1)
                if len(parts) > 1:
                    image_path = parts[1].strip()
                    # msg = input("Add message (optional): ").strip()
                    # User requested to default to motivational phrase
                    msg = "Generate a short motivational phrase based on this image."
                    send_message(message=msg, image_path=image_path)
                else:
                    print("Usage: /image <path/to/image.png>")
            else:
                send_message(message=user_input)
                
        except KeyboardInterrupt:
            print("\nExiting...")
            break

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # One-shot mode for testing
        img = sys.argv[1]
        send_message(image_path=img)
    else:
        chat_loop()
