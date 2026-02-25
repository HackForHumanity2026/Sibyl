import { NavLink, useLocation } from "react-router-dom";
import { FileText } from "lucide-react";
import { cn } from "@/lib/utils";

function getIsActive(path: string, pathname: string): boolean {
  return pathname.startsWith(path);
}

export function Header() {
  const location = useLocation();
  const analysisActive = getIsActive("/analysis", location.pathname);
  const reportActive = getIsActive("/report", location.pathname);

  return (
    <header className="relative z-20 h-14 border-b border-border bg-[#fff6e9] flex items-center px-6 shrink-0">
      {/* Logo — acts as home link */}
      <NavLink
        to="/"
        className="font-semibold text-base tracking-tight text-foreground hover:text-foreground/70 transition-colors mr-8"
      >
        Sibyl
      </NavLink>

      {/* Left nav — primary pages */}
      <nav className="flex items-center gap-1">
        <NavLink
          to="/analysis"
          className={cn(
            "px-3 py-1.5 text-sm transition-colors",
            analysisActive
              ? "font-semibold text-foreground"
              : "text-muted-foreground hover:text-foreground"
          )}
        >
          Analysis
        </NavLink>
      </nav>

      {/* Right slot — Report link + future utilities */}
      <div className="ml-auto flex items-center gap-1">
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
      </div>
    </header>
  );
}
