import { NavLink, useLocation } from "react-router-dom";
import { FileText, FlaskConical, BookOpen } from "lucide-react";
import { cn } from "@/lib/utils";

function getIsActive(path: string, pathname: string): boolean {
  return pathname.startsWith(path);
}

export function Header() {
  const location = useLocation();
  const analysisActive = getIsActive("/analysis", location.pathname);
  const reportActive = getIsActive("/report", location.pathname);
  const docsActive = getIsActive("/docs", location.pathname);

  return (
    <header className="relative z-20 h-14 border-b border-border bg-[#fff6e9] flex items-center px-6 shrink-0">
      {/* Logo — acts as home link */}
      <NavLink
        to="/"
        className="flex items-center font-semibold text-base tracking-tight text-foreground hover:text-foreground/70 transition-colors mr-8"
        style={{ gap: "2px" }}
      >
        {/* The PNG has transparent padding; -4px margin trims the visual gap */}
        <img
          src="/sibyl-favicon.png"
          alt=""
          className="object-contain"
          style={{ width: 32, height: 32, margin: "-4px -2px -4px -4px" }}
        />
        Sibyl
      </NavLink>

      {/* Spacer */}
      <div className="flex-1" />

      {/* Right slot — Analysis + Report */}
      <nav className="flex items-center gap-1">
        <NavLink
          to="/analysis"
          className={cn(
            "flex items-center gap-1.5 px-3 py-1.5 text-sm transition-colors",
            analysisActive
              ? "font-semibold text-foreground"
              : "text-muted-foreground hover:text-foreground"
          )}
        >
          <FlaskConical size={14} />
          Analysis
        </NavLink>

        <NavLink
          to="/report"
          className={cn(
            "flex items-center gap-1.5 px-3 py-1.5 text-sm transition-colors",
            reportActive
              ? "font-semibold text-foreground"
              : "text-muted-foreground hover:text-foreground"
          )}
        >
          <FileText size={14} />
          Report
        </NavLink>

        <NavLink
          to="/docs"
          className={cn(
            "flex items-center gap-1.5 px-3 py-1.5 text-sm transition-colors",
            docsActive
              ? "font-semibold text-foreground"
              : "text-muted-foreground hover:text-foreground"
          )}
        >
          <BookOpen size={14} />
          Docs
        </NavLink>
      </nav>
    </header>
  );
}
