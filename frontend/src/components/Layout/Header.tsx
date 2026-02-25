import { NavLink, useLocation } from "react-router-dom";
import { cn } from "@/lib/utils";

interface NavItem {
  label: string;
  path: string;
  exact?: boolean;
}

const navItems: NavItem[] = [
  { label: "Analysis", path: "/analysis" },
  { label: "Report", path: "/report" },
];

function getIsActive(item: NavItem, pathname: string): boolean {
  if (item.exact) {
    return pathname === item.path;
  }
  return pathname.startsWith(item.path);
}

export function Header() {
  const location = useLocation();

  return (
    <header className="relative z-20 h-14 border-b border-border bg-[#fff6e9] flex items-center px-6 shrink-0">
      {/* Logo — acts as home link */}
      <NavLink
        to="/"
        className="font-semibold text-base tracking-tight text-foreground hover:text-foreground/70 transition-colors mr-8"
      >
        Sibyl
      </NavLink>

      {/* Navigation Links */}
      <nav className="flex items-center gap-1">
        {navItems.map((item) => {
          const isActive = getIsActive(item, location.pathname);
          return (
            <NavLink
              key={item.path}
              to={item.path}
              className={cn(
                "px-3 py-1.5 text-sm transition-colors",
                isActive
                  ? "font-semibold text-foreground"
                  : "text-muted-foreground hover:text-foreground"
              )}
            >
              {item.label}
            </NavLink>
          );
        })}
      </nav>

      {/* Right slot — reserved for future utility actions (chatbot toggle, etc.) */}
      <div className="ml-auto flex items-center gap-3">
        {/* Placeholder for chatbot FAB and other utility actions (FRD 14) */}
      </div>
    </header>
  );
}
