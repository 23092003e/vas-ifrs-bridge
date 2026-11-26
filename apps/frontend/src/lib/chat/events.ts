import type { Citation, Message, SSEEvent } from "@/types/api";

function isRecord(value: unknown): value is Record<string, unknown> {
	return typeof value === "object" && value !== null;
}

function parseEvent(value: unknown): SSEEvent | null {
	if (!isRecord(value) || typeof value.type !== "string") return null;

	switch (value.type) {
		case "intent":
			return typeof value.intent === "string" && typeof value.model === "string"
				? { type: "intent", intent: value.intent, model: value.model }
				: null;
		case "token":
			return typeof value.delta === "string"
				? { type: "token", delta: value.delta }
				: null;
		case "citation":
			return typeof value.key === "string" &&
				typeof value.doc_id === "string" &&
				typeof value.chunk_id === "string" &&
				typeof value.snippet === "string" &&
				(typeof value.standard_code === "string" ||
					value.standard_code === null)
				? {
						type: "citation",
						key: value.key,
						doc_id: value.doc_id,
						chunk_id: value.chunk_id,
						snippet: value.snippet,
						standard_code: value.standard_code,
					}
				: null;
		case "final":
			return typeof value.content === "string" &&
				(value.conversation_id === undefined ||
					typeof value.conversation_id === "string")
				? {
						type: "final",
						content: value.content,
						conversation_id: value.conversation_id,
					}
				: null;
		case "error":
			return typeof value.message === "string"
				? { type: "error", message: value.message }
				: null;
		default:
			return null;
	}
}

export function consumeSseBuffer(
	buffer: string,
	flush = false,
): { events: SSEEvent[]; rest: string } {
	const lines = buffer.split("\n");
	const rest = flush ? "" : (lines.pop() ?? "");
	const events: SSEEvent[] = [];

	for (const rawLine of lines) {
		const line = rawLine.endsWith("\r") ? rawLine.slice(0, -1) : rawLine;
		if (!line.startsWith("data:")) continue;
		const payload = line.slice(5).trim();
		if (!payload) continue;
		try {
			const event = parseEvent(JSON.parse(payload));
			if (event) events.push(event);
		} catch {
			// Ignore malformed events while keeping the stream alive.
		}
	}

	return { events, rest };
}

export async function readChatStream(
	body: ReadableStream<Uint8Array>,
	onEvent: (event: SSEEvent) => void,
): Promise<void> {
	const reader = body.getReader();
	const decoder = new TextDecoder();
	let buffer = "";
	try {
		while (true) {
			const { value, done } = await reader.read();
			buffer += decoder.decode(value, { stream: !done });
			const { events, rest } = consumeSseBuffer(buffer, done);
			buffer = rest;
			for (const event of events) {
				if (event.type === "error") throw new Error(event.message);
				onEvent(event);
				if (event.type === "final") return;
			}
			if (done)
				throw new Error("Luồng phản hồi chưa hoàn tất. Vui lòng thử lại.");
		}
	} finally {
		void reader.cancel().catch(() => {});
		reader.releaseLock();
	}
}

function parseCitation(value: unknown): Citation | null {
	const parsed = parseEvent(
		isRecord(value) ? { ...value, type: "citation" } : value,
	);
	return parsed?.type === "citation"
		? {
				key: parsed.key,
				doc_id: parsed.doc_id,
				chunk_id: parsed.chunk_id,
				snippet: parsed.snippet,
				standard_code: parsed.standard_code,
			}
		: null;
}

export function parseConversationMessages(value: unknown): Message[] {
	if (!isRecord(value) || !Array.isArray(value.messages)) {
		throw new Error("Invalid conversation response");
	}

	return value.messages.map((item) => {
		if (
			!isRecord(item) ||
			typeof item.id !== "string" ||
			(item.role !== "user" && item.role !== "assistant") ||
			typeof item.content !== "string"
		) {
			throw new Error("Invalid conversation message");
		}

		const citations = Array.isArray(item.citations)
			? item.citations
					.map(parseCitation)
					.filter((citation): citation is Citation => citation !== null)
			: [];
		return {
			id: item.id,
			role: item.role,
			content: item.content,
			citations,
		};
	});
}

export function applyStreamEvent(message: Message, event: SSEEvent): Message {
	if (event.type === "token") {
		return { ...message, content: message.content + event.delta };
	}
	if (event.type === "citation") {
		const duplicate = message.citations.some(
			(citation) =>
				citation.key === event.key && citation.chunk_id === event.chunk_id,
		);
		if (duplicate) return message;
		return {
			...message,
			citations: [
				...message.citations,
				{
					key: event.key,
					doc_id: event.doc_id,
					chunk_id: event.chunk_id,
					snippet: event.snippet,
					standard_code: event.standard_code,
				},
			],
		};
	}
	if (event.type === "final") {
		return {
			...message,
			content: event.content,
			loading: false,
		};
	}
	if (event.type === "error") {
		return { ...message, content: `Error: ${event.message}`, loading: false };
	}
	return message;
}
