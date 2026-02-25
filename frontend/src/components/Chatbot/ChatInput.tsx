/**
 * ChatInput component - User input with send button.
 * Implements FRD 14 (Chatbot) Section 10 - Chat Input Component.
 */

import { useState, useRef, useCallback, useEffect } from "react";
import { Send, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

interface ChatInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
  placeholder?: string;
}

export function ChatInput({
  onSend,
  disabled = false,
  placeholder = "Ask about the report…",
}: ChatInputProps) {
  const [value, setValue] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = "auto";
      textarea.style.height = `${Math.min(textarea.scrollHeight, 150)}px`;
    }
  }, [value]);

  const handleSubmit = useCallback(() => {
    const trimmed = value.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setValue("");
  }, [value, disabled, onSend]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        handleSubmit();
      }
    },
    [handleSubmit]
  );

  const canSend = value.trim().length > 0 && !disabled;

  return (
    <div className="flex items-end gap-2 p-4 border-t border-slate-100 bg-[#fff6e9]">
      <textarea
        ref={textareaRef}
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        disabled={disabled}
        rows={1}
        className={cn(
          "flex-1 resize-none rounded-xl px-3.5 py-2.5",
          "border border-slate-200 bg-[#f5ecdb]",
          "text-slate-900 text-sm leading-relaxed",
          "placeholder:text-[#8b7355]",
          "focus:outline-none focus:ring-2 focus:ring-slate-200 focus:border-slate-300 focus:bg-[#fff6e9]",
          "disabled:opacity-50 disabled:cursor-not-allowed",
          "max-h-36 overflow-y-auto transition-all"
        )}
      />
      <button
        onClick={handleSubmit}
        disabled={!canSend}
        className={cn(
          "shrink-0 w-9 h-9 rounded-full flex items-center justify-center transition-all duration-200",
          canSend
            ? "bg-slate-900 text-white hover:bg-slate-700 cursor-pointer"
            : "bg-[#eddfc8] text-slate-300 cursor-not-allowed"
        )}
        aria-label="Send message"
      >
        {disabled ? (
          <Loader2 className="w-4 h-4 animate-spin" />
        ) : (
          <Send className="w-4 h-4" />
        )}
      </button>
    </div>
  );
}
