import os
import json
from fastapi.testclient import TestClient
from app.main import app

def main():
    print("Initializing TestClient...")
    client = TestClient(app)
    
    print("Loading input files...")
    with open("benchmark/dataset/reviewed_questions.json", "r", encoding="utf-8") as f:
        questions = json.load(f)
        
    with open("benchmark/dataset/ground_truth_chunks.json", "r", encoding="utf-8") as f:
        gt_chunks_list = json.load(f)
        
    # Create lookup map for ground truth chunks: question_id -> list of chunk_ids
    gt_chunks_map = {item["question_id"]: item["ground_truth_chunk_ids"] for item in gt_chunks_list}
    
    retrieval_results = []
    
    total_questions = len(questions)
    print(f"Running retrieval evaluation for {total_questions} questions...")
    
    reciprocal_ranks = []
    recalls = []
    hits = []
    
    for i, q in enumerate(questions):
        q_id = q["question_id"]
        question_text = q["question"]
        gt_chunk_ids = gt_chunks_map.get(q_id, [])
        
        # Call retrieval endpoint
        # POST /document/retrieval?query=...&top_k=5&threshold=0.0
        response = client.post(
            "/document/retrieval",
            params={
                "query": question_text,
                "top_k": 5,
                "threshold": 0.0
            }
        )
        
        if response.status_code != 200:
            print(f"[{i+1}/{total_questions}] Error retrieving for {q_id}: {response.status_code}")
            retrieved_chunk_ids = []
        else:
            retrieved_chunks = response.json()
            retrieved_chunk_ids = [chunk["chunk_id"] for chunk in retrieved_chunks]
            
        retrieval_results.append({
            "question_id": q_id,
            "retrieved_chunk_ids": retrieved_chunk_ids
        })
        
        # Compute metrics for this question
        # 1. Hit Rate & Recall
        intersection = set(retrieved_chunk_ids).intersection(set(gt_chunk_ids))
        
        hit = 1 if len(intersection) > 0 else 0
        hits.append(hit)
        
        recall = len(intersection) / len(gt_chunk_ids) if len(gt_chunk_ids) > 0 else 0.0
        recalls.append(recall)
        
        # 2. Reciprocal Rank
        rr = 0.0
        for rank_idx, chunk_id in enumerate(retrieved_chunk_ids):
            if chunk_id in gt_chunk_ids:
                rr = 1.0 / (rank_idx + 1)
                break
        reciprocal_ranks.append(rr)
        
        if (i + 1) % 10 == 0 or (i + 1) == total_questions:
            print(f"Processed {i+1}/{total_questions} questions...")
            
    # Compute overall metrics
    avg_recall = sum(recalls) / len(recalls) if recalls else 0.0
    avg_hit_rate = sum(hits) / len(hits) if hits else 0.0
    mrr = sum(reciprocal_ranks) / len(reciprocal_ranks) if reciprocal_ranks else 0.0
    
    print("\n--- Retrieval Metrics ---")
    print(f"Recall@5:   {avg_recall:.4f}")
    print(f"Hit Rate@5: {avg_hit_rate:.4f}")
    print(f"MRR:        {mrr:.4f}")
    print("-------------------------\n")
    
    # Save outputs
    os.makedirs("benchmark/retrieval", exist_ok=True)
    
    results_path = "benchmark/retrieval/retrieval_results.json"
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(retrieval_results, f, indent=2, ensure_ascii=False)
    print(f"Saved retrieval results to {results_path}")
    
    metrics_path = "benchmark/retrieval/retrieval_metrics.json"
    metrics = {
        "recall_at_5": avg_recall,
        "hit_rate_at_5": avg_hit_rate,
        "mrr": mrr
    }
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)
    print(f"Saved retrieval metrics to {metrics_path}")
    
    print("TASK 4 complete!")

if __name__ == "__main__":
    main()
