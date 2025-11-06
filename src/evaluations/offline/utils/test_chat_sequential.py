"""
Test script to invoke the chat server with sequential POST requests (loop)
"""
import requests

BASE_URL = "http://localhost:8000"

# Batch of test queries
QUERIES = [
    {"message": "What's the weather in New York?", "session_id": "session-1"},
    {"message": "turn on tv", "session_id": "session-2"},
    {"message": "Turn off the bedroom ac", "session_id": "session-2"},
]

def chat_request(message: str, session_id: str):
    """Send a chat request and return the response"""
    try:
        response = requests.post(
            f"{BASE_URL}/chat",
            json={"message": message, "session_id": session_id},
            timeout=70
        )
        if response.status_code == 200:
            return response.json()["response"]
        else:
            return f"Error {response.status_code}: {response.text}"
    except Exception as e:
        return f"Error: {e}"

def main():
    print("Chat Application Test (Sequential)")
    print("=" * 60)
    
    for i, query in enumerate(QUERIES, 1):
        print(f"\n[{i}/{len(QUERIES)}] {query['message']}")
        response = chat_request(query["message"], query["session_id"])
        print(f"→ {response}\n")
    
    print("=" * 60)
    print("All tests completed!")

if __name__ == "__main__":
    main()
