import os
import json
import asyncio
import re
from app.llm.groq import GroqModel

async def generate_question_for_chunk(router: GroqModel, chunk: dict, max_retries=3) -> dict | None:
    chunk_text = chunk["text"]
    chunk_id = chunk["chunk_id"]
    document_id = chunk["document_id"]
    
    prompt = f"""You are a RAG evaluator. Your task is to generate a high-quality, non-trivial, clear question and its ground truth answer based on the provided source text.
The question must be fully answerable using ONLY the text provided. Do not use external knowledge or assume facts not mentioned in the text.
Avoid simple or trivial questions (e.g., "What is the title of the document?" or "Who wrote this?"). Instead, focus on concepts, definitions, rules, or relationships explained in the text.

Source Text:
---
{chunk_text}
---

Provide the output in valid JSON format with the following keys:
- "question": The generated question.
- "ground_truth_answer": The detailed ground truth answer to the question based on the text.

Do not include any other text, markdown formatting (like ```json), or explanations outside of the JSON object.
"""
    
    for attempt in range(max_retries):
        try:
            raw_response = await router.generate(prompt)
            
            # Clean up potential markdown formatting
            cleaned = raw_response.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()
            
            # Attempt to parse JSON
            parsed = json.loads(cleaned)
            if "question" in parsed and "ground_truth_answer" in parsed:
                return {
                    "question": parsed["question"].strip(),
                    "ground_truth_answer": parsed["ground_truth_answer"].strip(),
                    "supporting_chunk_ids": [chunk_id]
                }
            
        except Exception as e:
            print(f"Attempt {attempt + 1} failed for chunk {chunk_id}: {e}")
            await asyncio.sleep(2)
            
    return None

async def main():
    print("Loading chunks...")
    with open("benchmark/dataset/chunks.json", "r", encoding="utf-8") as f:
        chunks = json.load(f)
        
    # Group chunks by document_id
    docs = {}
    for chunk in chunks:
        docs.setdefault(chunk["document_id"], []).append(chunk)
        
    print(f"Found {len(docs)} documents.")
    
    router = GroqModel()
    candidate_questions = []
    
    # We want 100 questions. 4 documents, so 25 questions per document.
    questions_per_doc = 25
    
    tasks = []
    chunk_mapping = [] # to keep track of which chunk maps to which task
    
    for doc_id, doc_chunks in docs.items():
        print(f"Doc {doc_id} has {len(doc_chunks)} chunks.")
        # Sample 25 chunks evenly
        n_chunks = len(doc_chunks)
        sampled_chunks = [doc_chunks[int(i * n_chunks / questions_per_doc)] for i in range(questions_per_doc)]
        
        for chunk in sampled_chunks:
            tasks.append(generate_question_for_chunk(router, chunk))
            chunk_mapping.append(chunk)
            
    print(f"Starting concurrency generation of {len(tasks)} candidate questions...")
    
    # Run in batches of 5 to avoid rate limiting
    batch_size = 5
    results = []
    for i in range(0, len(tasks), batch_size):
        batch_tasks = tasks[i:i+batch_size]
        print(f"Running batch {i // batch_size + 1}/{(len(tasks) - 1) // batch_size + 1}...")
        batch_results = await asyncio.gather(*batch_tasks)
        results.extend(batch_results)
        # small sleep between batches
        await asyncio.sleep(2)
        
    # Build final list of questions
    final_questions = []
    question_counter = 1
    for res, chunk in zip(results, chunk_mapping):
        if res:
            final_questions.append({
                "question_id": f"q_{question_counter:03d}",
                "question": res["question"],
                "ground_truth_answer": res["ground_truth_answer"],
                "supporting_chunk_ids": res["supporting_chunk_ids"]
            })
            question_counter += 1
        else:
            print(f"Warning: Failed to generate question for chunk {chunk['chunk_id']}")
            
    print(f"Generated {len(final_questions)} candidate questions successfully.")
    
    # Ensure dataset folder exists
    os.makedirs("benchmark/dataset", exist_ok=True)
    
    # Save output
    output_path = "benchmark/dataset/candidate_questions.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(final_questions, f, indent=2, ensure_ascii=False)
        
    print(f"Saved candidate questions to {output_path}")

if __name__ == "__main__":
    asyncio.run(main())
