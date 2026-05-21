export interface Tenant {
	id: string;
	name: string;
	plan: string;
}
export interface Message {
	id: string;
	role: "user" | "assistant";
	content: string;
	citations?: Citation[];
}
export interface Citation {
	key: string;
	doc_id: string;
	snippet: string;
	standard_code?: string;
}
