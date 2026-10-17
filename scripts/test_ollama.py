import httpx
import json

def test():
    print("Testing connection to http://localhost:11434...")
    try:
        r = httpx.get("http://localhost:11434/api/tags", timeout=5.0)
        models = [m["name"] for m in r.json().get("models", [])]
        print("Available models in Ollama:", models)
        
        target_model = "mistral:latest" if "mistral:latest" in models else models[0]
        print(f"Testing inference on model: {target_model}...")
        
        resp = httpx.post(
            "http://localhost:11434/api/chat",
            json={
                "model": target_model,
                "messages": [
                    {"role": "system", "content": "You are an AI assistant. Output valid JSON."},
                    {"role": "user", "content": "Return a JSON object with key 'status' equal to 'ready' and key 'engine' equal to 'ollama'."}
                ],
                "format": "json",
                "stream": False,
            },
            timeout=90.0,
        )
        print("HTTP Status:", resp.status_code)
        content = resp.json()["message"]["content"]
        print("LLM Response:\n", content)
        parsed = json.loads(content)
        print("Successfully parsed JSON:", parsed)
        return True
    except Exception as e:
        print("Error during Ollama test:", e)
        return False

if __name__ == "__main__":
    test()

