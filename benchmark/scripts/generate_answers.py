import os
import json
import time
from fastapi.testclient import TestClient
from app.main import app

def main():
    print("Initializing TestClient...")
    client = TestClient(app)
    
    print("Loading chunks for lookup...")
    with open("benchmark/dataset/chunks.json", "r", encoding="utf-8") as f:
        chunks = json.load(f)
    chunks_map = {c["chunk_id"]: c["text"] for c in chunks if c.get("chunk_id")}
    
    print("Loading reviewed questions...")
    with open("benchmark/dataset/reviewed_questions.json", "r", encoding="utf-8") as f:
        questions = json.load(f)
        
    generated_answers = []
    total = len(questions)
    
    print(f"Generating answers for {total} questions using the RAG pipeline...")
    
    for i, q in enumerate(questions):
        q_id = q["question_id"]
        question_text = q["question"]
        
        # Call RAG pipeline API
        # POST /chat/chat?question=...
        start_time = time.time()
        try:
            response = client.post(
                "/chat/chat",
                params={"question": question_text}
            )
            elapsed = time.time() - start_time
            
            if response.status_code != 200:
                print(f"[{i+1}/{total}] Error for {q_id}: {response.status_code} (took {elapsed:.2f}s)")
                print(response.text)
                answer = "Error generating answer"
                sources = []
            else:
                res_data = response.json()
                answer = res_data.get("answer", "")
                sources = res_data.get("sources", []) or []
                print(f"[{i+1}/{total}] Generated answer for {q_id} (took {elapsed:.2f}s)")
                
        except Exception as e:
            elapsed = time.time() - start_time
            print(f"[{i+1}/{total}] Exception for {q_id}: {e} (took {elapsed:.2f}s)")
            answer = "Exception generating answer"
            sources = []
            
        # Extract chunk IDs and resolve contexts
        retrieved_chunk_ids = []
        contexts = []
        for src in sources:
            chunk_id = src.get("chunk_id")
            if chunk_id:
                retrieved_chunk_ids.append(chunk_id)
                # Lookup context text
                context_text = chunks_map.get(chunk_id, "")
                contexts.append(context_text)
                
        generated_answers.append({
            "question_id": q_id,
            "answer": answer,
            "retrieved_chunk_ids": retrieved_chunk_ids,
            "contexts": contexts
        })
        
        # Sleep to comply with model rate limits
        time.sleep(2.5)
        
    # Save output
    os.makedirs("benchmark/generation", exist_ok=True)
    output_path = "benchmark/generation/generated_answers.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(generated_answers, f, indent=2, ensure_ascii=False)
        
    print(f"Saved generated answers to {output_path}")
    print("TASK 5 complete!")

if __name__ == "__main__":
    main()
