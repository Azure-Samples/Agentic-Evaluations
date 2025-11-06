"""
HTTP client for chat requests
"""
import requests


def chat_http_request(base_url: str, message: str, session_id: str):
    """Send a chat request and return the response"""
    try:
        response = requests.post(
            f"{base_url}/chat",
            json={"message": message, "session_id": session_id},
            timeout=70
        )
        if response.status_code == 200:
            return response.json()["response"]
        else:
            return f"Error {response.status_code}: {response.text}"
    except Exception as e:
        return f"Error: {e}"
