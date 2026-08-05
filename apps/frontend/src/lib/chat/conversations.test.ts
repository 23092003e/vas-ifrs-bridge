import { describe, expect, it } from "vitest";

import {
	groupConversations,
	parseConversationsResponse,
} from "./conversations";

describe("parseConversationsResponse", () => {
	it("accepts the backend conversation contract", () => {
		expect(
			parseConversationsResponse({
				conversations: [
					{ id: "c1", title: "IFRS 15", updated_at: "2026-08-05T02:00:00Z" },
				],
			}),
		).toHaveLength(1);
	});

	it("rejects invalid dates", () => {
		expect(() =>
			parseConversationsResponse({
				conversations: [{ id: "c1", title: "Bad", updated_at: "never" }],
			}),
		).toThrow("Invalid conversations response");
	});
});

describe("groupConversations", () => {
	it("groups conversations against a deterministic local day", () => {
		const groups = groupConversations(
			[
				{
					id: "today",
					title: "Today",
					updated_at: "2026-08-05T08:00:00+07:00",
				},
				{ id: "old", title: "Old", updated_at: "2026-07-01T08:00:00+07:00" },
			],
			new Date("2026-08-05T12:00:00+07:00"),
		);
		expect(groups.map((group) => group.group)).toEqual(["Hôm nay", "Cũ hơn"]);
	});
});
