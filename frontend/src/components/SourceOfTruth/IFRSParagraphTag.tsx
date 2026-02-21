/**
 * IFRSParagraphTag - Badge for IFRS paragraph identifiers.
 * Implements FRD 13 Section 6.4.
 */

interface IFRSParagraphTagProps {
  paragraphId: string;
  relevance?: string | null;
}

export function IFRSParagraphTag({ paragraphId, relevance }: IFRSParagraphTagProps) {
  return (
    <span
      className="inline-flex items-center px-1.5 py-0.5 rounded text-xs font-mono bg-muted text-foreground border border-border"
      title={relevance || undefined}
    >
      {paragraphId}
    </span>
  );
}
