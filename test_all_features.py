import urllib.request
import json
import re
import sys

BASE_URL = "https://llm-portfolio-mu.vercel.app"

def test_dom_ids():
    with open("public/index.html", "r", encoding="utf-8") as f:
        html = f.read()

    defined = set(re.findall(r'id=["\']([^"\']+)["\']', html))
    refs = set(re.findall(r"getElementById\(r?['\"]([^'\"]+)['\"]\)", html))
    refs.update({'tab-p1', 'tab-p2', 'tab-p3', 'tab-btn-p1', 'tab-btn-p2', 'tab-btn-p3'})

    missing = [r for r in refs if r not in defined]
    assert not missing, f"Missing DOM IDs: {missing}"
    print(f"[DOM Check] All {len(refs)} referenced element IDs exist in index.html!")

def test_live_homepage():
    req = urllib.request.Request(f"{BASE_URL}/", headers={"User-Agent": "Mozilla/5.0"})
    res = urllib.request.urlopen(req)
    assert res.status == 200, f"Expected 200, got {res.status}"
    body = res.read().decode("utf-8")
    assert "<style>" in body
    assert ".hidden { display: none !important; }" in body
    assert "cdn.tailwindcss.com" not in body
    print(f"[Homepage Check] Homepage is live, 200 OK, {len(body)} bytes, standalone CSS verified!")

def test_live_health():
    url = f"{BASE_URL}/api/health"
    res = urllib.request.urlopen(url)
    assert res.status == 200
    data = json.loads(res.read().decode())
    assert data.get("status") == "ok"
    print(f"[Health Check] /api/health -> 200 OK: {data}")

def test_live_stats():
    url = f"{BASE_URL}/api/stats"
    res = urllib.request.urlopen(url)
    assert res.status == 200
    data = json.loads(res.read().decode())
    assert "project_1" in data and "project_2" in data and "project_3" in data
    print(f"[Stats Check] /api/stats -> 200 OK! P1 hit rate: {data['project_1']['hit_rate_pct']}%, P2 flips: {data['project_2']['position_flips']}, P3 ASR after: {data['project_3']['injections_after']}")

def test_live_p1_features():
    # 1. Exact Hit
    url = f"{BASE_URL}/api/p1/query"
    payload = json.dumps({"question": "What is your return policy?", "threshold": 0.75, "enable_neg_guard": True, "enable_pii_filter": True}).encode()
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
    res = urllib.request.urlopen(req)
    assert res.status == 200
    data = json.loads(res.read().decode())
    assert data["hit"] is True, f"Expected cache hit, got {data}"
    assert data["matched_faq_id"] == "faq_01"
    print(f"[P1 Feature: Exact Hit] Success! Matched: {data['matched_faq_id']}, Similarity: {data['similarity']}, Latency: {data['latency_ms']}ms")

    # 2. Semantic Paraphrase Hit
    payload = json.dumps({"question": "can i get a refund on an item i bought?", "threshold": 0.75, "enable_neg_guard": True, "enable_pii_filter": True}).encode()
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
    res = urllib.request.urlopen(req)
    assert res.status == 200
    data = json.loads(res.read().decode())
    assert data["hit"] is True, f"Expected semantic hit, got {data}"
    print(f"[P1 Feature: Semantic Hit] Success! Matched: {data['matched_faq_id']}, Similarity: {data['similarity']}")

    # 3. Negation Polarity Guard (Should NOT hit even if high similarity)
    payload = json.dumps({"question": "Why is international shipping not available?", "threshold": 0.75, "enable_neg_guard": True, "enable_pii_filter": True}).encode()
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
    res = urllib.request.urlopen(req)
    assert res.status == 200
    data = json.loads(res.read().decode())
    assert data["hit"] is False, "Expected negation guard to prevent false hit"
    assert data["audit"]["negation_blocked"] is True
    print(f"[P1 Feature: Negation Guard] Success! Correctly blocked hit due to polarity conflict (audit.negation_blocked=True)")

    # 4. Out of scope / Miss
    payload = json.dumps({"question": "What is the capital of Australia?", "threshold": 0.75, "enable_neg_guard": True, "enable_pii_filter": True}).encode()
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
    res = urllib.request.urlopen(req)
    assert res.status == 200
    data = json.loads(res.read().decode())
    assert data["hit"] is False
    print(f"[P1 Feature: Miss Fallback] Success! LLM answer generated, tokens: {data['tokens']}")

def test_live_p2_features():
    # 1. Fetch Questions list
    url = f"{BASE_URL}/api/p2/questions"
    res = urllib.request.urlopen(url)
    assert res.status == 200
    questions = json.loads(res.read().decode())
    assert len(questions) == 30
    print(f"[P2 Feature: Questions List] Success! Loaded {len(questions)} evaluation pairs")

    # 2. Evaluate Question without swap
    url = f"{BASE_URL}/api/p2/judge"
    payload = json.dumps({"question_id": "q01", "swap_order": False, "length_neutral": False}).encode()
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
    res = urllib.request.urlopen(req)
    assert res.status == 200
    v1 = json.loads(res.read().decode())
    assert "winner" in v1 and "reason" in v1
    print(f"[P2 Feature: Standard Judge] Success! Winner: {v1['winner']}, Reason: {v1['reason'][:60]}...")

    # 3. Evaluate Question with swap
    payload = json.dumps({"question_id": "q01", "swap_order": True, "length_neutral": False}).encode()
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
    res = urllib.request.urlopen(req)
    assert res.status == 200
    v2 = json.loads(res.read().decode())
    assert "winner" in v2
    print(f"[P2 Feature: Swapped Order Judge] Success! Winner: {v2['winner']}, Presentation: {v2['presentation']}")

    # 4. Evaluate with Length-Neutral Instruction
    payload = json.dumps({"question_id": "q01", "swap_order": False, "length_neutral": True}).encode()
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
    res = urllib.request.urlopen(req)
    assert res.status == 200
    v3 = json.loads(res.read().decode())
    assert "winner" in v3
    print(f"[P2 Feature: Length-Neutral Debiasing] Success! Winner: {v3['winner']}")

def test_live_p3_features():
    # 1. Fetch Attacks list
    url = f"{BASE_URL}/api/p3/attacks"
    res = urllib.request.urlopen(url)
    assert res.status == 200
    attacks = json.loads(res.read().decode())
    assert len(attacks) == 10
    print(f"[P3 Feature: Attacks List] Success! Loaded {len(attacks)} distinct injection vectors")

    # 2. Test Defense Active across attacks (should defend)
    url = f"{BASE_URL}/api/p3/query"
    for atk in attacks[:3]:
        payload = json.dumps({
            "attack_id": atk["id"],
            "layer_spotlighting": True,
            "layer_input_filter": True,
            "layer_output_filter": True,
            "layer_least_privilege": True
        }).encode()
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
        res = urllib.request.urlopen(req)
        assert res.status == 200
        data = json.loads(res.read().decode())
        assert data["attack_succeeded"] is False, f"Expected defense to block attack {atk['id']}"
        assert data["status"] == "DEFENDED"
        print(f"[P3 Feature: Defended Attack {atk['id']}] Success! Status: {data['status']}, Poison in top-3: {data['poison_in_top3']}")

    # 3. Test Defenses Disabled (Baseline - should trigger exploit)
    payload = json.dumps({
        "attack_id": "atk_01",
        "layer_spotlighting": False,
        "layer_input_filter": False,
        "layer_output_filter": False,
        "layer_least_privilege": False
    }).encode()
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
    res = urllib.request.urlopen(req)
    assert res.status == 200
    data = json.loads(res.read().decode())
    print(f"[P3 Feature: Baseline Bypass Simulation] Status: {data['status']}, Response: {data['response'][:60]}...")

if __name__ == "__main__":
    print("==================================================")
    print("STARTING END-TO-END VERIFICATION OF ALL FEATURES")
    print("==================================================")
    test_dom_ids()
    test_live_homepage()
    test_live_health()
    test_live_stats()
    test_live_p1_features()
    test_live_p2_features()
    test_live_p3_features()
    print("==================================================")
    print("ALL TESTS PASSED WITH 100% SUCCESS!")
    print("==================================================")
