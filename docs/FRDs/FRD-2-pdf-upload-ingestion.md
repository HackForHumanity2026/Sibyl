# Feature Requirements Document: FRD 2 -- PDF Upload & Ingestion (v1.0)

| Field | Value |
|---|---|
| **Project** | Sibyl |
| **Parent Document** | [PRD v0.3](../PRD.md) |
| **FRD Order** | [FRD Order](../FRD-order.md) |
| **PRD Sections** | 4.1 (PDF Upload and Ingestion), 7.2 (Home Page) |
| **Type** | Feature |
| **Depends On** | FRD 0 (Setup Document), FRD 1 (RAG Pipeline) |
| **Delivers** | Home page UI, PDF upload endpoint, PyMuPDF4LLM parsing, content storage, RAG embedding, background processing |
| **Created** | 2026-02-09 |

---

## Summary

FRD 2 delivers the user-facing entry point to Sibyl: a home page with a hero section and drag-and-drop PDF upload zone, backed by a FastAPI upload endpoint, PyMuPDF4LLM-based PDF parsing, Redis background task processing, and integration with the RAG pipeline (FRD 1) for content chunking and embedding. When a user drops a sustainability report PDF onto the upload zone, the system stores the original binary, enqueues a background task that parses the PDF into structured markdown (preserving tables, headings, and page numbers), stores the parsed content in the `reports` table, generates a content structure preview (sections, page count, detected tables), and chunks and embeds the content into pgvector via the RAG pipeline. The frontend displays real-time upload progress and parsing status via polling, and renders a content structure preview once parsing completes. The user can then initiate analysis from the preview (future FRDs).

---

## Given Context (Preconditions)

The following are assumed to be in place from FRD 0 and FRD 1:

| Prerequisite | Source FRD | Deliverable |
|---|---|---|
| Docker Compose with PostgreSQL 17 + pgvector, Redis, backend, frontend | FRD 0 | `docker-compose.yml` |
| `Report` SQLAlchemy model with all columns (`filename`, `file_size_bytes`, `page_count`, `status`, `parsed_content`, `pdf_binary`, `content_structure`, `error_message`) | FRD 0 | `app/models/report.py` |
| Async database engine and session factory | FRD 0 | `app/core/database.py` |
| FastAPI app with CORS, API router at `/api/v1` | FRD 0 | `app/main.py` |
| Upload route stub (`app/api/routes/upload.py`) | FRD 0 | Empty `APIRouter` |
| Upload schema stub (`app/schemas/upload.py`) | FRD 0 | Empty file |
| PDF parser service stub (`app/services/pdf_parser.py`) | FRD 0 | Empty file |
| Settings with `MAX_UPLOAD_SIZE_MB`, `REDIS_URL` | FRD 0 | `app/core/config.py` |
| Redis service running | FRD 0 | Docker Compose `redis` service |
| Frontend layout shell (`AppShell`, `Sidebar`, `Header`) | FRD 0 | `src/components/Layout/` |
| `HomePage` page stub with routing at `/` | FRD 0 | `src/pages/HomePage.tsx` |
| Upload component directory (`src/components/Upload/`) | FRD 0 | Empty barrel `index.ts` |
| `Report` and `ReportStatus` TypeScript types | FRD 0 | `src/types/report.ts` |
| API client stub (`src/services/api.ts`) | FRD 0 | Base URL, fetch wrapper, `uploadReport()` stub |
| `RAGService.ingest_report()` method | FRD 1 | Chunks, embeds, and stores report content in pgvector |
| Report hierarchical chunking strategy | FRD 1 | 500-800 token chunks with section headers, page numbers, table preservation |
| Embedding service | FRD 1 | `text-embedding-3-small` via OpenRouter |
| `pymupdf4llm` installed in backend requirements | FRD 0 | `requirements.txt` |

### Terms

| Term | Definition |
|---|---|
| PyMuPDF4LLM | A Python library that extracts structured markdown from PDF files, preserving tables, headings, and page boundaries |
| Content structure | A JSON summary of the parsed document's organization: detected sections, page count, table count, and section hierarchy |
| Upload zone | A drag-and-drop area on the home page where users drop PDF files to begin analysis |
| Background task | A unit of work enqueued in Redis and processed asynchronously by the backend, decoupling the HTTP response from long-running parsing and embedding operations |
| Polling | A frontend pattern where the client periodically requests the current status of a long-running operation until it reaches a terminal state |

---

## Executive Summary (Gherkin-Style)

```gherkin
Feature: PDF Upload & Ingestion

  Background:
    Given  FRD 0 and FRD 1 are complete
    And    all services are running (backend, frontend, PostgreSQL, Redis)
    And    the IFRS/SASB corpus has been ingested into the RAG pipeline

  Scenario: View the home page
    When   a user navigates to http://localhost:5173
    Then   the browser renders the home page with a hero section
    And    a drag-and-drop upload zone is prominently displayed
    And    the hero section contains the project name, tagline, and a brief description
    And    the upload zone shows instructional text and a file input fallback

  Scenario: Upload a valid PDF via drag-and-drop
    Given  the user is on the home page
    When   the user drags a PDF file onto the upload zone
    Then   the upload zone shows visual feedback (hover state with highlight)
    When   the user drops the file
    Then   the file is uploaded to the backend via POST /api/v1/upload
    And    the upload zone transitions to a progress indicator
    And    the progress indicator shows the current processing status

  Scenario: Upload a valid PDF via file picker
    Given  the user is on the home page
    When   the user clicks the upload zone
    Then   a file picker dialog opens filtered to PDF files
    When   the user selects a PDF file
    Then   the upload behaves identically to the drag-and-drop flow

  Scenario: Backend receives a PDF upload
    When   the backend receives a PDF file via POST /api/v1/upload
    Then   it validates the file type (application/pdf) and size (≤ 50MB)
    And    it creates a Report record with status "uploaded"
    And    it stores the PDF binary in the Report record
    And    it enqueues a background parsing task in Redis
    And    it returns the report ID and status to the frontend immediately

  Scenario: Background PDF parsing
    Given  a parsing task is dequeued from Redis
    When   the parser processes the PDF
    Then   it sets the report status to "parsing"
    And    it uses PyMuPDF4LLM to extract structured markdown
    And    it preserves tables, headings, and page number boundaries
    And    it stores the parsed markdown in the Report's parsed_content column
    And    it stores the page count in the Report's page_count column
    And    it generates a content structure summary (sections, table count, page count)
    And    it stores the content structure in the Report's content_structure column

  Scenario: Background RAG embedding
    Given  the PDF has been parsed successfully
    When   the parser completes markdown extraction
    Then   it calls RAGService.ingest_report() with the parsed content
    And    the RAG pipeline chunks the content using hierarchical chunking
    And    the chunks are embedded and stored in pgvector
    And    the report status is set to "parsed"

  Scenario: Frontend displays parsing progress
    Given  a PDF has been uploaded
    When   the frontend polls GET /api/v1/upload/{reportId}/status
    Then   it receives the current report status
    And    the progress indicator updates to reflect: uploaded → parsing → parsed
    And    once status is "parsed", the content structure preview is displayed

  Scenario: Content structure preview
    Given  parsing is complete and status is "parsed"
    When   the frontend renders the content preview
    Then   it displays the document's detected sections as a tree
    And    it shows the total page count
    And    it shows the number of detected tables
    And    it shows a "Begin Analysis" button (disabled until FRD 3+)

  Scenario: Reject invalid file type
    When   the user drops a non-PDF file onto the upload zone
    Then   the frontend shows an error message: "Only PDF files are accepted"
    And    no upload request is sent to the backend

  Scenario: Reject oversized file
    When   the user drops a PDF file exceeding 50MB
    Then   the frontend shows an error message: "File exceeds the 50MB size limit"
    And    no upload request is sent to the backend

  Scenario: Handle parsing failure
    Given  a PDF has been uploaded and parsing begins
    When   PyMuPDF4LLM encounters an error during parsing
    Then   the report status is set to "error"
    And    the error message is stored in the Report's error_message column
    And    the frontend displays a user-friendly error with a retry option

  Scenario: Navigate to analysis after upload
    Given  parsing is complete and the content preview is displayed
    When   the user clicks "Begin Analysis"
    Then   the application navigates to /analysis/{reportId}
```

---

## Table of Contents

1. [Home Page UI](#1-home-page-ui)
2. [Upload Components](#2-upload-components)
3. [Backend Upload Endpoint](#3-backend-upload-endpoint)
4. [PDF Parser Service](#4-pdf-parser-service)
5. [Background Task Processing](#5-background-task-processing)
6. [RAG Integration](#6-rag-integration)
7. [Upload Status Endpoint](#7-upload-status-endpoint)
8. [Frontend Polling and State Management](#8-frontend-polling-and-state-management)
9. [Upload Schemas](#9-upload-schemas)
10. [Error Handling](#10-error-handling)
11. [Exit Criteria](#11-exit-criteria)
12. [Appendix A: Content Structure Schema](#appendix-a-content-structure-schema)
13. [Appendix B: PyMuPDF4LLM Output Examples](#appendix-b-pymupdf4llm-output-examples)
14. [Appendix C: Upload Flow Sequence Diagram](#appendix-c-upload-flow-sequence-diagram)
15. [Design Decisions Log](#design-decisions-log)

---

## 1. Home Page UI

### 1.1 Overview

The home page (`src/pages/HomePage.tsx`) is the landing page and primary entry point for Sibyl. It replaces the FRD 0 placeholder with a fully designed page containing two zones: a hero section and an upload zone. The page follows the design system established in FRD 0 (dark theme, detective aesthetic) and the layout described in PRD Section 7.2.

### 1.2 Hero Section

The hero section occupies the upper portion of the home page and shall:

1. Display the project name **"Sibyl"** as a large, prominent heading.
2. Display a tagline below the project name (e.g., "AI-Powered Sustainability Report Verification").
3. Display a brief one-paragraph explanation of what Sibyl does -- how it ingests sustainability report PDFs, dispatches investigative AI agents, and produces an IFRS S1/S2 compliance mapping with disclosure gap analysis.
4. Use the design system typography: project name as H1, tagline as subtitle text, description as body text.
5. Be horizontally centered within the main content area.
6. Include sufficient vertical padding to give the page a spacious, modern feel.

### 1.3 Upload Zone Placement

The upload zone is positioned below the hero section, horizontally centered, and prominently sized to be the obvious next action. It occupies a maximum width of approximately 600px and has generous vertical padding.

### 1.4 Page States

The home page transitions through the following states based on upload activity:

| State | Display |
|---|---|
| **Idle** | Hero section + upload zone (drag-and-drop area) |
| **Uploading** | Hero section + upload progress indicator (file upload in progress) |
| **Processing** | Hero section + processing status (parsing and embedding in progress) |
| **Preview** | Hero section + content structure preview with "Begin Analysis" button |
| **Error** | Hero section + error message with retry option |

State transitions are driven by the upload response and subsequent status polling.

---

## 2. Upload Components

### 2.1 Component Overview

Three components in `src/components/Upload/` handle the upload flow:

| Component | File | Responsibility |
|---|---|---|
| `UploadZone` | `UploadZone.tsx` | Drag-and-drop area with file validation and upload triggering |
| `UploadProgress` | `UploadProgress.tsx` | Progress display during file upload and backend processing |
| `ContentPreview` | `ContentPreview.tsx` | Preview of parsed document structure after processing completes |

### 2.2 UploadZone (`src/components/Upload/UploadZone.tsx`)

The upload zone is a large interactive drop target for PDF files.

**Visual design:**

1. A bordered region (dashed border, rounded corners) with a document/upload icon centered inside.
2. Instructional text: **"Drop a sustainability report PDF here"** as primary text, and **"or click to browse"** as secondary text below.
3. A note beneath the instructions: "PDF files up to 50MB".
4. On hover (mouse or drag-over), the border highlights and the background subtly changes to indicate the drop target is active.
5. On drag-over with a valid file, the zone shows a "Drop to upload" state with an accent-colored border.
6. On drag-over with an invalid file, the zone shows a red border with "Only PDF files are accepted".

**Functional requirements:**

The system shall:

1. Accept files via drag-and-drop (using the HTML Drag and Drop API: `onDragOver`, `onDragLeave`, `onDrop` events).
2. Accept files via a hidden `<input type="file" accept=".pdf,application/pdf">` triggered by clicking the zone.
3. Validate the dropped/selected file before uploading:
   - **File type:** Must be `application/pdf` or have a `.pdf` extension. Reject all other types with an inline error message.
   - **File size:** Must be ≤ 50MB (`MAX_UPLOAD_SIZE_MB` from settings). Reject oversized files with an inline error message showing the actual file size.
   - **File count:** Accept only a single file. If multiple files are dropped, show an inline error message: "Please upload one file at a time".
4. On successful validation, call the `onUpload(file: File)` callback prop to initiate the upload.
5. Be disabled (visually and functionally) while an upload is in progress.

**Props:**

```typescript
interface UploadZoneProps {
  onUpload: (file: File) => void;
  disabled?: boolean;
  maxSizeMB?: number;  // Default: 50
}
```

### 2.3 UploadProgress (`src/components/Upload/UploadProgress.tsx`)

The progress component displays the current state of the upload and processing pipeline.

**Visual design:**

1. A card or panel replacing the upload zone after a file is submitted.
2. Displays the filename and file size at the top.
3. A multi-step progress indicator showing the pipeline stages:
   - **Step 1: Uploading** -- File transfer to the server
   - **Step 2: Parsing** -- PDF content extraction (PyMuPDF4LLM)
   - **Step 3: Embedding** -- Content chunking and vector embedding (RAG pipeline)
4. The current step is highlighted with an animated indicator (pulsing dot or spinner).
5. Completed steps show a checkmark icon.
6. If an error occurs, the failed step shows an error icon with the error message.

**Functional requirements:**

The system shall:

1. Accept the current report status and render the appropriate step as active.
2. Map report statuses to progress steps:

| Report Status | Active Step | Description |
|---|---|---|
| `uploaded` | Step 1 (Uploading) | File received, queued for parsing |
| `parsing` | Step 2 (Parsing) | PDF extraction in progress |
| `parsed` | All complete | Content extracted and embedded |
| `error` | Failed step | Display error message |

3. Show a subtle animation on the active step to indicate ongoing processing.
4. Display elapsed time since upload started (updated every second via `setInterval`).

**Props:**

```typescript
interface UploadProgressProps {
  filename: string;
  fileSizeBytes: number;
  status: ReportStatus;
  errorMessage?: string | null;
  startedAt: Date;
}
```

### 2.4 ContentPreview (`src/components/Upload/ContentPreview.tsx`)

The content preview component displays the structure of the parsed document.

**Visual design:**

1. A card or panel displaying the parsed document's structural summary.
2. At the top: the filename and a summary line (e.g., "142 pages · 12 sections · 8 tables").
3. A collapsible section tree showing the document's hierarchical structure:
   - H1 headings as top-level items
   - H2 headings nested below their parent H1
   - H3 headings nested below their parent H2
   - Each item shows its page number(s)
4. At the bottom: a prominent "Begin Analysis" button that navigates to the Analysis page.

**Functional requirements:**

The system shall:

1. Accept the `ContentStructure` data from the report status response.
2. Render sections as a collapsible tree using disclosure/accordion components from shadcn/ui.
3. Show summary statistics: total pages, total sections, total detected tables.
4. Render a "Begin Analysis" button that navigates to `/analysis/{reportId}`.
5. The "Begin Analysis" button is functionally enabled but will lead to a stub page until FRD 3+ delivers the analysis pipeline. This is acceptable -- the button establishes the navigation flow.

**Props:**

```typescript
interface ContentPreviewProps {
  reportId: string;
  filename: string;
  contentStructure: ContentStructure;
  pageCount: number;
}
```

---

## 3. Backend Upload Endpoint

### 3.1 Endpoint Definition

The upload route (`app/api/routes/upload.py`) replaces the FRD 0 stub with a functional endpoint:

```
POST /api/v1/upload

Content-Type: multipart/form-data
Body: file (PDF binary)

Response 201:
{
  "report_id": "uuid-...",
  "filename": "sustainability-report-2024.pdf",
  "file_size_bytes": 8432156,
  "status": "uploaded",
  "created_at": "2026-02-09T14:30:00Z"
}

Response 400 (invalid file type):
{
  "detail": "Invalid file type. Only PDF files are accepted."
}

Response 400 (file too large):
{
  "detail": "File exceeds the maximum size of 50MB."
}

Response 500 (server error):
{
  "detail": "An error occurred while processing the upload."
}
```

### 3.2 Upload Processing Flow

The system shall:

1. Accept the uploaded file as a FastAPI `UploadFile` parameter.
2. Validate the file:
   - **Content type:** Must be `application/pdf`. Also accept `application/octet-stream` if the filename ends with `.pdf` (some browsers send the generic type).
   - **File size:** Read the file content and verify it does not exceed `settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024` bytes. FastAPI does not enforce upload size limits by default, so this must be checked after reading.
   - **Non-empty:** The file must have content (size > 0 bytes).
3. Create a `Report` record in the database:
   - `filename`: Original filename from the upload
   - `file_size_bytes`: Size of the uploaded content
   - `status`: `"uploaded"`
   - `pdf_binary`: The raw PDF bytes
   - All other fields remain at their defaults (null/initial values)
4. Enqueue a background parsing task in Redis with the `report_id`.
5. Return a `201 Created` response with the report ID, filename, file size, status, and creation timestamp.
6. The response is returned immediately -- parsing happens asynchronously in the background task.

### 3.3 File Reading Strategy

The system shall:

1. Read the entire file into memory using `await file.read()`.
2. For MVP (50MB max), this is acceptable. A streaming approach is not required for hackathon scope.
3. After reading, seek back to the beginning if needed for further processing.

---

## 4. PDF Parser Service

### 4.1 Overview

The PDF parser service (`app/services/pdf_parser.py`) replaces the FRD 0 stub with a functional service that uses PyMuPDF4LLM to extract structured markdown from PDF files.

### 4.2 Functional Requirements

The system shall provide a `PDFParserService` class with the following interface:

```python
class PDFParserService:
    async def parse_pdf(self, pdf_bytes: bytes) -> ParseResult:
        """Parse a PDF binary into structured markdown.

        Args:
            pdf_bytes: Raw PDF file content.

        Returns:
            ParseResult with markdown content, page count, and content structure.

        Raises:
            PDFParseError: If the PDF cannot be parsed.
        """
```

### 4.3 ParseResult Schema

```python
class ParseResult(BaseModel):
    """Result of PDF parsing."""
    markdown: str                     # Full structured markdown text
    page_count: int                   # Total number of pages
    content_structure: ContentStructure  # Structural summary for preview
    page_boundaries: list[PageBoundary]  # Page number to character offset mapping

class ContentStructure(BaseModel):
    """Structural summary of the parsed document."""
    sections: list[SectionInfo]       # Hierarchical section tree
    table_count: int                  # Number of tables detected
    page_count: int                   # Total pages
    estimated_word_count: int         # Approximate word count

class SectionInfo(BaseModel):
    """A section detected in the document."""
    title: str                        # Section heading text
    level: int                        # Heading level (1 = H1, 2 = H2, etc.)
    page_start: int                   # Page where the section begins
    page_end: int | None              # Page where the section ends (null if last section)
    children: list['SectionInfo'] = []  # Nested sub-sections

class PageBoundary(BaseModel):
    """Maps page numbers to character positions in the markdown output."""
    page_number: int                  # 1-indexed page number
    char_start: int                   # Start character offset in the markdown
    char_end: int                     # End character offset in the markdown
```

### 4.4 PyMuPDF4LLM Integration

The system shall:

1. Use `pymupdf4llm.to_markdown()` with the following configuration:
   - `page_chunks=True` -- return output chunked by page for page boundary tracking
   - `write_images=False` -- do not extract images (MVP scope; reduces complexity and storage)
   - `show_progress=False` -- suppress console progress output
2. When `page_chunks=True`, PyMuPDF4LLM returns a list of dictionaries, one per page, each containing:
   - `"text"`: The markdown text for that page
   - `"metadata"`: Page metadata including page number
3. Concatenate the per-page markdown into a single document string, inserting page boundary markers:
   ```
   <!-- PAGE 1 -->
   [markdown content for page 1]

   <!-- PAGE 2 -->
   [markdown content for page 2]
   ```
4. Track page boundaries (character offsets) for each page marker for downstream page-number mapping.

### 4.5 Content Structure Extraction

After parsing, the system shall analyze the markdown output to generate the `ContentStructure`:

1. **Section detection:** Scan the markdown for heading patterns (`# `, `## `, `### `, etc.) and build a hierarchical tree of `SectionInfo` objects.
2. **Table detection:** Count the number of markdown tables (identified by lines containing `|` with a header separator row `|---|`).
3. **Page count:** Derived from the number of page chunks returned by PyMuPDF4LLM.
4. **Word count:** Estimate by splitting the full markdown on whitespace after stripping markdown syntax.

### 4.6 Page Metadata for RAG

The system shall produce a `page_metadata` list suitable for passing to `RAGService.ingest_report()`:

```python
page_metadata = [
    {"page_number": 1, "char_start": 0, "char_end": 2450},
    {"page_number": 2, "char_start": 2451, "char_end": 5100},
    # ...
]
```

This enables the RAG pipeline's hierarchical chunking to tag each chunk with the correct page number(s) for PDF highlighting in FRD 4.

### 4.7 Error Handling

The system shall:

1. Catch PyMuPDF exceptions (corrupt PDFs, password-protected PDFs, empty PDFs) and raise a `PDFParseError` with a user-friendly message.
2. Handle PDFs with no extractable text (scanned/image-only) by checking if the extracted markdown is empty or nearly empty (< 100 characters of non-whitespace text). In this case, raise a `PDFParseError` with the message: "This PDF appears to contain only scanned images. Text-based PDFs are required for analysis."
3. Log parsing duration and page count for monitoring.

---

## 5. Background Task Processing

### 5.1 Overview

PDF parsing and RAG embedding are performed in a background task to keep the upload endpoint responsive. The task is enqueued in Redis and processed by a worker within the backend process.

### 5.2 Task Queue Implementation

The system shall implement a lightweight Redis-based task queue:

1. Use the `redis` Python package (already installed from FRD 0) for direct Redis operations.
2. Define a task queue key: `sibyl:tasks:parse_pdf`.
3. On upload, push the `report_id` to the queue using `LPUSH`.
4. A background worker (running as an `asyncio.Task` started during FastAPI's lifespan) polls the queue using `BRPOP` with a timeout.
5. When a task is dequeued, the worker processes it by calling the parsing pipeline.

**Design rationale:** A full-featured task queue library (Celery, ARQ, Dramatiq) adds unnecessary complexity for MVP. The system processes one report at a time, and a simple Redis list with `BRPOP` provides reliable FIFO processing with blocking dequeue. This can be replaced with a proper task queue in production.

### 5.3 Worker Implementation

The system shall implement a `TaskWorker` class (`app/services/task_worker.py`):

```python
class TaskWorker:
    def __init__(self, redis_client: Redis, db_session_factory, settings: Settings):
        ...

    async def start(self):
        """Start the background worker loop. Called during FastAPI lifespan."""

    async def stop(self):
        """Gracefully stop the worker. Called during FastAPI shutdown."""

    async def process_parse_task(self, report_id: str):
        """Parse a PDF and embed its content."""
```

### 5.4 Parsing Pipeline

When the worker dequeues a task, it executes the following pipeline:

1. **Fetch the report:** Load the `Report` record from the database by `report_id`.
2. **Update status:** Set `status = "parsing"`.
3. **Parse the PDF:** Call `PDFParserService.parse_pdf(report.pdf_binary)`.
4. **Store parsed content:** Update the report:
   - `parsed_content` = the full markdown text
   - `page_count` = total pages
   - `content_structure` = the `ContentStructure` as a JSON dict
5. **Embed the content:** Call `RAGService.ingest_report(report_id, markdown, page_metadata)`.
6. **Update status:** Set `status = "parsed"`.
7. **Error handling:** If any step fails, set `status = "error"` and store the error message in `error_message`.

### 5.5 Lifespan Integration

The system shall register the task worker with FastAPI's lifespan:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    worker = TaskWorker(redis_client, db_session_factory, settings)
    asyncio.create_task(worker.start())

    yield

    # Shutdown
    await worker.stop()
```

### 5.6 Concurrency

For MVP, the worker processes one task at a time (sequential processing). This is sufficient for hackathon scope where reports are uploaded one at a time. The `BRPOP` call blocks until a task is available, consuming no CPU while idle.

---

## 6. RAG Integration

### 6.1 Integration Point

After successful parsing, the background task calls `RAGService.ingest_report()` (implemented in FRD 1) to chunk and embed the report content. This is the only integration point between FRD 2 and the RAG pipeline.

### 6.2 Input to RAG Pipeline

The system shall pass the following to `RAGService.ingest_report()`:

| Parameter | Value | Source |
|---|---|---|
| `report_id` | The report UUID (string) | `Report.id` |
| `markdown_content` | The full parsed markdown text | `PDFParserService.parse_pdf().markdown` |
| `page_metadata` | List of page boundary dicts | `PDFParserService.parse_pdf().page_boundaries` converted to dicts |

### 6.3 Embedding Progress

The RAG pipeline's embedding step may take 10-30 seconds for a 200-page report (depending on chunk count and OpenRouter API latency). The report status remains `"parsing"` during this step. It transitions to `"parsed"` only after embedding is complete. This simplifies the status model at the cost of a less granular progress display -- the user sees "Parsing..." during both extraction and embedding. This is acceptable for MVP.

---

## 7. Upload Status Endpoint

### 7.1 Endpoint Definition

The status endpoint allows the frontend to poll for the current processing state of an uploaded report:

```
GET /api/v1/upload/{reportId}/status

Response 200:
{
  "report_id": "uuid-...",
  "filename": "sustainability-report-2024.pdf",
  "file_size_bytes": 8432156,
  "status": "parsed",
  "page_count": 142,
  "content_structure": {
    "sections": [
      {
        "title": "About This Report",
        "level": 1,
        "page_start": 3,
        "page_end": 5,
        "children": []
      },
      {
        "title": "Environmental Performance",
        "level": 1,
        "page_start": 42,
        "page_end": 78,
        "children": [
          {
            "title": "GHG Emissions",
            "level": 2,
            "page_start": 45,
            "page_end": 56,
            "children": [
              { "title": "Scope 1", "level": 3, "page_start": 46, "page_end": 48, "children": [] },
              { "title": "Scope 2", "level": 3, "page_start": 49, "page_end": 51, "children": [] },
              { "title": "Scope 3", "level": 3, "page_start": 52, "page_end": 56, "children": [] }
            ]
          }
        ]
      }
    ],
    "table_count": 8,
    "page_count": 142,
    "estimated_word_count": 52000
  },
  "error_message": null,
  "created_at": "2026-02-09T14:30:00Z",
  "updated_at": "2026-02-09T14:30:45Z"
}

Response 404:
{
  "detail": "Report not found."
}
```

### 7.2 Response Fields

| Field | Type | Presence | Description |
|---|---|---|---|
| `report_id` | `string` | Always | UUID of the report |
| `filename` | `string` | Always | Original filename |
| `file_size_bytes` | `int` | Always | File size in bytes |
| `status` | `string` | Always | Current processing status |
| `page_count` | `int \| null` | After parsing | Number of pages detected |
| `content_structure` | `object \| null` | After parsing | Structural summary (see Section 4.3) |
| `error_message` | `string \| null` | On error | Error description |
| `created_at` | `string` | Always | ISO 8601 upload timestamp |
| `updated_at` | `string` | Always | ISO 8601 last update timestamp |

### 7.3 Status Transitions

The report status follows a linear progression with an error branch:

```
uploaded ──► parsing ──► parsed
                │
                └──► error
```

| Status | Meaning | Frontend Behavior |
|---|---|---|
| `uploaded` | File stored, queued for parsing | Show "Processing..." with step 1 active |
| `parsing` | PyMuPDF4LLM extraction and RAG embedding in progress | Show "Parsing..." with step 2 active |
| `parsed` | Content extracted, chunked, and embedded | Show content preview; stop polling |
| `error` | Processing failed | Show error message with retry button; stop polling |

Note: The `analyzing` and `completed` statuses (defined in FRD 0's Report model) are used by FRD 3+ and are not relevant to this FRD's upload flow.

---

## 8. Frontend Polling and State Management

### 8.1 Upload Hook (`src/hooks/useUpload.ts`)

The system shall implement a custom React hook that manages the entire upload lifecycle:

```typescript
interface UseUploadReturn {
  // State
  uploadState: 'idle' | 'uploading' | 'processing' | 'complete' | 'error';
  report: ReportStatus | null;
  error: string | null;

  // Actions
  uploadFile: (file: File) => Promise<void>;
  retry: () => void;
  reset: () => void;
}

function useUpload(): UseUploadReturn;
```

### 8.2 Upload Flow (inside `useUpload`)

1. **Upload phase:** When `uploadFile(file)` is called:
   - Set state to `'uploading'`.
   - Send `POST /api/v1/upload` with the file as `multipart/form-data`.
   - On success, store the returned `report_id` and transition to `'processing'`.
   - On failure, set state to `'error'` with the error message.

2. **Polling phase:** When state is `'processing'`:
   - Start polling `GET /api/v1/upload/{reportId}/status` every **2 seconds**.
   - On each poll response:
     - Update the `report` state with the latest status data.
     - If status is `"parsed"`, transition to `'complete'` and stop polling.
     - If status is `"error"`, transition to `'error'` and stop polling.
   - Implement a maximum poll count of **150** (5 minutes at 2-second intervals) to prevent infinite polling. If exceeded, transition to `'error'` with a timeout message.

3. **Retry:** Clear the error state and re-enqueue the parsing task by calling a retry endpoint (or re-upload the file).

4. **Reset:** Return to the `'idle'` state, clearing all upload data.

### 8.3 Polling Implementation

The system shall use `setInterval` (or `useEffect` with a timeout) for polling:

1. Poll requests use a simple `GET` fetch with no caching.
2. If a poll request fails (network error), log the error but continue polling -- transient network issues should not abort the flow.
3. Stop polling when the state reaches a terminal state (`'complete'` or `'error'`).
4. Clean up the interval on component unmount.

---

## 9. Upload Schemas

### 9.1 Backend Schemas (`app/schemas/upload.py`)

The system shall define the following Pydantic response schemas, replacing the FRD 0 stub:

```python
class UploadResponse(BaseModel):
    """Response after successful file upload."""
    report_id: str
    filename: str
    file_size_bytes: int
    status: str
    created_at: datetime

class ReportStatusResponse(BaseModel):
    """Response for report status polling."""
    report_id: str
    filename: str
    file_size_bytes: int
    status: str
    page_count: int | None = None
    content_structure: dict | None = None
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime
```

### 9.2 Frontend Types

The system shall update the existing `src/types/report.ts` to include:

```typescript
// Extends the existing ReportStatus type from FRD 0
interface ContentStructure {
  sections: SectionInfo[];
  table_count: number;
  page_count: number;
  estimated_word_count: number;
}

interface SectionInfo {
  title: string;
  level: number;
  page_start: number;
  page_end: number | null;
  children: SectionInfo[];
}

interface UploadResponse {
  report_id: string;
  filename: string;
  file_size_bytes: number;
  status: ReportStatus;
  created_at: string;
}

interface ReportStatusResponse {
  report_id: string;
  filename: string;
  file_size_bytes: number;
  status: ReportStatus;
  page_count: number | null;
  content_structure: ContentStructure | null;
  error_message: string | null;
  created_at: string;
  updated_at: string;
}
```

### 9.3 API Client Methods (`src/services/api.ts`)

The system shall replace the FRD 0 stubs with functional implementations:

```typescript
async function uploadReport(file: File): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${BASE_URL}/upload`, {
    method: 'POST',
    body: formData,
    // Note: Do NOT set Content-Type header; the browser sets it
    // automatically with the correct multipart boundary
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Upload failed');
  }

  return response.json();
}

async function getReportStatus(reportId: string): Promise<ReportStatusResponse> {
  const response = await fetch(`${BASE_URL}/upload/${reportId}/status`);

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to get report status');
  }

  return response.json();
}
```

---

## 10. Error Handling

### 10.1 Frontend Validation Errors

Errors caught by the frontend before any network request:

| Error | Trigger | User Message |
|---|---|---|
| Invalid file type | Non-PDF file selected/dropped | "Only PDF files are accepted." |
| File too large | File exceeds 50MB | "File exceeds the 50MB size limit. Your file is {size}MB." |
| Multiple files | More than one file dropped | "Please upload one file at a time." |

These are displayed inline below the upload zone and clear when the user attempts a new upload.

### 10.2 Backend Validation Errors

Errors returned by the upload endpoint (HTTP 400):

| Error | Trigger | Response |
|---|---|---|
| Invalid content type | File is not `application/pdf` | `{"detail": "Invalid file type. Only PDF files are accepted."}` |
| File too large | File exceeds `MAX_UPLOAD_SIZE_MB` | `{"detail": "File exceeds the maximum size of 50MB."}` |
| Empty file | File has 0 bytes | `{"detail": "The uploaded file is empty."}` |

### 10.3 Processing Errors

Errors that occur during background processing:

| Error | Trigger | Stored In | User Message |
|---|---|---|---|
| Corrupt PDF | PyMuPDF4LLM cannot parse the file | `Report.error_message` | "The uploaded PDF could not be parsed. The file may be corrupt." |
| Password-protected PDF | PDF requires a password | `Report.error_message` | "This PDF is password-protected. Please upload an unprotected version." |
| Scanned/image-only PDF | No extractable text | `Report.error_message` | "This PDF appears to contain only scanned images. Text-based PDFs are required for analysis." |
| Embedding failure | OpenRouter API error during RAG embedding | `Report.error_message` | "An error occurred while processing the document. Please try again." |
| Unknown error | Any other exception | `Report.error_message` | "An unexpected error occurred. Please try again." |

All processing errors set the report status to `"error"` and store a descriptive message in `error_message`.

### 10.4 Retry Mechanism

The system shall provide a retry endpoint:

```
POST /api/v1/upload/{reportId}/retry

Response 200:
{
  "report_id": "uuid-...",
  "status": "uploaded",
  "message": "Report has been re-queued for processing."
}

Response 400:
{
  "detail": "Report is not in an error state."
}

Response 404:
{
  "detail": "Report not found."
}
```

The retry endpoint shall:

1. Verify the report exists and is in `"error"` status.
2. Reset the report status to `"uploaded"` and clear `error_message`, `parsed_content`, `content_structure`, and `page_count`.
3. Delete any existing embeddings for this report (via `RAGService.delete_report_embeddings()`).
4. Re-enqueue the parsing task in Redis.
5. Return the updated report status.

---

## 11. Exit Criteria

FRD 2 is complete when ALL of the following are satisfied:

| # | Criterion | Verification |
|---|---|---|
| 1 | Home page renders hero section and upload zone | Navigate to `http://localhost:5173` and visually confirm the hero section and upload zone |
| 2 | Drag-and-drop upload works | Drag a PDF onto the upload zone; observe the file is sent to the backend |
| 3 | File picker upload works | Click the upload zone; select a PDF via the dialog; observe the file is uploaded |
| 4 | Invalid file type is rejected | Drop a `.txt` file; observe the error message without any network request |
| 5 | Oversized file is rejected | Drop a >50MB file; observe the error message without any network request |
| 6 | Backend creates a Report record | After upload, query the `reports` table and verify a record exists with status `"uploaded"` and `pdf_binary` populated |
| 7 | Background parsing extracts markdown | After upload, wait for status to change to `"parsed"`; verify `parsed_content` is populated with markdown text |
| 8 | Page count is detected | After parsing, verify `page_count` matches the actual PDF page count |
| 9 | Content structure is generated | After parsing, verify `content_structure` contains sections, table count, and page count |
| 10 | RAG embeddings are created | After parsing, query the `embeddings` table for `source_type = 'report'` and the report's `report_id`; verify chunks exist |
| 11 | Frontend progress indicator works | Upload a PDF and observe the progress indicator cycling through uploading → parsing → complete |
| 12 | Content preview renders | After parsing completes, the content preview shows the document structure, page count, and table count |
| 13 | "Begin Analysis" button navigates | Click "Begin Analysis" and verify the URL changes to `/analysis/{reportId}` |
| 14 | Error handling works | Upload a corrupt or scanned PDF; verify the error status and user-friendly error message |
| 15 | Retry works | After an error, click retry; verify the report is re-queued and reprocessed |
| 16 | Status polling works | Upload a PDF; observe the frontend polls `/status` at 2-second intervals and stops when parsing completes |

---

## Appendix A: Content Structure Schema

### A.1 Full ContentStructure Example

```json
{
  "sections": [
    {
      "title": "About This Report",
      "level": 1,
      "page_start": 3,
      "page_end": 5,
      "children": [
        {
          "title": "Reporting Scope",
          "level": 2,
          "page_start": 3,
          "page_end": 4,
          "children": []
        },
        {
          "title": "Standards and Frameworks",
          "level": 2,
          "page_start": 4,
          "page_end": 5,
          "children": []
        }
      ]
    },
    {
      "title": "Governance",
      "level": 1,
      "page_start": 6,
      "page_end": 18,
      "children": [
        {
          "title": "Board Oversight",
          "level": 2,
          "page_start": 7,
          "page_end": 10,
          "children": []
        },
        {
          "title": "Management Responsibility",
          "level": 2,
          "page_start": 11,
          "page_end": 14,
          "children": []
        },
        {
          "title": "Remuneration and ESG",
          "level": 2,
          "page_start": 15,
          "page_end": 18,
          "children": []
        }
      ]
    },
    {
      "title": "Environmental Performance",
      "level": 1,
      "page_start": 42,
      "page_end": 78,
      "children": [
        {
          "title": "GHG Emissions",
          "level": 2,
          "page_start": 45,
          "page_end": 56,
          "children": [
            {
              "title": "Scope 1 Emissions",
              "level": 3,
              "page_start": 46,
              "page_end": 48,
              "children": []
            },
            {
              "title": "Scope 2 Emissions",
              "level": 3,
              "page_start": 49,
              "page_end": 51,
              "children": []
            },
            {
              "title": "Scope 3 Emissions",
              "level": 3,
              "page_start": 52,
              "page_end": 56,
              "children": []
            }
          ]
        },
        {
          "title": "Energy Consumption",
          "level": 2,
          "page_start": 57,
          "page_end": 62,
          "children": []
        },
        {
          "title": "Water Management",
          "level": 2,
          "page_start": 63,
          "page_end": 68,
          "children": []
        }
      ]
    }
  ],
  "table_count": 8,
  "page_count": 142,
  "estimated_word_count": 52000
}
```

### A.2 ContentStructure Storage

The `content_structure` is stored as a JSONB column on the `reports` table (defined in FRD 0). It is returned directly in the status endpoint response and consumed by the frontend's `ContentPreview` component.

---

## Appendix B: PyMuPDF4LLM Output Examples

### B.1 Heading Extraction

**PDF visual:**
```
ENVIRONMENTAL PERFORMANCE
GHG Emissions
Our total Scope 1 emissions were 2.3 million tonnes CO2e...
```

**PyMuPDF4LLM markdown output:**
```markdown
# ENVIRONMENTAL PERFORMANCE

## GHG Emissions

Our total Scope 1 emissions were 2.3 million tonnes CO2e...
```

### B.2 Table Extraction

**PDF visual:**

| Scope | FY2024 (tCO2e) | FY2023 (tCO2e) | Change (%) |
|---|---|---|---|
| Scope 1 | 2,300,000 | 2,450,000 | -6.1% |
| Scope 2 | 890,000 | 950,000 | -6.3% |
| Scope 3 | 12,400,000 | 12,810,000 | -3.2% |

**PyMuPDF4LLM markdown output:**
```markdown
| Scope | FY2024 (tCO2e) | FY2023 (tCO2e) | Change (%) |
|---|---|---|---|
| Scope 1 | 2,300,000 | 2,450,000 | -6.1% |
| Scope 2 | 890,000 | 950,000 | -6.3% |
| Scope 3 | 12,400,000 | 12,810,000 | -3.2% |
```

### B.3 Page Boundary Markers (Post-Processing)

After PyMuPDF4LLM extraction, the parser inserts page boundary markers:

```markdown
<!-- PAGE 42 -->

# ENVIRONMENTAL PERFORMANCE

Our environmental strategy is guided by...

<!-- PAGE 43 -->

## GHG Emissions

Our total greenhouse gas emissions for FY2024...

| Scope | FY2024 (tCO2e) | FY2023 (tCO2e) | Change (%) |
|---|---|---|---|
| Scope 1 | 2,300,000 | 2,450,000 | -6.1% |
```

These markers are used by the RAG pipeline (FRD 1) to assign page numbers to chunks and by the Claims Agent (FRD 3) to locate claims in the original PDF.

---

## Appendix C: Upload Flow Sequence Diagram

```
User                 Frontend              Backend             Redis          Worker           Database         RAG Service
 │                      │                     │                  │               │                 │                │
 │   Drop PDF           │                     │                  │               │                 │                │
 │─────────────────────►│                     │                  │               │                 │                │
 │                      │  Validate file      │                  │               │                 │                │
 │                      │  (type, size)       │                  │               │                 │                │
 │                      │                     │                  │               │                 │                │
 │                      │  POST /upload       │                  │               │                 │                │
 │                      │────────────────────►│                  │               │                 │                │
 │                      │                     │  Validate file   │               │                 │                │
 │                      │                     │  Create Report   │               │                 │                │
 │                      │                     │─────────────────────────────────────────────────►│                │
 │                      │                     │                  │               │                 │                │
 │                      │                     │  Enqueue task    │               │                 │                │
 │                      │                     │─────────────────►│               │                 │                │
 │                      │                     │                  │               │                 │                │
 │                      │  201 {report_id}    │                  │               │                 │                │
 │                      │◄────────────────────│                  │               │                 │                │
 │                      │                     │                  │               │                 │                │
 │  Show progress       │                     │                  │  BRPOP        │                 │                │
 │◄─────────────────────│                     │                  │──────────────►│                 │                │
 │                      │                     │                  │               │                 │                │
 │                      │                     │                  │               │  Set "parsing"   │                │
 │                      │                     │                  │               │────────────────►│                │
 │                      │                     │                  │               │                 │                │
 │                      │  GET /status        │                  │               │  PyMuPDF4LLM    │                │
 │                      │────────────────────►│                  │               │  parse PDF      │                │
 │                      │  {"status":"parsing"}                  │               │                 │                │
 │                      │◄────────────────────│                  │               │                 │                │
 │                      │                     │                  │               │  Store content   │                │
 │  Update progress     │                     │                  │               │────────────────►│                │
 │◄─────────────────────│                     │                  │               │                 │                │
 │                      │                     │                  │               │  ingest_report() │                │
 │                      │                     │                  │               │───────────────────────────────►│
 │                      │                     │                  │               │                 │   Chunk +      │
 │                      │                     │                  │               │                 │   embed        │
 │                      │                     │                  │               │                 │◄───────────────│
 │                      │                     │                  │               │  Set "parsed"    │                │
 │                      │                     │                  │               │────────────────►│                │
 │                      │                     │                  │               │                 │                │
 │                      │  GET /status        │                  │               │                 │                │
 │                      │────────────────────►│                  │               │                 │                │
 │                      │  {"status":"parsed", content_structure}│               │                 │                │
 │                      │◄────────────────────│                  │               │                 │                │
 │                      │                     │                  │               │                 │                │
 │  Show preview        │                     │                  │               │                 │                │
 │◄─────────────────────│                     │                  │               │                 │                │
```

---

## Design Decisions Log

| Decision | Rationale |
|---|---|
| Simple Redis `LPUSH`/`BRPOP` over Celery/ARQ | A full task queue framework adds configuration complexity (broker, backend, serializer) for a single task type. `BRPOP` provides reliable, blocking, FIFO processing with zero extra dependencies. Sufficient for MVP where reports are processed sequentially. |
| Frontend polling over WebSocket/SSE for upload status | Upload status checking is simple request-response (one status field changes). SSE would require a dedicated connection and event source management for a flow that lasts 10-60 seconds. Polling every 2 seconds is simpler, sufficient, and disposable. SSE is reserved for the detective dashboard (FRD 5) where real-time streaming is genuinely needed. |
| `page_chunks=True` in PyMuPDF4LLM | Returns per-page output, enabling precise page boundary tracking. This is critical for mapping chunks to page numbers and for the PDF viewer highlighting in FRD 4. Without this, page attribution would require heuristic estimation. |
| `write_images=False` in PyMuPDF4LLM | Image extraction adds storage complexity (where to store images, how to reference them from markdown). Charts are preserved as text descriptions by PyMuPDF4LLM. Full image extraction is deferred to post-MVP. |
| Store PDF binary in PostgreSQL `BYTEA` over filesystem/S3 | For hackathon scope (50MB max, single-digit reports), database storage is simplest. Avoids filesystem path management, volume mounts, or S3 configuration. The `pdf_binary` column was defined in FRD 0's Report model. |
| File read fully into memory over streaming | 50MB max file size means full memory read is feasible. Streaming adds complexity (chunked upload handling, temp file management) with no benefit at this scale. |
| Content structure as JSONB over normalized tables | The section tree is read-only metadata used for preview display. Normalizing sections into a separate table would require recursive queries for tree rendering. JSONB stores and retrieves the full tree in one operation. |
| Embedding during parsing step (not a separate status) | Adding an `"embedding"` status between `"parsing"` and `"parsed"` complicates the state machine for minimal user benefit. Users don't need to know the internal difference between text extraction and vector embedding. |
| 2-second polling interval | Balances responsiveness (user sees updates within 2 seconds) against server load (0.5 req/sec per active upload). Parsing takes 10-60 seconds, so the user will see a few polling cycles before completion. |
| Max poll count of 150 (5 minutes) | A 200-page PDF should parse and embed in under 2 minutes. 5 minutes provides generous headroom for slow OpenRouter API responses while preventing infinite polling from zombie uploads. |
| Retry by re-enqueueing over re-uploading | The PDF binary is already stored in the database. Re-uploading wastes bandwidth and time. Retrying simply resets the status and re-enqueues the existing data for reprocessing. |
| `setInterval` polling over React Query/SWR refetch interval | Keeps the implementation simple and dependency-free. React Query's refetch interval would work too, but adds a dependency just for polling. The custom `useUpload` hook is straightforward and self-contained. |
| Page boundary markers as HTML comments (`<!-- PAGE N -->`) | HTML comments are invisible in rendered markdown, don't interfere with markdown parsing, and provide a clean delimiter for page tracking. They're easily stripped if the raw markdown is displayed to users. |
