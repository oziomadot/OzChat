import time
import csv
import requests
from statistics import median, quantiles

# Change this to your deployed Render URL or local URL
BASE_URL = "https://ozchat-x5d3.onrender.com"   # ← UPDATE THIS

def evaluate():
    results = []
    latencies = []
    
    with open("evaluation_set.csv", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            question = row["question"]
            start = time.perf_counter()
            
            try:
                resp = requests.post(f"{BASE_URL}/chat", json={"question": question}, timeout=60)
                end = time.perf_counter()
                
                latency = (end - start) * 1000  # ms
                latencies.append(latency)
                
                data = resp.json()
                answer = data.get("answer", "")
                citations = data.get("citations", [])
                
                results.append({
                    "question": question,
                    "answer": answer,
                    "citations": citations,
                    "latency_ms": round(latency, 1),
                    "raw_response": data
                })
                
                print(f" {question[:60]:60} | {latency:6.1f}ms")
                
            except requests.exceptions.Timeout:
                print(f"  TIMEOUT: {question[:60]:60}")
                results.append({
                    "question": question,
                    "answer": "REQUEST TIMEOUT",
                    "citations": [],
                    "latency_ms": 60000,
                    "error": "timeout"
                })
            except Exception as e:
                print(f" ERROR: {question[:60]:60} | {str(e)}")
                results.append({
                    "question": question,
                    "answer": f"ERROR: {str(e)}",
                    "citations": [],
                    "latency_ms": 0,
                    "error": str(e)
                })
    
    # Calculate metrics (only successful requests)
    successful_latencies = [r["latency_ms"] for r in results if "error" not in r]
    if successful_latencies:
        p50 = median(successful_latencies)
        p95 = quantiles(successful_latencies, n=20)[18] if len(successful_latencies) >= 20 else max(successful_latencies)
    else:
        p50 = p95 = 0
    
    print("\n=== EVALUATION RESULTS ===")
    print(f"Total questions: {len(results)}")
    print(f"Successful: {len(successful_latencies)}")
    print(f"Latency → p50: {p50:.1f}ms | p95: {p95:.1f}ms")
    
    return results

if __name__ == "__main__":
    evaluate()