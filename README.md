# Prisoner DB RAG Chatbot (Python MVP)

## Run
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --port 8000
```

## API
- `GET /`
- `GET /health`
- `POST /chat`

Browser UI:
- Open `http://127.0.0.1:8000/`
- Type the question in the input box
- Read the human-friendly answer directly on the page

Normal user example:
```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"question":"1607070011 дугаартай хоригдлын ерөнхий мэдээлэл"}'
```

Another natural-language example:
```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"question":"Хамгийн сүүлд хэн хоригдол суллагдсан бэ?"}'
```

Developer example:
```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"question":"Хамгийн сүүлд хэн хоригдол суллагдсан бэ?","role":"developer"}'
```

## Notes
- `role` is optional. If omitted, it defaults to `user`.
- `.env` дээр Oracle credential өгвөл real query ажиллана.
- Credential хоосон үед mock executor ашиглана.
- MVP guardrails: SELECT-only, allowlist check, row-limit enforcement, sensitive field masking.
