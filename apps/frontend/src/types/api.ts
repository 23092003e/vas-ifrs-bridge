export interface ChatRequest {
	conversation_id?: string;
	content: string;
	lang: "vi" | "en" | "auto";
	scope: "shared" | "tenant" | "both";
	reasoning?: "fast" | "balanced" | "deep";
	intent_hint?: "qa" | "compare" | "mapping" | "report" | "adjustment";
}

export type SSEEvent =
	| { type: "intent"; intent: string; model: string }
	| { type: "token"; delta: string }
	| {
			type: "citation";
			key: string;
			doc_id: string;
			chunk_id: string;
			snippet: string;
			standard_code: string | null;
	  }
	| { type: "final"; content: string; conversation_id?: string }
	| { type: "error"; message: string };

export interface Citation {
	key: string;
	doc_id: string;
	chunk_id: string;
	snippet: string;
	standard_code: string | null;
}

export interface Message {
	id: string;
	role: "user" | "assistant";
	content: string;
	citations: Citation[];
	loading?: boolean;
}
