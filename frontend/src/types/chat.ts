/**
 * Chat types for the contextual chatbot.
 * Implements FRD 14 (Chatbot).
 */

/**
 * Types of sources that can be cited in chat responses.
 */
export type CitationSourceType =
  | "claim"
  | "finding"
  | "ifrs_paragraph"
  | "verdict"
  | "gap"
  | "report"
  | "sasb";

/**
 * Navigation targets for citation clicks in the UI.
 */
export type CitationNavigationTarget =
  | "pdf_viewer"
  | "finding_panel"
  | "ifrs_viewer"
  | "source_of_truth"
  | "disclosure_gaps";

/**
 * A citation linking to a source entity.
 */
export interface Citation {
  citation_number: number;
  source_type: CitationSourceType;
  source_id: string;
  navigation_target: CitationNavigationTarget;
  display_text: string;
}

/**
 * A single chat message with metadata and citations.
 */
export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations: Citation[];
  timestamp: string;
}

/**
 * Response containing full conversation history for a report.
 */
export interface ConversationHistoryResponse {
  conversation_id: string;
  report_id: string;
  messages: ChatMessage[];
}

/**
 * SSE event types for chat streaming.
 */
export type ChatStreamEventType =
  | "chat_token"
  | "chat_citations"
  | "chat_done"
  | "chat_error";

/**
 * Token event data from SSE stream.
 */
export interface ChatTokenEventData {
  token: string;
}

/**
 * Citations event data from SSE stream.
 */
export interface ChatCitationsEventData {
  citations: Citation[];
}

/**
 * Done event data from SSE stream.
 */
export interface ChatDoneEventData {
  message_id: string;
  full_content: string;
}

/**
 * Error event data from SSE stream.
 */
export interface ChatErrorEventData {
  error: string;
}

/**
 * Chat state for the useChat hook.
 */
export interface ChatState {
  messages: ChatMessage[];
  isStreaming: boolean;
  currentResponse: string;
  error: string | null;
  conversationId: string | null;
}
