# Mock Data Guide for Source of Truth Report

This guide explains how to create mock data for testing the FRD 13 Source of Truth Report without running the full LLM pipeline (avoiding OpenRouter token consumption).

## Overview

Mock data allows you to:

- Test the report UI without waiting for the pipeline
- Develop frontend features independently
- Demo the application without API costs
- Debug report rendering issues

## Process to Add Mock Data Support

### 1. Backend: Add Mock Schema

Add to `backend/app/schemas/report.py`:

```python
class MockSeedResponse(BaseModel):
    """Response from mock data seeding."""

    report_id: str
    claims_created: int
    findings_created: int
    verdicts_created: int
    gaps_created: int
    message: str
```

### 2. Backend: Add Mock Endpoints

Add to `backend/app/api/routes/report.py`:

```python
from app.core.database import generate_uuid7
from app.models.claim import Claim
from app.models.finding import Finding
from app.models.verdict import Verdict
from sqlalchemy import select
from datetime import datetime, timezone

@router.post("/mock", response_model=dict)
async def create_mock_report(
    db: AsyncSession = Depends(get_db),
):
    """Create a mock report record without uploading a PDF.

    For development/testing only - creates a report you can seed with mock data.
    """
    report_id = generate_uuid7()

    report = Report(
        id=report_id,
        filename="mock_sustainability_report_2024.pdf",
        file_size_bytes=1024000,
        status="completed",
        created_at=datetime.now(timezone.utc),
    )
    db.add(report)
    await db.commit()

    return {
        "report_id": str(report_id),
        "message": f"Mock report created. Call POST /api/v1/report/{report_id}/seed-mock to populate.",
    }


@router.post("/{report_id}/seed-mock", response_model=MockSeedResponse)
async def seed_mock_data(
    report_id: str,
    db: AsyncSession = Depends(get_db),
) -> MockSeedResponse:
    """Seed mock data for testing the Source of Truth report."""
    report_uuid = UUID(report_id)
    report = await db.get(Report, report_uuid)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    # Check if data already exists
    existing_claims = await db.execute(
        select(Claim).where(Claim.report_id == report_uuid).limit(1)
    )
    if existing_claims.scalar():
        raise HTTPException(status_code=400, detail="Report already has data")

    # Generate mock data (see Mock Data Templates below)
    claims_created, findings_created, verdicts_created, gaps_created = await create_mock_data(db, report_uuid)

    report.status = "completed"
    await db.commit()

    return MockSeedResponse(
        report_id=report_id,
        claims_created=claims_created,
        findings_created=findings_created,
        verdicts_created=verdicts_created,
        gaps_created=gaps_created,
        message="Mock data seeded successfully.",
    )
```

### 3. Frontend: Add Mock Types

Add to `frontend/src/types/sourceOfTruth.ts`:

```typescript
export interface MockSeedResponse {
  report_id: string;
  claims_created: number;
  findings_created: number;
  verdicts_created: number;
  gaps_created: number;
  message: string;
}
```

### 4. Frontend: Add API Functions

Add to `frontend/src/services/api.ts`:

```typescript
import type { MockSeedResponse } from "@/types/sourceOfTruth";

export async function seedMockReport(
  reportId: string,
): Promise<MockSeedResponse> {
  return fetchAPI<MockSeedResponse>(`/report/${reportId}/seed-mock`, {
    method: "POST",
  });
}

export async function createMockReport(): Promise<{
  report_id: string;
  message: string;
}> {
  return fetchAPI<{ report_id: string; message: string }>(`/report/mock`, {
    method: "POST",
  });
}
```

### 5. Frontend: Add to useReport Hook

Update `frontend/src/hooks/useReport.ts`:

```typescript
import { seedMockReport } from "@/services/api";

// Add to UseReportReturn interface:
seedMock: () => Promise<void>;
seedingMock: boolean;

// Add state:
const [seedingMock, setSeedingMock] = useState(false);

// Add function:
const seedMock = useCallback(async () => {
  if (!reportId) return;
  setSeedingMock(true);
  try {
    await seedMockReport(reportId);
    await fetchReport();
  } catch (err) {
    setError(err instanceof Error ? err.message : "Failed to seed mock data");
  } finally {
    setSeedingMock(false);
  }
}, [reportId, fetchReport]);

// Add to return:
return { ..., seedMock, seedingMock };
```

### 6. Frontend: Add UI Button (Optional)

Add to `frontend/src/pages/ReportPage.tsx` for dev-only button:

```tsx
{
  import.meta.env.DEV && (
    <button
      onClick={seedMock}
      disabled={seedingMock}
      className="px-4 py-2 bg-primary text-primary-foreground rounded-md"
    >
      {seedingMock ? "Seeding..." : "Seed Mock Data"}
    </button>
  );
}
```

---

## Mock Data Templates

### Sample Claims by IFRS Pillar

```python
mock_claims = [
    # Governance
    {
        "claim_text": "The Board's Sustainability Committee has primary oversight for climate matters...",
        "claim_type": "legal_governance",
        "source_page": 12,
        "ifrs_paragraphs": [
            {"paragraph_id": "S2.6", "pillar": "governance", "relevance": "Board oversight"},
        ],
        "priority": "high",
        "verdict": "verified",
        "agents": ["legal", "news_media"],
    },
    # Strategy
    {
        "claim_text": "Our transition plan targets net-zero by 2050 with 42% reduction by 2030...",
        "claim_type": "strategic",
        "source_page": 45,
        "ifrs_paragraphs": [
            {"paragraph_id": "S2.14(a)(iv)", "pillar": "strategy", "relevance": "Transition plan"},
        ],
        "priority": "high",
        "verdict": "verified",
        "agents": ["legal", "academic", "data_metrics"],
    },
    # Risk Management
    {
        "claim_text": "Annual climate risk assessment using TCFD framework...",
        "claim_type": "legal_governance",
        "source_page": 38,
        "ifrs_paragraphs": [
            {"paragraph_id": "S2.25(a)", "pillar": "risk_management", "relevance": "Risk identification"},
        ],
        "priority": "medium",
        "verdict": "verified",
        "agents": ["legal"],
    },
    # Metrics & Targets
    {
        "claim_text": "Scope 1: 450,000 tCO2e. Scope 2: 1.2M tCO2e. Scope 3: 12.4M tCO2e.",
        "claim_type": "quantitative",
        "source_page": 68,
        "ifrs_paragraphs": [
            {"paragraph_id": "S2.29(a)", "pillar": "metrics_targets", "relevance": "GHG emissions"},
        ],
        "priority": "high",
        "verdict": "verified",
        "agents": ["data_metrics", "legal"],
    },
]
```

### Agent Finding Templates

```python
agent_finding_templates = {
    "legal": {
        "evidence_type": "ifrs_compliance",
        "summary_positive": "Claim meets IFRS requirements.",
        "summary_negative": "Claim has compliance gaps.",
    },
    "geography": {
        "evidence_type": "satellite_analysis",
        "summary_positive": "Satellite imagery confirms conditions.",
        "summary_negative": "Satellite imagery contradicts claim.",
    },
    "news_media": {
        "evidence_type": "news_corroboration",
        "summary_positive": "Multiple sources corroborate.",
        "summary_negative": "News reports contradict claim.",
    },
    "academic": {
        "evidence_type": "methodology_validation",
        "summary_positive": "Methodology aligns with standards.",
        "summary_negative": "Methodology deviates from standards.",
    },
    "data_metrics": {
        "evidence_type": "mathematical_consistency",
        "summary_positive": "Figures are mathematically consistent.",
        "summary_negative": "Analysis reveals inconsistencies.",
    },
}
```

### Disclosure Gap Templates

```python
mock_gaps = [
    {
        "paragraph_id": "S1.27(a)(ii)",
        "pillar": "governance",
        "gap_type": "fully_unaddressed",
        "requirement_text": "How the body determines appropriate skills...",
        "materiality_context": "Board competency is critical for oversight.",
        "severity": "high",
    },
    {
        "paragraph_id": "S2.14(c)",
        "pillar": "strategy",
        "gap_type": "fully_unaddressed",
        "requirement_text": "Progress of plans disclosed in prior periods.",
        "materiality_context": "Without progress reporting, stakeholders cannot assess.",
        "severity": "medium",
    },
]
```

---

## Using Mock Data via API

Without code changes, you can seed mock data directly via curl:

```bash
# 1. Create a mock report
curl -X POST http://localhost:8000/api/v1/report/mock

# Response: {"report_id": "uuid-here", "message": "..."}

# 2. Seed mock data into the report
curl -X POST http://localhost:8000/api/v1/report/{report_id}/seed-mock

# 3. View the report
# Open http://localhost:5173/report/{report_id}
```

---

## Important Notes

1. **DEV ONLY**: Mock endpoints should only be available in development
2. **No Pipeline Run**: Mock data bypasses the LLM pipeline entirely
3. **Verdict Distribution**: Include a mix of verdicts (verified, unverified, contradicted, insufficient_evidence)
4. **Gap Types**: Include both `fully_unaddressed` and `partially_addressed` gaps
5. **All Pillars**: Ensure claims exist for all four IFRS pillars
