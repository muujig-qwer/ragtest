# Requirements - Prisoner DB RAG Chatbot

## Functional Requirements

### FR-1 Chat API
- Систем `POST /chat` endpoint-оор хэрэглэгчийн асуулт авна.
- Request body дор хаяж `question` талбартай байна.
- Response нь `answer`, `meta` (optional) талбартай JSON байна.

### FR-2 SQL Generation
- LLM зөвхөн SELECT SQL санал болгоно.
- SQL зөвхөн allowlist-д бүртгэлтэй view/table ашиглана.
- SQL generation prompt нь schema-aware байх.

### FR-3 SQL Validation
- SQL execute хийхээс өмнө validation дамжина.
- Дараахыг хориглоно: `;`, `DROP`, `UPDATE`, `DELETE`, `MERGE`, DDL, multi-statement.
- WHERE clause байхгүй query дээр default row limit автоматаар нэмнэ.

### FR-4 Oracle Execution
- Query read-only Oracle user-аар ажиллана.
- Query timeout 8 секунд.
- Max row limit default 200.

### FR-5 Response Formatting
- Хариу Монгол хэл дээр байна.
- Эхэндээ 1-3 мөр summary өгнө.
- Олон мөртэй бол list эсвэл table форматтай буцаана.
- Developer role-д SQL preview харуулж болно; normal role-д нуусан байна.

### FR-6 Logging and Audit
- Лог дээр хадгална: question, generated_sql, row_count, latency_ms, user_role, timestamp.
- Audit data нь админ хэрэглэгчдэд харагдана.

### FR-7 Security and Privacy
- Sensitive fields (регистр, утас, хаяг, нууц) masking дүрэмтэй байна.
- Role-based access control мөрдөнө.

### FR-8 Accuracy Target
- MVP test set-ийн 10 асуултаас дор хаяж 8-д зөв/хүлээн зөвшөөрөхүйц хариулт өгнө.

## Non-Functional Requirements

### NFR-1 Performance
- P95 API response хугацаа <= 10 секунд (MVP baseline).

### NFR-2 Reliability
- SQL validation fail бол safe error message өгч DB execute хийхгүй.

### NFR-3 Maintainability
- SQL policy/allowlist config code-оос тусдаа manage хийдэг байна.

### NFR-4 Observability
- Structured log формат (JSON) ашиглана.
- Correlation/request ID дэмжинэ.

## Data and Access Requirements
- Allowlist: эхний MVP-д 5-15 view.
- Schema metadata refresh mechanism шаардлагатай (гараар эсвэл scheduled).
- DB connection secret management шаардлагатай.

## Phase 2 Requirements (Document RAG)
- Document ingestion pipeline (PDF/DOCX/TXT) байна.
- Chunking + embeddings + metadata index хийнэ.
- Source citation-тай хариу буцаана.

## Phase 3 Requirements (MCP)
- MCP client integration backend талд байна.
- Tool бүр дээр explicit permission whitelist байна.
- DB/file/browser/github tool chain audit trail-тэй байна.

## Out of Scope (MVP)
- Full-featured web chat UI
- Write-back DB operations
- Autonomous multi-agent workflows

## Acceptance Criteria
1. `/chat` endpoint production-like орчинд ажиллана.
2. Guardrail тестүүд (forbidden SQL, no-WHERE limit, allowlist breach) PASS.
3. 10 use-case evaluation >=80% амжилттай.
4. Audit log-оос query trace бүрэн харагдана.
