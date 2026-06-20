import os
import sys
import json
import time
import asyncio
from uuid import uuid4

# Add project root to sys.path to enable imports from app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.api.chat import get_chat_service

# Global dictionary to capture timings of the current request
current_timings = {
    "retrieval": 0.0,
    "context": 0.0,
    "llm_calls": []
}

def compute_stats(values):
    if not values:
        return {"mean": 0.0, "median": 0.0, "p95": 0.0}
    
    # Sort values for median and percentile calculations
    sorted_vals = sorted(values)
    n = len(sorted_vals)
    
    # Mean
    mean_val = sum(sorted_vals) / n
    
    # Median
    if n % 2 == 1:
        median_val = sorted_vals[n // 2]
    else:
        median_val = (sorted_vals[n // 2 - 1] + sorted_vals[n // 2]) / 2.0
        
    # P95 using linear interpolation
    p_idx = 0.95 * (n - 1)
    idx_floor = int(p_idx)
    idx_ceil = min(n - 1, idx_floor + 1)
    weight = p_idx - idx_floor
    p95_val = sorted_vals[idx_floor] * (1.0 - weight) + sorted_vals[idx_ceil] * weight
    
    return {
        "mean": float(mean_val),
        "median": float(median_val),
        "p95": float(p95_val)
    }

async def main_async():
    input_path = "benchmark/dataset/reviewed_questions.json"
    print(f"Loading questions from {input_path}...")
    if not os.path.exists(input_path):
        print(f"Error: {input_path} not found.")
        sys.exit(1)
        
    with open(input_path, "r", encoding="utf-8") as f:
        questions = json.load(f)
        
    total_questions = len(questions)
    print(f"Total reviewed questions found: {total_questions}")
    
    # Select exactly 30 representative questions spread uniformly
    num_to_select = 30
    if total_questions <= num_to_select:
        selected_questions = questions
    else:
        step = total_questions / num_to_select
        indices = [int(i * step) for i in range(num_to_select)]
        selected_questions = [questions[i] for i in indices]
        
    selected_count = len(selected_questions)
    print(f"Selected {selected_count} representative questions for latency evaluation.")
    
    # Initialize chat service
    print("Initializing ChatService...")
    chat_service = await get_chat_service()
    
    # Wrap retrieval service search
    original_search = chat_service.retrieval_service.search
    async def timed_search(*args, **kwargs):
        t0 = time.perf_counter()
        res = await original_search(*args, **kwargs)
        current_timings["retrieval"] = time.perf_counter() - t0
        return res
    chat_service.retrieval_service.search = timed_search
    
    # Wrap context builder
    original_build_context = chat_service.context_builder_service.build_context
    async def timed_build_context(*args, **kwargs):
        t0 = time.perf_counter()
        res = await original_build_context(*args, **kwargs)
        current_timings["context"] = time.perf_counter() - t0
        return res
    chat_service.context_builder_service.build_context = timed_build_context
    
    # Wrap LLM router generate
    original_llm_generate = chat_service.llm_service.generate
    async def timed_llm_generate(*args, **kwargs):
        t0 = time.perf_counter()
        res = await original_llm_generate(*args, **kwargs)
        current_timings["llm_calls"].append(time.perf_counter() - t0)
        return res
    chat_service.llm_service.generate = timed_llm_generate

    results = []
    retrieval_latencies = []
    context_latencies = []
    llm_latencies = []
    e2e_latencies = []
    
    os.makedirs("benchmark/latency", exist_ok=True)
    
    for idx, q in enumerate(selected_questions):
        q_id = q["question_id"]
        question_text = q["question"]
        
        # Reset timings capture for the request
        current_timings["retrieval"] = 0.0
        current_timings["context"] = 0.0
        current_timings["llm_calls"] = []
        
        print(f"[{idx+1}/{selected_count}] Querying: '{question_text[:50]}...' ({q_id})")
        
        start_time = time.perf_counter()
        try:
            # We call chat_service.generate directly!
            # Since conversation_id is None, it will create a new conversation and generate a title
            await chat_service.generate(question=question_text)
            elapsed_e2e = time.perf_counter() - start_time
            
            ret_lat = current_timings["retrieval"]
            ctx_lat = current_timings["context"]
            llm_lat = sum(current_timings["llm_calls"])
            
            print(f"  Timings -> Retrieval: {ret_lat:.4f}s | Context: {ctx_lat:.4f}s | LLM: {llm_lat:.4f}s | E2E: {elapsed_e2e:.4f}s")
            
            results.append({
                "question_id": q_id,
                "retrieval_latency": ret_lat,
                "context_building_latency": ctx_lat,
                "llm_latency": llm_lat,
                "end_to_end_latency": elapsed_e2e,
                "individual_llm_calls": list(current_timings["llm_calls"])
            })
            
            retrieval_latencies.append(ret_lat)
            context_latencies.append(ctx_lat)
            llm_latencies.append(llm_lat)
            e2e_latencies.append(elapsed_e2e)
            
        except Exception as e:
            print(f"  Exception querying {q_id}: {e}")
            import traceback
            traceback.print_exc()
            
        save_metrics(retrieval_latencies, context_latencies, llm_latencies, e2e_latencies, results)
        
        # Sleep to comply with API rate limits
        await asyncio.sleep(2.5)

    print("\nLatency measurement complete! Calculating final statistics...")
    save_metrics(retrieval_latencies, context_latencies, llm_latencies, e2e_latencies, results)
    print("TASK 8 complete!")

def save_metrics(retrieval, context, llm, e2e, raw_results):
    metrics = {
        "retrieval_latency": compute_stats(retrieval),
        "context_building_latency": compute_stats(context),
        "llm_latency": compute_stats(llm),
        "end_to_end_latency": compute_stats(e2e),
        "sample_size": len(raw_results),
        "raw_results": raw_results
    }
    
    metrics_path = "benchmark/latency/latency_metrics.json"
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)

def main():
    asyncio.run(main_async())

if __name__ == "__main__":
    main()
