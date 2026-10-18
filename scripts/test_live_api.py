import httpx
import json

def test_live():
    url = "http://127.0.0.1:8000/api/ask"
    payload = {"query": "What are the risk factors for type 2 diabetes?"}
    print(f"Sending POST to {url}...")

    with httpx.Client(timeout=120.0) as client:
        resp = client.post(url, json=payload)
        print(f"Response status: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            print("=== SUCCESS ===")
            print(f"Answer: {data['answer'][:200]}...")
            print(f"Sources count: {len(data['sources'])}")
            print(f"Total claims: {data['claim_verification']['total_claims']}")
            print(f"Supported claims: {data['claim_verification']['supported_claims']}")
            print(f"Confidence score: {data['confidence']['confidence_score']:.4f} ({data['confidence']['confidence_level']})")
            print(f"Hallucination decision: {data['hallucination_decision']['decision']}")
            print(f"Self-correction applied: {data['self_correction']['correction_applied']}")
        else:
            print("Failed:", resp.text)

if __name__ == "__main__":
    test_live()
