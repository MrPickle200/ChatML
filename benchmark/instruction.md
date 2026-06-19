# Benchmark Plan

## General Rules

You are evaluating a RAG system.

Follow these rules:

1. Execute exactly one task per run.
2. Stop immediately after completing a task.
3. Never continue to the next task automatically.
4. Save all outputs to disk.
5. Reuse existing files whenever possible.
6. Do not regenerate existing artifacts.
7. Do not access Qdrant directly.
8. Use provided APIs only.
9. All intermediate results must be stored.

Directory structure:

benchmark/
├── dataset/
│   ├── chunks.json
│   ├── candidate_questions.json
│   ├── reviewed_questions.json
│   ├── ground_truth_answers.json
│   └── ground_truth_chunks.json
│
├── retrieval/
│   ├── retrieval_results.json
│   └── retrieval_metrics.json
│
├── generation/
│   ├── generated_answers.json
│   └── generation_metrics.json
│
├── faithfulness/
│   └── faithfulness_metrics.json
│
├── latency/
│   └── latency_metrics.json
│
└── final_report/
└── benchmark_report.md

---

## TASK 0 — Export Chunks

Goal:

Collect all chunks from the knowledge base.

Write script app/api/benchmark.py which contains API:

GET /benchmark/chunks

Use above API

Expected response:

[
{
"chunk_id": "...",
"document_id": "...",
"text": "..."
}
]

Save as:

benchmark/dataset/chunks.json

Stop.

---

## TASK 1 — Generate Candidate Questions

Input:

benchmark/dataset/chunks.json

Goal:

Generate 100 candidate QA pairs.

For each QA pair:

{
"question_id": "...",
"question": "...",
"ground_truth_answer": "...",
"supporting_chunk_ids": [...]
}

Requirements:

* Questions must be answerable from chunks.
* Questions should cover different documents.
* Avoid duplicate questions.
* Avoid trivial questions.

Save:

benchmark/dataset/candidate_questions.json

Stop.

---

## TASK 2 — Human Review Checkpoint

Do NOT generate anything.

Wait for human review.

Human will:

* Remove bad questions
* Remove duplicates
* Fix incorrect answers
* Keep approximately 50 high-quality questions

Expected file after review:

benchmark/dataset/reviewed_questions.json

Stop.

---

## TASK 3 — Build Ground Truth Files

Input:

reviewed_questions.json

Create:

benchmark/dataset/ground_truth_answers.json

benchmark/dataset/ground_truth_chunks.json

Stop.

---

## TASK 4 — Retrieval Evaluation

Input:

reviewed_questions.json
ground_truth_chunks.json

For each question:

Call retrieval endpoint:

POST /retrieve

Retrieve:

top_k = 5

Save:

{
"question_id": "...",
"retrieved_chunk_ids": [...]
}

Output:

benchmark/retrieval/retrieval_results.json

Compute:

* Recall@5
* Hit Rate@5
* MRR

Save:

benchmark/retrieval/retrieval_metrics.json

Stop.

---

## TASK 5 — Generate Answers

Input:

reviewed_questions.json

For each question:

Call complete RAG pipeline:

POST /chat

Save:

{
"question_id": "...",
"answer": "...",
"retrieved_chunk_ids": [...],
"contexts": [...]
}

Output:

benchmark/generation/generated_answers.json

Stop.

---

## TASK 6 — Evaluate Answer Correctness

Input:

generated_answers.json
ground_truth_answers.json

Use LLM-as-Judge.

Scoring:

1 = completely wrong
2 = mostly wrong
3 = partially correct
4 = mostly correct
5 = fully correct

Save per-question scores.

Compute:

* Average Correctness
* Score Distribution

Output:

benchmark/generation/generation_metrics.json

Stop.

---

## TASK 7 — Evaluate Faithfulness

Input:

generated_answers.json

For each answer:

Determine whether factual claims are supported by retrieved contexts.

Scoring:

1 = hallucinated
2 = major unsupported claims
3 = some unsupported claims
4 = mostly grounded
5 = fully grounded

Compute:

* Average Faithfulness
* Hallucination Rate

Save:

benchmark/faithfulness/faithfulness_metrics.json

Stop.

---

## TASK 8 — Latency Evaluation

Input:

reviewed_questions.json

Select 30 representative questions.

Measure:

* Retrieval latency
* Context building latency
* LLM latency
* End-to-end latency

Compute:

* Mean
* Median
* P95

Save:

benchmark/latency/latency_metrics.json

Stop.

---

## TASK 9 — Final Report

Input:

retrieval_metrics.json
generation_metrics.json
faithfulness_metrics.json
latency_metrics.json

Generate:

benchmark/final_report/benchmark_report.md

Include:

# Retrieval

Recall@5
Hit Rate@5
MRR

# Generation

Average Correctness

# Faithfulness

Average Faithfulness
Hallucination Rate

# Latency

Mean
Median
P95

# Strengths

# Weaknesses

# Recommended Improvements

Stop.
