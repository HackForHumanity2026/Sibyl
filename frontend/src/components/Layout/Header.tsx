import { useLocation } from "react-router-dom";

const pageTitles: Record<string, string> = {
  "/": "Home",
  "/analysis": "Analysis",
  "/report": "Report",
};

function getPageTitle(pathname: string): string {
  // Exact match first
  if (pageTitles[pathname]) {
    return pageTitles[pathname];
  }

  // Check for parameterized routes
  if (pathname.startsWith("/analysis")) {
    return "Analysis";
  }
  if (pathname.startsWith("/report")) {
    return "Report";
  }

  return "Sibyl";
}

export function Header() {
  const location = useLocation();
  const title = getPageTitle(location.pathname);

  return (
    <header className="h-16 border-b border-border bg-background flex items-center justify-between px-6">
      <h1 className="text-xl font-semibold text-foreground">{title}</h1>

      {/* Reserved space for chatbot toggle (FRD 14) */}
      <div className="flex items-center gap-4">
        {/* Placeholder for future chatbot button */}
        <div className="w-10 h-10" aria-hidden="true" />
      </div>
    </header>
  );
}
