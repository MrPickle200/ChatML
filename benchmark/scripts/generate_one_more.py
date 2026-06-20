import json
import asyncio
from app.llm.groq import GroqModel

async def main():
    # Load chunks
    with open("benchmark/dataset/chunks.json", "r", encoding="utf-8") as f:
        chunks = json.load(f)
    
    target_chunk = None
    for chunk in chunks:
        if chunk["chunk_id"] == "14413de1-9dba-4124-9498-c38dc27b5215":
            target_chunk = chunk
            break
            
    if not target_chunk:
        print("Chunk not found!")
        return
        
    # Load existing questions
    with open("benchmark/dataset/candidate_questions.json", "r", encoding="utf-8") as f:
        questions = json.load(f)
        
    if len(questions) >= 100:
        print(f"Already have {len(questions)} questions. No need to generate more.")
        return
        
    router = GroqModel()
    prompt = f"""You are a RAG evaluator. Your task is to generate a high-quality, non-trivial, clear question and its ground truth answer based on the provided source text.
The question must be fully answerable using ONLY the text provided. Do not use external knowledge or assume facts not mentioned in the text.
Avoid simple or trivial questions (e.g., "What is the title of the document?" or "Who wrote this?"). Instead, focus on concepts, definitions, rules, or relationships explained in the text.

Source Text:
---
{target_chunk['text']}
---

Provide the output in valid JSON format with the following keys:
- "question": The generated question.
- "ground_truth_answer": The detailed ground truth answer to the question based on the text.

Do not include any other text, markdown formatting (like ```json), or explanations outside of the JSON object.
"""

    print("Generating question for chunk...")
    response = await router.generate(prompt)
    cleaned = response.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    cleaned = cleaned.strip()
    
    parsed = json.loads(cleaned)
    new_q = {
        "question_id": "q_100",
        "question": parsed["question"].strip(),
        "ground_truth_answer": parsed["ground_truth_answer"].strip(),
        "supporting_chunk_ids": [target_chunk["chunk_id"]]
    }
    
    questions.append(new_q)
    
    # Save back
    with open("benchmark/dataset/candidate_questions.json", "w", encoding="utf-8") as f:
        json.dump(questions, f, indent=2, ensure_ascii=False)
        
    print("Successfully added q_100. Total questions:", len(questions))

if __name__ == "__main__":
    asyncio.run(main())
