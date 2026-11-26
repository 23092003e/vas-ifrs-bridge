"use client";

import {
	applyStreamEvent,
	parseConversationMessages,
	readChatStream,
} from "@/lib/chat/events";
import type { Message, SSEEvent } from "@/types/api";
import { useParams, useRouter } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";

let messageIdCounter = 0;
function nextId() {
	return String(++messageIdCounter);
}

function errorMessage(error: unknown): string {
	return error instanceof Error ? error.message : String(error);
}

async function responseError(response: Response): Promise<string> {
	try {
		const payload: unknown = await response.json();
		if (
			typeof payload === "object" &&
			payload !== null &&
			"detail" in payload &&
			typeof payload.detail === "string"
		) {
			return payload.detail;
		}
	} catch {
		// Fall through to the HTTP status.
	}
	return `HTTP ${response.status}`;
}

interface SendOptions {
	lang?: "vi" | "en" | "auto";
	scope?: "shared" | "tenant" | "both";
	reasoning?: "fast" | "balanced" | "deep";
}

export function useChat() {
	const params = useParams();
	const router = useRouter();
	const conversationId = params?.conversationId as string | undefined;

	const [messages, setMessages] = useState<Message[]>([]);
	const [loading, setLoading] = useState(false);
	const abortRef = useRef<AbortController | null>(null);

	useEffect(() => {
		if (!conversationId) {
			setMessages([]);
			setLoading(false);
			return;
		}

		const controller = new AbortController();
		setLoading(true);

		async function loadConversation() {
			try {
				const response = await fetch(
					`/api/chat/conversations/${encodeURIComponent(conversationId ?? "")}`,
					{ signal: controller.signal },
				);
				if (!response.ok) throw new Error(await responseError(response));
				setMessages(parseConversationMessages(await response.json()));
			} catch (error) {
				if (controller.signal.aborted) return;
				console.error("Error loading chat history", error);
				setMessages([
					{
						id: "error",
						role: "assistant",
						content: `Lỗi: ${errorMessage(error)}`,
						citations: [],
					},
				]);
			} finally {
				if (!controller.signal.aborted) setLoading(false);
			}
		}

		void loadConversation();
		return () => controller.abort();
	}, [conversationId]);

	useEffect(() => () => abortRef.current?.abort(), [conversationId]);

	const sendMessage = useCallback(
		async (content: string, opts: SendOptions = {}) => {
			abortRef.current?.abort();
			const controller = new AbortController();
			abortRef.current = controller;

			const userMessage: Message = {
				id: nextId(),
				role: "user",
				content,
				citations: [],
			};
			const assistantId = nextId();
			const assistantMessage: Message = {
				id: assistantId,
				role: "assistant",
				content: "",
				citations: [],
				loading: true,
			};

			setMessages((previous) => [...previous, userMessage, assistantMessage]);
			setLoading(true);

			const handleEvent = (event: SSEEvent) => {
				if (controller.signal.aborted) return;
				setMessages((previous) =>
					previous.map((message) =>
						message.id === assistantId
							? applyStreamEvent(message, event)
							: message,
					),
				);
				if (
					event.type === "final" &&
					!conversationId &&
					event.conversation_id
				) {
					router.push(`/chat/${encodeURIComponent(event.conversation_id)}`);
				}
			};

			try {
				const response = await fetch("/api/chat/stream", {
					method: "POST",
					headers: {
						Accept: "text/event-stream",
						"Content-Type": "application/json",
					},
					body: JSON.stringify({
						conversation_id: conversationId,
						content,
						lang: opts.lang ?? "auto",
						scope: opts.scope ?? "both",
						reasoning: opts.reasoning,
					}),
					signal: controller.signal,
				});

				if (!response.ok || !response.body) {
					throw new Error(await responseError(response));
				}

				await readChatStream(response.body, handleEvent);
			} catch (error) {
				if (controller.signal.aborted) return;
				setMessages((previous) =>
					previous.map((message) =>
						message.id === assistantId
							? {
									...message,
									content: `Lỗi: ${errorMessage(error)}`,
									citations: [],
									loading: false,
								}
							: message,
					),
				);
			} finally {
				setMessages((previous) =>
					previous.map((message) =>
						message.id === assistantId && message.loading
							? { ...message, loading: false }
							: message,
					),
				);
				if (abortRef.current === controller) {
					abortRef.current = null;
					setLoading(false);
				}
			}
		},
		[conversationId, router],
	);

	const clearMessages = useCallback(() => {
		abortRef.current?.abort();
		abortRef.current = null;
		setMessages([]);
		setLoading(false);
		router.push("/chat");
	}, [router]);

	const abort = useCallback(() => {
		abortRef.current?.abort();
		abortRef.current = null;
		setLoading(false);
		setMessages((previous) =>
			previous.map((message) =>
				message.loading
					? {
							...message,
							content: "Đã dừng phản hồi.",
							citations: [],
							loading: false,
						}
					: message,
			),
		);
	}, []);

	return { messages, loading, sendMessage, clearMessages, abort };
}
