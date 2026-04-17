import json, urllib.request

BASE_URL = "http://localhost:8003"
session_id = None

def post(path, data):
    req = urllib.request.Request(
        f"{BASE_URL}{path}",
        data=json.dumps(data).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())

def get(path):
    with urllib.request.urlopen(f"{BASE_URL}{path}") as r:
        return json.loads(r.read())

questions = ["What is Docker?", "Why containers?", "What is Redis?"]
instances_seen = set()

for i, q in enumerate(questions, 1):
    r = post("/chat", {"question": q, "session_id": session_id})
    if session_id is None:
        session_id = r["session_id"]
        print(f"Session: {session_id}")
    instances_seen.add(r["served_by"])
    print(f"Request {i}: [{r['served_by']}] storage={r['storage']}")

history = get(f"/chat/{session_id}/history")
print(f"History messages: {history['count']}")
print(f"Instances seen: {instances_seen}")
