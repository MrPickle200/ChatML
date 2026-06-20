import os
import json
import time
import requests

def main():
    print("Loading chunks for lookup...")
    with open("benchmark/dataset/chunks.json", "r", encoding="utf-8") as f:
        chunks = json.load(f)
    chunks_map = {c["chunk_id"]: c["text"] for c in chunks if c.get("chunk_id")}
    
    print("Loading reviewed questions...")
    with open("benchmark/dataset/reviewed_questions.json", "r", encoding="utf-8") as f:
        questions = json.load(f)
    questions_map = {q["question_id"]: q["question"] for q in questions}
        
    print("Loading generated answers...")
    with open("benchmark/generation/generated_answers.json", "r", encoding="utf-8") as f:
        generated = json.load(f)
        
    url = "http://127.0.0.1:8000/chat/chat"
    updated_count = 0
    
    for idx, item in enumerate(generated):
        q_id = item["question_id"]
        answer = item.get("answer", "")
        
        # Check if this item is a failed connection/exception
        if answer.startswith("Exception generating answer") or answer.startswith("Error generating answer"):
            question_text = questions_map.get(q_id)
            if not question_text:
                print(f"Question text not found for {q_id}!")
                continue
                
            print(f"Repairing {q_id}...")
            start_time = time.time()
            try:
                response = requests.post(
                    url,
                    params={"question": question_text},
                    timeout=120
                )
                elapsed = time.time() - start_time
                
                if response.status_code != 200:
                    print(f"Failed to repair {q_id}: {response.status_code} (took {elapsed:.2f}s)")
                    continue
                    
                res_data = response.json()
                item["answer"] = res_data.get("answer", "")
                sources = res_data.get("sources", []) or []
                
                # Resolve chunk IDs and contexts
                retrieved_chunk_ids = []
                contexts = []
                for src in sources:
                    chunk_id = src.get("chunk_id")
                    if chunk_id:
                        retrieved_chunk_ids.append(chunk_id)
                        contexts.append(chunks_map.get(chunk_id, ""))
                        
                item["retrieved_chunk_ids"] = retrieved_chunk_ids
                item["contexts"] = contexts
                
                updated_count += 1
                print(f"Successfully repaired {q_id} (took {elapsed:.2f}s)")
                
                # Write back immediately after each success to preserve progress
                with open("benchmark/generation/generated_answers.json", "w", encoding="utf-8") as f:
                    json.dump(generated, f, indent=2, ensure_ascii=False)
                    
            except Exception as e:
                elapsed = time.time() - start_time
                print(f"Error repairing {q_id}: {e} (took {elapsed:.2f}s)")
                
            time.sleep(2.5)
            
    print(f"Repair finished! Total updated items: {updated_count}")

if __name__ == "__main__":
    main()
