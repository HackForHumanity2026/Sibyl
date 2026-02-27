/**
 * ChatFab component - Floating action button to open chat panel.
 * Implements FRD 14 (Chatbot) Section 8 - Chat Panel UI.
 */

import { MessageSquare, X } from "lucide-react";
import { cn } from "@/lib/utils";

interface ChatFabProps {
  isOpen: boolean;
  onClick: () => void;
  disabled?: boolean;
}

export function ChatFab({ isOpen, onClick, disabled = false }: ChatFabProps) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={cn(
        "fixed bottom-6 right-6 z-30",
        "w-12 h-12 rounded-full",
        "flex items-center justify-center",
        "shadow-lg hover:shadow-xl border",
        "transition-all duration-200 ease-in-out",
        "hover:scale-105 active:scale-95",
        isOpen
          ? "bg-[#eddfc8] border-[#e0d4bf] text-[#4a3c2e] hover:bg-[#e4d3ba]"
          : "bg-[#4a3c2e] border-[#4a3c2e] text-white hover:bg-[#2d1f14]",
        disabled && "opacity-50 cursor-not-allowed hover:scale-100"
      )}
      aria-label={isOpen ? "Close chat" : "Open chat"}
      aria-expanded={isOpen}
    >
      {isOpen ? (
        <X className="w-5 h-5" />
      ) : (
        <MessageSquare className="w-5 h-5" />
      )}
    </button>
  );
}
