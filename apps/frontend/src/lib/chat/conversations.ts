export interface ConversationItem {
	id: string;
	title: string;
	updated_at: string;
}

export interface GroupedConversations {
	group: string;
	items: ConversationItem[];
}

function isConversation(value: unknown): value is ConversationItem {
	if (typeof value !== "object" || value === null) return false;
	const item = value as Record<string, unknown>;
	return (
		typeof item.id === "string" &&
		typeof item.title === "string" &&
		typeof item.updated_at === "string" &&
		Number.isFinite(Date.parse(item.updated_at))
	);
}

export function parseConversationsResponse(value: unknown): ConversationItem[] {
	if (typeof value !== "object" || value === null) {
		throw new Error("Invalid conversations response");
	}
	const conversations = (value as Record<string, unknown>).conversations;
	if (!Array.isArray(conversations) || !conversations.every(isConversation)) {
		throw new Error("Invalid conversations response");
	}
	return conversations;
}

export function groupConversations(
	conversations: ConversationItem[],
	now = new Date(),
): GroupedConversations[] {
	const buckets = {
		today: [] as ConversationItem[],
		yesterday: [] as ConversationItem[],
		thisWeek: [] as ConversationItem[],
		older: [] as ConversationItem[],
	};
	const startOfToday = new Date(
		now.getFullYear(),
		now.getMonth(),
		now.getDate(),
	).getTime();
	const startOfYesterday = startOfToday - 24 * 60 * 60 * 1000;
	const startOfThisWeek = startOfToday - 7 * 24 * 60 * 60 * 1000;

	for (const item of conversations) {
		const time = Date.parse(item.updated_at);
		if (time >= startOfToday) buckets.today.push(item);
		else if (time >= startOfYesterday) buckets.yesterday.push(item);
		else if (time >= startOfThisWeek) buckets.thisWeek.push(item);
		else buckets.older.push(item);
	}

	return [
		{ group: "Hôm nay", items: buckets.today },
		{ group: "Hôm qua", items: buckets.yesterday },
		{ group: "Tuần này", items: buckets.thisWeek },
		{ group: "Cũ hơn", items: buckets.older },
	].filter((group) => group.items.length > 0);
}
