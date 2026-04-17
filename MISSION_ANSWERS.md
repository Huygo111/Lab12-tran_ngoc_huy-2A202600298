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
- URL: https://your-app.railway.app
- Screenshot: [Link to screenshot in repo]

## Part 4: API Security

### Exercise 4.1-4.3: Test results
[Paste your test outputs]

### Exercise 4.4: Cost guard implementation
[Explain your approach]

## Part 5: Scaling & Reliability

### Exercise 5.1-5.5: Implementation notes
[Your explanations and test results]