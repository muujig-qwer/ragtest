import logging
import time

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse

from app.config import get_settings
from app.db import MockExecutor, OracleExecutor
from app.logging_utils import setup_logging
from app.models import ChatMeta, ChatRequest, ChatResponse
from app.response_builder import build_mn_answer, mask_row
from app.sql_generator import generate_sql
from app.sql_guard import ensure_row_limit, validate_sql

setup_logging()
logger = logging.getLogger(__name__)
settings = get_settings()

app = FastAPI(title=settings.app_name)


def _get_executor():
    if settings.db_dsn and settings.db_user and settings.db_password:
        return OracleExecutor(
            dsn=settings.db_dsn,
            user=settings.db_user,
            password=settings.db_password,
            timeout_sec=settings.db_timeout_sec,
        )
    return MockExecutor()


def _run_chat(payload: ChatRequest) -> ChatResponse:
    started = time.perf_counter()

    try:
        raw_sql = generate_sql(payload.question, settings.allowed_objects)
        valid_sql = validate_sql(raw_sql, settings.allowed_objects)
        final_sql = ensure_row_limit(valid_sql, settings.default_row_limit)

        executor = _get_executor()
        rows = executor.execute(final_sql)
        masked_rows = [mask_row(r) for r in rows]
        answer = build_mn_answer(masked_rows)

        elapsed_ms = int((time.perf_counter() - started) * 1000)
        logger.info(
            "chat_query question=%r sql=%r row_count=%d latency_ms=%d role=%s",
            payload.question,
            final_sql,
            len(masked_rows),
            elapsed_ms,
            payload.role,
        )

        meta = ChatMeta(
            row_count=len(masked_rows),
            latency_ms=elapsed_ms,
            sql=final_sql if payload.role in {"developer", "admin"} else None,
        )
        return ChatResponse(answer=answer, meta=meta)

    except Exception as exc:
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        logger.exception("chat_failed latency_ms=%d reason=%s", elapsed_ms, str(exc))
        raise HTTPException(status_code=400, detail=f"Хүсэлт боловсруулахад алдаа гарлаа: {exc}")


@app.get("/", response_class=HTMLResponse)
def home() -> str:
    return """
<!doctype html>
<html lang="mn">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Prisoner DB Chat</title>
  <style>
    :root {
      --bg: #f5efe4;
      --panel: #fffaf2;
      --line: #d7c7a7;
      --ink: #231b10;
      --muted: #6f604d;
      --accent: #8c4b1f;
      --accent-2: #c7772d;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: Georgia, "Times New Roman", serif;
      background:
        radial-gradient(circle at top right, rgba(199,119,45,.18), transparent 32%),
        linear-gradient(180deg, #f8f2e8 0%, var(--bg) 100%);
      color: var(--ink);
    }
    .wrap {
      max-width: 920px;
      margin: 48px auto;
      padding: 0 20px;
    }
    .panel {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 20px;
      padding: 24px;
      box-shadow: 0 18px 60px rgba(60, 36, 12, 0.08);
    }
    h1 {
      margin: 0 0 8px;
      font-size: 34px;
      line-height: 1.1;
    }
    p {
      margin: 0 0 18px;
      color: var(--muted);
      font-size: 17px;
      line-height: 1.5;
    }
    textarea {
      width: 100%;
      min-height: 120px;
      resize: vertical;
      border: 1px solid var(--line);
      border-radius: 16px;
      padding: 16px;
      font: inherit;
      font-size: 18px;
      background: #fff;
      color: var(--ink);
    }
    .row {
      display: flex;
      gap: 12px;
      flex-wrap: wrap;
      margin-top: 14px;
    }
    button {
      border: 0;
      border-radius: 999px;
      padding: 12px 18px;
      font: inherit;
      font-size: 16px;
      cursor: pointer;
      background: var(--accent);
      color: #fff8f0;
    }
    .ghost {
      background: transparent;
      color: var(--accent);
      border: 1px solid var(--line);
    }
    .examples {
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
      margin-top: 12px;
    }
    .chip {
      padding: 10px 12px;
      border-radius: 999px;
      border: 1px solid var(--line);
      background: #fff;
      color: var(--ink);
      cursor: pointer;
    }
    .answer {
      margin-top: 20px;
      padding: 18px;
      border-radius: 16px;
      background: #fff;
      border: 1px solid var(--line);
      white-space: pre-wrap;
      line-height: 1.6;
      min-height: 88px;
    }
    .meta {
      margin-top: 12px;
      color: var(--muted);
      font-size: 14px;
    }
  </style>
</head>
<body>
  <div class="wrap">
    <div class="panel">
      <h1>Хоригдлын мэдээлэл асуух чат</h1>
      <p>Асуултаа энгийнээр бич. Жишээ нь: "1607070011 дугаартай хоригдлын ерөнхий мэдээлэл" эсвэл "Хамгийн сүүлд хэн хоригдол суллагдсан бэ?"</p>
      <textarea id="question" placeholder="Энд асуултаа бичнэ үү..."></textarea>
      <div class="row">
        <button id="askButton">Асуух</button>
        <button class="ghost" id="clearButton" type="button">Цэвэрлэх</button>
      </div>
      <div class="examples">
        <button class="chip" type="button" data-question="1607070011 дугаартай хоригдлын ерөнхий мэдээлэл">Ерөнхий мэдээлэл</button>
        <button class="chip" type="button" data-question="Хамгийн сүүлд хэн хоригдол суллагдсан бэ?">Сүүлийн суллалт</button>
        <button class="chip" type="button" data-question="Хөдөлмөр эрхлэлтийн мэдээлэл">Хөдөлмөр эрхлэлт</button>
      </div>
      <div class="answer" id="answer">Хариулт энд гарна.</div>
      <div class="meta" id="meta"></div>
    </div>
  </div>
  <script>
    const question = document.getElementById("question");
    const answer = document.getElementById("answer");
    const meta = document.getElementById("meta");
    const askButton = document.getElementById("askButton");
    const clearButton = document.getElementById("clearButton");

    async function ask() {
      const text = question.value.trim();
      if (!text) {
        answer.textContent = "Асуултаа оруулна уу.";
        meta.textContent = "";
        return;
      }

      askButton.disabled = true;
      answer.textContent = "Хариулт бэлтгэж байна...";
      meta.textContent = "";

      try {
        const response = await fetch("/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ question: text })
        });
        const data = await response.json();
        if (!response.ok) {
          throw new Error(data.detail || "Хүсэлт боловсруулахад алдаа гарлаа.");
        }
        answer.textContent = data.answer;
        meta.textContent = `Олдсон мөр: ${data.meta.row_count} | Хугацаа: ${data.meta.latency_ms} ms`;
      } catch (error) {
        answer.textContent = error.message;
      } finally {
        askButton.disabled = false;
      }
    }

    askButton.addEventListener("click", ask);
    clearButton.addEventListener("click", () => {
      question.value = "";
      answer.textContent = "Хариулт энд гарна.";
      meta.textContent = "";
    });
    question.addEventListener("keydown", (event) => {
      if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {
        ask();
      }
    });

    document.querySelectorAll("[data-question]").forEach((button) => {
      button.addEventListener("click", () => {
        question.value = button.dataset.question;
        ask();
      });
    });
  </script>
</body>
</html>
"""


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "env": settings.app_env}

@app.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest) -> ChatResponse:
    return _run_chat(payload)
