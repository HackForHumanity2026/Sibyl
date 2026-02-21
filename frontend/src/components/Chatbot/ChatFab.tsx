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
        "w-14 h-14 rounded-full",
        "flex items-center justify-center",
        "shadow-lg hover:shadow-xl",
        "transition-all duration-300 ease-in-out",
        "transform hover:scale-105 active:scale-95",
        isOpen
          ? "bg-gray-700 hover:bg-gray-600 rotate-90"
          : "bg-blue-600 hover:bg-blue-700 rotate-0",
        disabled && "opacity-50 cursor-not-allowed hover:scale-100"
      )}
      aria-label={isOpen ? "Close chat" : "Open chat"}
      aria-expanded={isOpen}
    >
      {isOpen ? (
        <X className="w-6 h-6 text-white" />
      ) : (
        <MessageSquare className="w-6 h-6 text-white" />
      )}
    </button>
  );
}
