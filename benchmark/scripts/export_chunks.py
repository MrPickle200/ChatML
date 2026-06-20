import os
import json
from fastapi.testclient import TestClient
from app.main import app

def main():
    client = TestClient(app)
    print("Calling GET /benchmark/chunks...")
    response = client.get("/benchmark/chunks")
    
    if response.status_code != 200:
        print(f"Error calling API: {response.status_code}")
        print(response.text)
        return
        
    data = response.json()
    print(f"Retrieved {len(data)} chunks.")
    
    # Ensure directory exists
    os.makedirs("benchmark/dataset", exist_ok=True)
    
    # Save output
    output_path = "benchmark/dataset/chunks.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        
    print(f"Saved chunks to {output_path}")

if __name__ == "__main__":
    main()
