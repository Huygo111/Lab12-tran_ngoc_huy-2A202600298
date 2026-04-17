# Day 12 Lab - Mission Answers

## Part 1: Localhost vs Production

### Exercise 1.1: Anti-patterns found
1. Line 17-18: API key hardcode

OPENAI_API_KEY = "sk-hardcoded-fake-key-never-do-this"
DATABASE_URL = "postgresql://admin:password123@localhost:5432/mydb"
→ Nếu push lên GitHub, ai cũng thấy password.
2. Line 21: Debug mode luôn bật

DEBUG = True
→ Trên production, debug mode làm lộ stack trace cho user.
3. Line 33-35: Dùng print() và log ra secret

print(f"[DEBUG] Got question: {question}")
print(f"[DEBUG] Using key: {OPENAI_API_KEY}")  # log ra secret!
→ Không có log level, không có format, lại còn in key ra màn hình.
4. Line 42: Không có health check
5. Line 51-53: Port và host cứng

host="localhost",   # chỉ chạy được trên local
port=8000,          # cứng port
reload=True         # debug reload trong production
→ Trong container, localhost không nhận traffic từ bên ngoài. Cloud platform inject PORT qua env var, nếu cứng 8000 sẽ không hoạt động.

### Exercise 1.3: Comparison table
| Feature | Basic | Advanced | Tại sao quan trọng? |
|---------|-------|----------|-----------------|
| Config | Hardcode | Env vars | Không lộ secret lên GitHub |
| Health check | Không có | /health + /ready | Platform tự restart khi crash |
| Logging | print() | JSON structured | Dễ parse, không lộ key |
| Shutdown | Đột ngột | Graceful | Request đang chạy được hoàn thành |

## Part 2: Docker

### Exercise 2.1: Dockerfile questions
1. Base image: python:3.11 — full Python ~1GB
2. Working directory: /app — mọi lệnh sau đều chạy trong này
3. Tại sao COPY requirements.txt trước: Docker cache layer: nếu code thay đổi nhưng requirements không đổi → Docker dùng cache, không cài lại pip → build nhanh hơn
4. CMD vs ENTRYPOINT: CMD có thể bị override khi docker run, ENTRYPOINT thì không. CMD phù hợp cho lệnh mặc định linh hoạt

### Exercise 2.3: Image size comparison

| Image | Disk Usage | Content Size |
|-------|-----------|--------------|
| my-agent:develop | 1.66 GB | 424 MB |
| my-agent:production | 236 MB | 56.6 MB |
| **Giảm** | **~7x nhỏ hơn** | **~7.5x nhỏ hơn** |

| Câu hỏi | Trả lời |
|---------|---------|
| Stage 1 (builder) làm gì? | Cài pip, gcc, libpq-dev để compile dependencies |
| Stage 2 (runtime) làm gì? | Chỉ copy code + packages đã cài từ builder, không có build tools |
| Tại sao image nhỏ hơn? | Stage 2 dùng python:3.11-slim, không có gcc/pip cache/build tools — chỉ giữ thứ cần để chạy |

## Part 3: Cloud Deployment

### Exercise 3.1: Railway deployment
- URL: https://ai-agent-ujf7.onrender.com/
- Screenshot: Screenshot Render deployment.png

## Part 4: API Security

### Exercise 4.1: API Key Authentication

**Câu hỏi & Trả lời:**

| Câu hỏi | Trả lời |
|---------|---------|
| API key được check ở đâu? | Hàm `verify_api_key()` trong `app.py` dùng `APIKeyHeader(name="X-API-Key")` để đọc header, sau đó so sánh với env var `AGENT_API_KEY`. Được inject vào endpoint qua `Depends(verify_api_key)` |
| Điều gì xảy ra nếu sai/thiếu key? | Thiếu key → HTTP 401 `Missing API key`. Sai key → HTTP 403 `Invalid API key` |
| Làm sao rotate key? | Đổi giá trị env var `AGENT_API_KEY` rồi restart app — không cần sửa code |

**Test results:**
```
# Không có key → 401
curl.exe -s http://localhost:8001/ask?question=Hello -X POST
{"detail":"Missing API key. Include header: X-API-Key: <your-key>"}

# Có key đúng → 200
curl.exe -s http://localhost:8001/ask?question=Hello -X POST -H "X-API-Key: secret-key-123"
{"question":"Hello","answer":"Agent đang hoạt động tốt! (mock response) Hỏi thêm câu hỏi đi nhé."}
```

### Exercise 4.2: JWT Authentication

**JWT Flow:**
1. Client gửi `POST /auth/token` với username/password
2. Server verify credentials → tạo JWT token (signed bằng `SECRET_KEY`)
3. Client gửi token trong header `Authorization: Bearer <token>` cho mọi request
4. Server verify signature → extract `username` và `role` từ token → xử lý request

**Test results:**
```
# Lấy token
POST /auth/token {"username":"student","password":"demo123"}
→ access_token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# Dùng token gọi /ask
POST /ask với Authorization: Bearer <token>
→ {"question":"Explain JWT","answer":"..."}
```

**Ưu điểm JWT so với API Key:**

| Tiêu chí | API Key | JWT |
|----------|---------|-----|
| Stateless | Yes | Yes |
| Chứa thông tin user | No | Yes (role, expiry) |
| Có thể expire | No | Yes (60 phút) |
| Phù hợp cho | Internal API | User-facing API |

### Exercise 4.3: Rate Limiting

| Câu hỏi | Trả lời |
|---------|---------|
| Algorithm | Sliding Window Counter — đếm request trong 60 giây gần nhất |
| Limit | user: 10 req/phút, admin: 100 req/phút |
| Bypass cho admin | Role `admin` dùng `rate_limiter_admin` (100 req/phút) thay vì `rate_limiter_user` |

**Test results:**
```
[1] OK - remaining: 9
[2] OK - remaining: 8
...
[10] OK - remaining: 0
[11] RATE LIMITED: 429 - {"error":"Rate limit exceeded","limit":10,"window_seconds":60,"retry_after_seconds":59}
[12] RATE LIMITED: 429 - {"error":"Rate limit exceeded","limit":10,"window_seconds":60,"retry_after_seconds":59}
```

### Exercise 4.4: Cost guard implementation

**Cách hoạt động:**

| Câu hỏi | Trả lời |
|---------|---------|
| Logic check budget | 2 tầng: global ($10/ngày tổng) và per-user ($1/ngày). Vượt → HTTP 402 |
| Reset khi nào? | Mỗi ngày — so sánh `record.day` với ngày hôm nay, khác → tạo record mới |
| Khác CODE_LAB solution? | CODE_LAB dùng Redis (scale được). File này dùng in-memory dict (mất khi restart) |

**Test usage result:**
```
user_id              : student
date                 : 2026-04-17
requests             : 11
input_tokens         : 44
output_tokens        : 326
cost_usd             : 0.000202
budget_usd           : 1.0
budget_remaining_usd : 0.999798
budget_used_pct      : 0.0
```

## Part 5: Scaling & Reliability

### Exercise 5.1: Health Checks

| Endpoint | Loại probe | Mục đích |
|----------|-----------|---------|
| `/health` | Liveness | Platform hỏi "container còn sống không?" → restart nếu fail |
| `/ready` | Readiness | Load balancer hỏi "có nhận traffic không?" → 503 khi startup/shutdown |

**Test results:**
```
GET /health
status         : ok
uptime_seconds : 20.3
version        : 1.0.0
environment    : development
checks         : @{memory=}

GET /ready
ready : True
in_flight_requests : 1
```

### Exercise 5.2: Graceful Shutdown

**Cách hoạt động:**
- App bắt tín hiệu `SIGINT` (Ctrl+C) và `SIGTERM` (platform gửi khi tắt container)
- `lifespan` shutdown: đặt `_is_ready = False`, chờ in-flight requests hoàn thành (tối đa 30 giây)
- Request đang xử lý được hoàn thành trước khi tắt

**Test results:**
```
POST /ask?question=LongTask  → 200 OK (hoàn thành trước khi tắt)
Received signal 2 — uvicorn will handle graceful shutdown
Graceful shutdown initiated...
Shutdown complete
```

**SIGTERM vs SIGKILL:**
| Signal | Có thể bắt? | Platform dùng khi nào? |
|--------|------------|----------------------|
| SIGTERM | Yes | Tắt bình thường — cho app dọn dẹp |
| SIGKILL | No | Force kill sau timeout |

### Exercise 5.3: Stateless Design

**Tại sao stateless quan trọng:**
- Nếu lưu session trong memory: instance 1 có session, instance 2 không có → bug khi scale
- Giải pháp: lưu session trong Redis → mọi instance đều đọc được

**Test results:**
```
# Request 1
Session: 9c351b2c-ce16-4797-8982-084f8495bc88
Served by: instance-b62478

# Request 2 (cùng session)
Turn: 3
Served by: instance-b62478
Storage: in-memory (fallback vì không có Redis)

# History vẫn còn sau 2 turns
session_id: 9c351b2c-ce16-4797-8982-084f8495bc88
messages: [{role=user, content=Hello I am Huy}, ...]
```

**Anti-pattern vs Correct:**
| | Anti-pattern | Stateless |
|-|-------------|-----------|
| Lưu session ở đâu? | `conversation_history = {}` trong memory | Redis với TTL |
| Khi scale 3 instances? | Mỗi instance có memory riêng → mất session | Tất cả đọc chung Redis |
| Restart app? | Mất hết data | Data vẫn còn trong Redis |

### Exercise 5.5: Test Stateless

**Test results:**
```
Session: feea3808-1233-4b2a-bded-ffda6a5c4783
Request 1: [instance-b62478] storage=in-memory
Request 2: [instance-b62478] storage=in-memory
Request 3: [instance-b62478] storage=in-memory
History messages: 6
Instances seen: {'instance-b62478'}
```

**Nhận xét:**
- Chỉ thấy 1 instance vì đang chạy local (không có Docker scale)
- `storage=in-memory` vì không có Redis — nếu có Redis sẽ là `storage=redis`
- History được giữ đúng qua 3 requests (6 messages = 3 user + 3 assistant)
- Với `docker compose up --scale agent=3` + Redis, `instances_seen` sẽ có nhiều instance khác nhau nhưng history vẫn intact