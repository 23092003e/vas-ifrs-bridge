import { describe, expect, it } from "vitest";

import {
	applyStreamEvent,
	consumeSseBuffer,
	parseConversationMessages,
} from "./events";

describe("consumeSseBuffer", () => {
	it("keeps a partial event for the next network chunk", () => {
		const first = consumeSseBuffer('data: {"type":"token","del');
		expect(first.events).toEqual([]);

		const second = consumeSseBuffer(`${first.rest}ta":"xin"}\n\n`);
		expect(second.events).toEqual([{ type: "token", delta: "xin" }]);
		expect(second.rest).toBe("");
	});

	it("flushes a valid final event without a trailing newline", () => {
		const result = consumeSseBuffer(
			'data: {"type":"final","content":"done","conversation_id":"c-1"}',
			true,
		);
		expect(result.events).toEqual([
			{ type: "final", content: "done", conversation_id: "c-1" },
		]);
	});

	it("ignores malformed and unknown events", () => {
		const result = consumeSseBuffer(
			'data: nope\ndata: {"type":"unknown"}\ndata: {"type":"token"}\n',
		);
		expect(result.events).toEqual([]);
	});
});

describe("parseConversationMessages", () => {
	it("validates and normalizes conversation history", () => {
		expect(
			parseConversationMessages({
				messages: [
					{
						id: "m-1",
						role: "assistant",
						content: "answer",
						citations: [
							{
								key: "c1",
								doc_id: "d1",
								chunk_id: "ch1",
								snippet: "text",
								standard_code: null,
							},
						],
					},
				],
			}),
		).toHaveLength(1);
	});

	it("rejects an invalid response contract", () => {
		expect(() => parseConversationMessages({ messages: [{}] })).toThrow(
			"Invalid conversation message",
		);
	});
});

describe("applyStreamEvent", () => {
	const message = {
		id: "m-1",
		role: "assistant" as const,
		content: "partial",
		citations: [],
		loading: true,
	};

	it("preserves streamed content when the final event content is empty", () => {
		expect(
			applyStreamEvent(message, { type: "final", content: "" }).content,
		).toBe("partial");
	});

	it("deduplicates repeated citations", () => {
		const citation = {
			type: "citation" as const,
			key: "c1",
			doc_id: "d1",
			chunk_id: "ch1",
			snippet: "text",
			standard_code: null,
		};
		const once = applyStreamEvent(message, citation);
		const twice = applyStreamEvent(once, citation);
		expect(twice.citations).toHaveLength(1);
	});
});
