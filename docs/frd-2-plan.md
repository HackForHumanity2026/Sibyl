FRD 2: PDF Upload & Ingestion -- Implementation Plan
Current State
FRD 0 and FRD 1 are fully implemented and tested. The following stubs exist from FRD 0 that this plan fills in:

backend/app/api/routes/upload.py -- empty APIRouter
backend/app/schemas/upload.py -- empty file
backend/app/services/pdf_parser.py -- empty file
frontend/src/pages/HomePage.tsx -- placeholder text
frontend/src/components/Upload/index.ts -- empty barrel
frontend/src/services/api.ts -- uploadReport() stub throws
frontend/src/types/report.ts -- ContentStructure missing page_count and estimated_word_count; SectionInfo missing children
frontend/src/hooks/index.ts -- empty
Key infrastructure already in place: Report model with all required columns (pdf_binary, parsed_content, content_structure, page_count, error_message, status), Redis service in Docker, RAGService.ingest_report(), chunk_report(), EmbeddingService, shadcn/ui configured (but no @/lib/utils.ts yet -- needs creation), dark theme CSS variables.

---

Architecture Overview
DB
RAGService
PDFParser
TaskWorker
Redis
UploadAPI
Frontend
User
DB
RAGService
PDFParser
TaskWorker
Redis
UploadAPI
Frontend
User
Drop PDF
Validate type/size
POST /api/v1/upload
Create Report (status=uploaded, pdf_binary)
LPUSH report_id
201 {report_id, status}
Start polling
BRPOP
Set status=parsing
parse_pdf(pdf_bytes)
ParseResult
Store parsed_content, page_count, content_structure
ingest_report(report_id, markdown, page_metadata)
Store embeddings
Set status=parsed
GET /upload/{id}/status
{status=parsed, content_structure}
Show content preview
---

Backend Changes (7 files)
1. Create @/lib/utils.ts for shadcn/ui
Create frontend/src/lib/utils.ts with the standard cn() helper (used by Sidebar already, file is missing).

2. PDF Parser Service -- backend/app/services/pdf_parser.py
Replace stub with a PDFParserService class:

async parse_pdf(pdf_bytes: bytes) -> ParseResult using pymupdf4llm.to_markdown(page_chunks=True, write_images=False, show_progress=False)
ParseResult Pydantic model: markdown, page_count, content_structure: ContentStructure, `page_boundaries: list[PageBoundary]`
ContentStructure model: `sections: list[SectionInfo], `table_count, page_count, estimated_word_count
SectionInfo model: title, level, page_start, page_end, `children: list[SectionInfo]`
Insert <!-- PAGE N --> markers between pages
Build hierarchical section tree from markdown headings
Count tables via |---| pattern
Raise PDFParseError for corrupt / password-protected / image-only PDFs (< 100 chars non-whitespace)
3. Upload Schemas -- backend/app/schemas/upload.py
Replace stub with Pydantic models:

UploadResponse: report_id, filename, file_size_bytes, status, created_at
ReportStatusResponse: report_id, filename, file_size_bytes, status, page_count, content_structure, error_message, created_at, updated_at
4. Upload Routes -- backend/app/api/routes/upload.py
Replace stub with three endpoints:

POST /upload -- accept UploadFile, validate type/size, create Report record, store pdf_binary, LPUSH report_id to Redis queue sibyl:tasks:parse_pdf, return 201
GET /upload/{report_id}/status -- query Report by ID, return ReportStatusResponse (or 404)
POST /upload/{report_id}/retry -- verify report is in error state, reset status to uploaded, clear error/parsed fields, delete existing embeddings via RAGService.delete_report_embeddings(), re-enqueue
5. Task Worker -- new file backend/app/services/task_worker.py
Lightweight Redis-based background worker:

TaskWorker class with start(), stop(), process_parse_task(report_id)
Runs as asyncio.Task started in FastAPI lifespan
Uses BRPOP on sibyl:tasks:parse_pdf with timeout
Pipeline: fetch report -> set parsing -> call PDFParserService.parse_pdf() -> store results -> call RAGService.ingest_report() -> set parsed
On error: set error status with descriptive message
6. Lifespan Integration -- backend/app/main.py
Update the lifespan() function to:

Create a Redis client
Instantiate and start TaskWorker as a background asyncio.Task
Stop the worker on shutdown
7. Dependencies -- backend/app/core/dependencies.py
Add a get_redis() dependency that returns a Redis client (for the upload route to enqueue tasks).

---

Frontend Changes (8 files)
8. Update TypeScript Types -- frontend/src/types/report.ts
Add page_count and estimated_word_count to ContentStructure
Add children: SectionInfo[] to SectionInfo
Add UploadResponse and ReportStatusResponse interfaces per FRD 2 Section 9.2
9. API Client -- frontend/src/services/api.ts
Replace stubs with functional implementations:

uploadReport(file: File): Promise<UploadResponse> -- POST multipart/form-data (no Content-Type header)
getReportStatus(reportId: string): Promise<ReportStatusResponse> -- GET polling endpoint
10. useUpload Hook -- new file frontend/src/hooks/useUpload.ts
Custom hook managing the upload lifecycle:

States: idle, uploading, processing, complete, error
uploadFile(file) calls the API, transitions to processing, starts 2-second polling
Max 150 polls (5 min timeout)
retry() and reset() actions
Cleanup interval on unmount
Export from frontend/src/hooks/index.ts.

11. UploadZone Component -- new file frontend/src/components/Upload/UploadZone.tsx
Drag-and-drop PDF target:

HTML drag/drop API (onDragOver, onDragLeave, onDrop)
Hidden <input type="file" accept=".pdf"> for click-to-browse
Client-side validation: PDF type, max 50MB, single file
Inline error messages
Dashed border, upload icon (lucide-react Upload icon), instructional text
Disabled state during upload
12. UploadProgress Component -- new file frontend/src/components/Upload/UploadProgress.tsx
Multi-step progress indicator:

Three steps: Uploading, Parsing, Embedding
Map ReportStatus to active step
Animated spinner on active step, checkmark on completed
Elapsed time counter
Error display with error icon
13. ContentPreview Component -- new file frontend/src/components/Upload/ContentPreview.tsx
Document structure preview:

Summary line: pages, sections, tables
Collapsible section tree (recursive SectionInfo rendering)
"Begin Analysis" button linking to /analysis/{reportId}
Update frontend/src/components/Upload/index.ts to export all three components.

14. HomePage -- frontend/src/pages/HomePage.tsx
Replace placeholder with full implementation:

Hero section: "Sibyl" heading, tagline, description paragraph
Integrate useUpload hook
Render UploadZone (idle), UploadProgress (uploading/processing), or ContentPreview (complete) based on state
Error state with retry button
---

No Changes Needed
Database schema: Report model already has all columns (FRD 0)
RAGService.ingest_report(): already implemented (FRD 1)
chunk_report(): already implemented (FRD 1)
Docker Compose: Redis already running
pymupdf4llm: already in requirements.txt
redis: already in requirements.txt
---

Testing Strategy
After implementation, test by:

docker compose up -d --build and verify health
Navigate to http://localhost:5174 and verify the hero + upload zone renders
Drop the existing IFRS PDF (docs/ifrs-docs/ifrs-s1.pdf) onto the upload zone
Observe the progress indicator cycling through uploading -> parsing -> complete
Verify content preview shows sections, page count, table count
Verify GET /api/v1/upload/{id}/status returns full content_structure
Verify embeddings exist: GET /api/v1/rag/stats shows report source type
Test error path with a non-PDF file and an oversized file
Test retry endpoint