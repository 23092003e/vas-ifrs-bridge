export const MAX_DOCUMENT_SIZE_BYTES = 25 * 1024 * 1024;

const ALLOWED_EXTENSIONS = new Set([
	"pdf",
	"docx",
	"xlsx",
	"xls",
	"txt",
	"md",
	"csv",
]);

export interface DocumentItem {
	id: string;
	filename: string;
	size_bytes: number;
	status: string;
	chunk_count: number;
	created_at: string;
}

function isDocumentItem(value: unknown): value is DocumentItem {
	if (typeof value !== "object" || value === null) return false;
	const item = value as Record<string, unknown>;
	return (
		typeof item.id === "string" &&
		typeof item.filename === "string" &&
		typeof item.size_bytes === "number" &&
		typeof item.status === "string" &&
		typeof item.chunk_count === "number" &&
		typeof item.created_at === "string"
	);
}

export function parseDocumentsResponse(value: unknown): DocumentItem[] {
	if (typeof value !== "object" || value === null) {
		throw new Error("Invalid documents response");
	}
	const documents = (value as Record<string, unknown>).documents;
	if (!Array.isArray(documents) || !documents.every(isDocumentItem)) {
		throw new Error("Invalid documents response");
	}
	return documents;
}

export function validateDocumentFile(file: Pick<File, "name" | "size">) {
	const extension = file.name.split(".").pop()?.toLowerCase() ?? "";
	if (!ALLOWED_EXTENSIONS.has(extension)) {
		return "Định dạng tài liệu không được hỗ trợ.";
	}
	if (file.size > MAX_DOCUMENT_SIZE_BYTES) {
		return "Tài liệu vượt quá giới hạn 25 MB.";
	}
	return null;
}
