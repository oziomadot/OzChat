import time
import csv
import requests
from statistics import median, quantiles
import pandas as pd

# Change this to your deployed Render URL or local URL
BASE_URL = "https://ozchat-x5d3.onrender.com"   # ← UPDATE THIS

def evaluate():
    results = []
    latencies = []
    
    with open("evaluation_set.csv", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            question = row["question"]
            print(f"\nEvaluating: {question}")
            
            overall_start = time.perf_counter()
            
            # ── Measure retrieval ───────────────────────────────
            retrieve_start = time.perf_counter()
            # If you can call retrieval separately – do it here
            # Otherwise approximate by first part of /chat response
            retrieve_time = 0  # placeholder – improve if possible
            
            # ── Full API call ────────────────────────────────────
            resp_start = time.perf_counter()
            resp = requests.post(
                f"{BASE_URL}/chat",
                json={"question": question},
                timeout=60
            )
            resp_end = time.perf_counter()
            
            api_latency_ms = (resp_end - resp_start) * 1000
            
            overall_end = time.perf_counter()
            total_latency_ms = (overall_end - overall_start) * 1000
            
            if resp.status_code != 200:
                print(f"  → ERROR {resp.status_code}")
                continue
                
            data = resp.json()
            answer = data.get("answer", "")
            citations = data.get("citations", [])
            num_chunks = data.get("num_chunks_retrieved", 0)
            
            results.append({
                "question": question,
                "answer_snippet": answer[:120] + "..." if len(answer) > 120 else answer,
                "num_chunks": num_chunks,
                "api_latency_ms": round(api_latency_ms, 1),
                "total_latency_ms": round(total_latency_ms, 1),
                "citations_count": len(citations)
            })
            
            print(f"  → API call: {api_latency_ms:6.1f} ms")
            print(f"  → Total:    {total_latency_ms:6.1f} ms")
            print(f"  → Chunks:   {num_chunks:2d} | Citations: {len(citations)}")
    
    # Summary statistics
    if results:
        all_total = [r["total_latency_ms"] for r in results]
        p50 = median(all_total)
        p95 = quantiles(all_total, n=20)[18] if len(all_total) >= 20 else max(all_total)
        
        print("\n" + "="*40)
        print(f"Evaluation complete – {len(results)} queries")
        print(f"p50 latency: {p50:6.1f} ms")
        print(f"p95 latency: {p95:6.1f} ms")
        
        # Save detailed results
        pd.DataFrame(results).to_csv("evaluation_results_detailed.csv", index=False)
        print("Detailed results saved to evaluation_results_detailed.csv")
    
    return results

if __name__ == "__main__":
    evaluate()