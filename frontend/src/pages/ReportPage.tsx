import { useParams } from "react-router-dom";

export function ReportPage() {
  const { reportId } = useParams<{ reportId?: string }>();

  return (
    <div className="h-full flex flex-col">
      <div className="flex-1 flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-semibold text-foreground mb-4">
            Source of Truth Report
          </h2>
          <p className="text-muted-foreground">
            {reportId
              ? `Compliance report for ${reportId} will appear here`
              : "Source of Truth report will appear here"}
          </p>
          <p className="text-sm text-muted-foreground mt-2">
            Coming in FRD 13
          </p>
        </div>
      </div>
    </div>
  );
}
