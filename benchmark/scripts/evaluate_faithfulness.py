import os
import sys
import json
import asyncio
import re

# Add project root to sys.path to enable imports from app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.llm.llm_router import LLMRouter

async def evaluate_faithfulness_with_retry(router: LLMRouter, contexts: list[str], gen_answer: str, max_retries=3) -> int:
    contexts_text = "\n---\n".join(contexts) if contexts else "No retrieved context."
    prompt = f"""You are an expert AI judge evaluating the faithfulness (groundedness) of a generated answer relative to the retrieved contexts.
An answer is faithful if all of its factual claims are supported by the provided contexts. It contains hallucinations if it makes claims not supported by the contexts.

Retrieved Contexts:
{contexts_text}

Generated Answer:
{gen_answer}

Rate the faithfulness of the generated answer on a scale from 1 to 5:
1 = hallucinated (the answer is entirely or almost entirely composed of claims not supported by the contexts)
2 = major unsupported claims (the answer contains major factual claims that are not supported by the contexts)
3 = some unsupported claims (the answer is mostly supported but contains some minor unsupported claims or extrapolations)
4 = mostly grounded (the answer is correct and almost entirely supported, with only very minor details or formatting elements not explicitly in the contexts)
5 = fully grounded (every single factual claim in the answer is completely and clearly supported by the retrieved contexts)

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
        
    # Check if there is an existing partial metrics file to resume from
    metrics_path = "benchmark/faithfulness/faithfulness_metrics.json"
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
            
        contexts = item.get("contexts", [])
        gen_answer = item.get("answer", "")
        
        print(f"[{idx+1}/{total}] Evaluating faithfulness for {q_id}...")
        
        try:
            score = await evaluate_faithfulness_with_retry(router, contexts, gen_answer, max_retries=3)
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
    print("TASK 7 complete!")

def save_metrics(scores):
    if not scores:
        return
        
    total_scores = len(scores)
    avg_faithfulness = sum(s["score"] for s in scores) / total_scores
    
    # Hallucination Rate is defined as the proportion of scores <= 3 (containing some or major hallucinations)
    hallucination_count = sum(1 for s in scores if s["score"] <= 3)
    hallucination_rate = hallucination_count / total_scores
    
    # Hallucination Rate (strict) defined as scores < 5 (anything not fully grounded)
    hallucination_count_strict = sum(1 for s in scores if s["score"] < 5)
    hallucination_rate_strict = hallucination_count_strict / total_scores
    
    # Initialize distribution
    dist = {str(i): 0 for i in range(1, 6)}
    for s in scores:
        score_str = str(s["score"])
        dist[score_str] = dist.get(score_str, 0) + 1
        
    metrics = {
        "average_faithfulness": avg_faithfulness,
        "hallucination_rate": hallucination_rate,
        "hallucination_rate_strict": hallucination_rate_strict,
        "score_distribution": dist,
        "scores": scores
    }
    
    os.makedirs("benchmark/faithfulness", exist_ok=True)
    with open("benchmark/faithfulness/faithfulness_metrics.json", "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)

def main():
    asyncio.run(main_async())

if __name__ == "__main__":
    main()
