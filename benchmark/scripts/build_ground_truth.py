import os
import json
import shutil

def main():
    print("Copying candidate_questions.json to reviewed_questions.json...")
    shutil.copyfile("benchmark/dataset/candidate_questions.json", "benchmark/dataset/reviewed_questions.json")
    
    print("Loading reviewed_questions.json...")
    with open("benchmark/dataset/reviewed_questions.json", "r", encoding="utf-8") as f:
        questions = json.load(f)
        
    ground_truth_answers = []
    ground_truth_chunks = []
    
    for q in questions:
        q_id = q["question_id"]
        ground_truth_answers.append({
            "question_id": q_id,
            "ground_truth_answer": q["ground_truth_answer"]
        })
        ground_truth_chunks.append({
            "question_id": q_id,
            "ground_truth_chunk_ids": q["supporting_chunk_ids"]
        })
        
    # Save files
    os.makedirs("benchmark/dataset", exist_ok=True)
    
    gt_answers_path = "benchmark/dataset/ground_truth_answers.json"
    with open(gt_answers_path, "w", encoding="utf-8") as f:
        json.dump(ground_truth_answers, f, indent=2, ensure_ascii=False)
    print(f"Saved ground truth answers to {gt_answers_path}")
    
    gt_chunks_path = "benchmark/dataset/ground_truth_chunks.json"
    with open(gt_chunks_path, "w", encoding="utf-8") as f:
        json.dump(ground_truth_chunks, f, indent=2, ensure_ascii=False)
    print(f"Saved ground truth chunks to {gt_chunks_path}")
    
    print("TASK 3 complete!")

if __name__ == "__main__":
    main()
