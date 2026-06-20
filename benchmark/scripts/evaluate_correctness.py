import os
import sys
import json
import asyncio
import re

# Add project root to sys.path to enable imports from app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.llm.llm_router import LLMRouter

async def evaluate_question_with_retry(router: LLMRouter, question: str, gt_answer: str, gen_answer: str, max_retries=3) -> int:
    prompt = f"""You are an expert AI judge evaluating the correctness of a generated answer against a ground truth answer.

Question: {question}
Ground Truth Answer: {gt_answer}
Generated Answer: {gen_answer}

Rate the correctness of the generated answer on a scale from 1 to 5:
1 = completely wrong (the answer is entirely incorrect or irrelevant)
2 = mostly wrong (the answer contains major errors or misses the main point)
3 = partially correct (the answer contains some correct information but also significant errors or omissions)
4 = mostly correct (the answer is correct in all major aspects but might have minor details wrong or missing)
5 = fully correct (the answer is completely correct and matches the ground truth in all important details)

Return ONLY a single integer between 1 and 5 (inclusive) representing the score. Do not provide any explanation, preamble, or markdown formatting. Just return the digit.
"""
    for attempt in range(1, max_retries + 1):
        try:
            response = await router.generate(prompt)
            match = re.search(r'[1-5]', response.strip())
            if match:
                return int(match.group(0))
            else:
                print(f"Warning: Could not parse score from response: '{response}' (attempt {attempt}/{max_retries})")
                if attempt == max_retries:
                    print("Defaulting to score 3 after failed parsing.")
                    return 3
        except Exception as e:
            print(f"Error on evaluation attempt {attempt}/{max_retries}: {e}")
            if attempt < max_retries:
                # Wait before retrying (exponential backoff)
                await asyncio.sleep(5 * attempt)
            else:
                raise e
    return 3

async def main_async():
    print("Loading generated answers...")
    if not os.path.exists("benchmark/generation/generated_answers.json"):
        print("Error: benchmark/generation/generated_answers.json not found!")
        sys.exit(1)
        
    with open("benchmark/generation/generated_answers.json", "r", encoding="utf-8") as f:
        generated_answers = json.load(f)
        
    print("Loading ground truth answers...")
    if not os.path.exists("benchmark/dataset/ground_truth_answers.json"):
        print("Error: benchmark/dataset/ground_truth_answers.json not found!")
        sys.exit(1)
        
    with open("benchmark/dataset/ground_truth_answers.json", "r", encoding="utf-8") as f:
        gt_answers = json.load(f)
        
    # Map ground truth by question_id
    gt_map = {item["question_id"]: item["ground_truth_answer"] for item in gt_answers}
    
    print("Loading reviewed questions (for question text)...")
    if not os.path.exists("benchmark/dataset/reviewed_questions.json"):
        print("Error: benchmark/dataset/reviewed_questions.json not found!")
        sys.exit(1)
        
    with open("benchmark/dataset/reviewed_questions.json", "r", encoding="utf-8") as f:
        reviewed_questions = json.load(f)
        
    questions_map = {q["question_id"]: q["question"] for q in reviewed_questions}
    
    # Check if there is an existing partial metrics file to resume from
    metrics_path = "benchmark/generation/generation_metrics.json"
    scores = []
    completed_ids = set()
    
    if os.path.exists(metrics_path):
        try:
            with open(metrics_path, "r", encoding="utf-8") as f:
                existing_data = json.load(f)
                scores = existing_data.get("scores", [])
                completed_ids = {s["question_id"] for s in scores}
                print(f"Resuming evaluation: found {len(completed_ids)} already evaluated answers.")
        except Exception:
            print("Could not load existing metrics file, starting fresh.")
            scores = []
            completed_ids = set()

    router = LLMRouter()
    total = len(generated_answers)
    
    for idx, item in enumerate(generated_answers):
        q_id = item["question_id"]
        if q_id in completed_ids:
            continue
            
        question_text = questions_map.get(q_id, "")
        gt_answer = gt_map.get(q_id, "")
        gen_answer = item.get("answer", "")
        
        print(f"[{idx+1}/{total}] Evaluating {q_id}...")
        
        try:
            score = await evaluate_question_with_retry(router, question_text, gt_answer, gen_answer, max_retries=3)
            scores.append({
                "question_id": q_id,
                "score": score
            })
            
            # Compute current metrics and save intermediate progress
            save_metrics(scores)
            
            # Sleep briefly to prevent rate limits
            await asyncio.sleep(2)
            
        except Exception as e:
            print(f"\nCRITICAL: Rate limit or error occurred across all models. Retries exhausted.")
            print(f"Details: {e}")
            print("Stopping execution and preserving progress. Please notify the user.")
            sys.exit(1)
            
    print("\nEvaluation complete! Computing final metrics...")
    save_metrics(scores)
    print("TASK 6 complete!")

def save_metrics(scores):
    if not scores:
        return
        
    total_scores = len(scores)
    avg_correctness = sum(s["score"] for s in scores) / total_scores
    
    # Initialize distribution
    dist = {str(i): 0 for i in range(1, 6)}
    for s in scores:
        score_str = str(s["score"])
        dist[score_str] = dist.get(score_str, 0) + 1
        
    metrics = {
        "average_correctness": avg_correctness,
        "score_distribution": dist,
        "scores": scores
    }
    
    os.makedirs("benchmark/generation", exist_ok=True)
    with open("benchmark/generation/generation_metrics.json", "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)

def main():
    asyncio.run(main_async())

if __name__ == "__main__":
    main()
