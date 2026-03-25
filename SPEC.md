# Prisoner DB RAG Chatbot - SPEC

## 1. Scope
Энэ баримт нь Oracle DB-д суурилсан RAG chatbot (эхний ээлжид SQL retrieval) хөгжүүлэх MVP болон MCP өргөтгөлийн техникийн хүрээг тодорхойлно.

## 2. Objectives
- Асуултаас Oracle DB-с зөв өгөгдөл retrieve хийх
- Хариуг Монгол хэлээр тайлбарлан буцаах
- Аюулгүй SQL execution guardrail-тэй байх
- Дараагийн шатанд document RAG болон MCP tool orchestration нэмэх

## 3. Phased Delivery

### Phase 0 - Preparation (0.5 day)
- Use-case: 10 бодит асуулт тодорхойлох
- DB allowlist: 5-15 view (table-оос илүү view ашиглах)
- Security baseline:
  - Read-only DB user
  - Row limit: default 200
  - SQL timeout: 8 sec
  - Sensitive field masking policy

### Phase 1 - DB-based RAG MVP (1-2 days)
- API only (`POST /chat`), UI шаардлагагүй
- Flow:
  - User question
  - LLM -> SQL generation (strict rules)
  - Oracle query execution
  - Mongolian response generation
- Guardrails (mandatory):
  - SELECT only
  - Allowlist-only object access
  - WHERE байхгүй үед row limit auto-apply
  - Block keywords/symbols: `;`, `DROP`, `UPDATE`, `DELETE`, `MERGE`
  - Log: question, sql, rowCount, latency
- Output format:
  - 1-3 мөр summary
  - шаардлагатай бол list/table
  - SQL visibility нь role-based (developer vs normal user)
- MVP acceptance:
  - 10 асуултаас >=8 зөв
  - Security rule зөрчихгүй

### Phase 2 - Document RAG (1-2 days)
- Index sources: журам, заавар, тайлан тайлбар, usage guide
- Metadata: төрөл, огноо, байгууллага, section
- Vector store: Qdrant/Chroma (local) эсвэл cloud
- Hybrid routing:
  - Structured data -> SQL retrieval
  - Policy/instruction -> vector retrieval
  - Mixed -> SQL + doc grounding
- Acceptance:
  - журам/баримт төрлийн асуултад source-grounded answer

### Phase 3 - MCP Integration (1 day)
- MCP tools:
  - DB query tool
  - Filesystem tool
  - Browser tool
  - GitHub tool (optional)
- Integration model:
  - MCP servers (stdio/http)
  - Backend/agent acts as MCP client
  - Per-tool permission whitelist
- Acceptance:
  - Question -> tool chain -> reliable answer

### Phase 4 - Product Integration (1-2 days)
- Route: `/admin/ai-chat`
- Chat UI integration
- Role-based access: developer/admin/officer
- Audit log view: question/sql/access

## 4. Architecture (Current MVP)
- Backend: Python + FastAPI
- DB: Oracle via read-only user
- Retrieval mode: SQL retrieval only
- Core modules:
  - Question intake (`POST /chat`)
  - SQL generator
  - SQL validator/sanitizer
  - Oracle query executor
  - Response formatter (MN)
  - Audit logger

## 5. Architecture v2 (Target)

### 5.1 High-Level Flow
```text
User question
  -> API gateway (/chat)
  -> Question router
     -> SQL RAG path
     -> Vector RAG path
     -> Hybrid path
  -> Answer composer
  -> Audit log
```

### 5.2 SQL RAG Path
Зориулалт:
- prisoner profile
- labor history
- release / transfer
- status/count/date-range queries

Flow:
```text
User question
  -> SQL classifier/rules
  -> SQL generation
  -> SQL validation
  -> Oracle allowlist views
  -> Result masking/formatting
  -> Mongolian answer
```

Design rules:
- SELECT only
- allowlist views only
- auto row limit
- timeout + audit log
- developer role-д SQL preview

### 5.3 Vector RAG Path
Зориулалт:
- журам
- заавар
- гарын авлага
- тайлбар материал
- PDF/DOCX/TXT knowledge base

Flow:
```text
Documents
  -> loader
  -> text cleanup
  -> chunking
  -> embeddings
  -> vector DB

User question
  -> query embedding
  -> similarity search
  -> top-k chunks
  -> LLM answer synthesis
  -> source citation
```

Suggested defaults:
- chunk size: 500-800 tokens
- overlap: 50-100 tokens
- top-k retrieval: 3-5
- vector DB: Qdrant or Chroma
- metadata: source, title, page, section, doc_type, updated_at

### 5.4 Hybrid Path
Зориулалт:
- structured data + document explanation хосолсон асуулт

Example:
- "1607070011 дугаартай хоригдлын хөдөлмөр эрхлэлтийн төлөв ямар байна, энэ төлөвийг журамд яаж тайлбарласан бэ?"

Flow:
```text
User question
  -> router detects mixed intent
  -> SQL retrieval for live data
  -> Vector retrieval for policy/guide context
  -> Answer composer merges both
  -> response with citations where relevant
```

### 5.5 MCP Layer
MCP нь retrieval engine биш. Энэ нь tool integration standard.

Target MCP tools:
- DB query tool
- Vector search tool
- Filesystem export/log tool
- Browser tool
- GitHub tool (optional)

Flow:
```text
User question
  -> agent/backend
  -> MCP client
     -> DB tool
     -> Vector search tool
     -> File tool
     -> Browser tool
  -> final response
```

MCP usage goal:
- retrieval logic тогтворжсоны дараа tool orchestration стандартчлах
- permission whitelist-тэй ажиллах
- tool call бүр audit trail-тэй байх

## 6. Implementation Task List

### 6.1 Phase A - Harden SQL RAG
- Allowlist view list final болгох
- 10 use-case evaluation set үүсгэх
- SQL generator-ийг intent-aware болгох
- SQL validator дээр forbidden pattern coverage нэмэх
- PII masking rule-г финал болгох
- Structured JSON audit log нэвтрүүлэх
- Role-based SQL visibility шалгах
- Error responses-ийг user-safe болгох

Definition of done:
- 10 асуултаас 8+ зөв
- forbidden SQL execute болохгүй
- 1 record lookup болон date-range query зөв ажиллах

### 6.2 Phase B - Add Vector RAG
- Index хийх document set батлах
- PDF/DOCX/TXT loader хийх
- Chunking strategy сонгох
- Embedding provider сонгох
- Vector DB сонгох, local/dev setup хийх
- Ingestion script бичих
- Citation format тогтоох
- `/chat` дээр SQL vs Vector router нэмэх

Definition of done:
- document question-д 1-3 source citation-тай хариу өгдөг болох
- retrieval latency acceptable байх

### 6.3 Phase C - Hybrid Routing
- Intent classification rule буюу lightweight classifier нэмэх
- Mixed query detection хийх
- SQL result + document snippets merge logic хийх
- Answer composer дээр sectioned output нэмэх

Definition of done:
- mixed question дээр structured data болон source-grounded explanation хоёуланг нь өгдөг болох

### 6.4 Phase D - MCP Integration
- MCP client strategy сонгох
- DB tool wrapper гаргах
- Vector search tool wrapper гаргах
- File export/log tool wrapper гаргах
- Browser tool use-case тодорхойлох
- Tool-level permissions болон audit trail нэмэх

Definition of done:
- нэг асуулт дээр 1-с олон tool chain найдвартай ажиллах

### 6.5 Phase E - Product Integration
- `/admin/ai-chat` route
- role-based UI
- audit log viewer
- response rendering for summary/table/citations

## 7. Decision Checklist
- SQL-only MVP дээр эхлээд зогсох уу
- Vector RAG-д оруулах document set бэлэн үү
- Embedding provider cloud байх уу, local байх уу
- MCP хэрэгцээ одоо бий юу, эсвэл Phase B/C дууссаны дараа юу
- Admin UI одоо хэрэгтэй юу, эсвэл API-first хэвээр явах уу

## 8. Non-Functional Requirements
- Security-first SQL handling
- Deterministic guardrails
- Observability via structured logs
- Extensible design for MCP adoption

## 9. Risks and Mitigations
- SQL hallucination -> strict validator + allowlist + fallback response
- PII leakage -> masking + role-based redaction
- Slow queries -> timeout + row limit + indexed views
- Incorrect routing (Phase 2) -> classifier threshold + safe fallback
- Weak document chunking -> poor retrieval quality
- MCP overreach -> whitelist + least privilege + audit
- Source staleness -> document versioning and refresh policy

## 10. Immediate Next Actions
1. Allowlist view list баталгаажуулах
2. 10 use-case question-аа final болгох
3. SQL RAG evaluation script болон golden queries бэлдэх
4. Vector RAG-д оруулах document sources жагсаах
5. Qdrant/Chroma-аас нэгийг сонгож dev setup шийдэх
6. MCP-ийг түр хойш тавих эсэхээ шийдэх
