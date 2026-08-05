import { describe, expect, it } from "vitest";

import {
	MAX_DOCUMENT_SIZE_BYTES,
	parseDocumentsResponse,
	validateDocumentFile,
} from "./validation";

describe("validateDocumentFile", () => {
	it("accepts formats supported by the backend", () => {
		expect(validateDocumentFile({ name: "policy.MD", size: 100 })).toBeNull();
	});

	it("rejects HTML and oversized files", () => {
		expect(validateDocumentFile({ name: "page.html", size: 100 })).toContain(
			"không được hỗ trợ",
		);
		expect(
			validateDocumentFile({
				name: "large.pdf",
				size: MAX_DOCUMENT_SIZE_BYTES + 1,
			}),
		).toContain("25 MB");
	});
});

describe("parseDocumentsResponse", () => {
	it("accepts the backend document contract", () => {
		expect(
			parseDocumentsResponse({
				documents: [
					{
						id: "d1",
						filename: "ifrs.pdf",
						size_bytes: 10,
						status: "ready",
						chunk_count: 2,
						created_at: "2026-08-05T00:00:00Z",
					},
				],
			}),
		).toHaveLength(1);
	});

	it("rejects malformed responses", () => {
		expect(() => parseDocumentsResponse({ documents: [{}] })).toThrow(
			"Invalid documents response",
		);
	});
});
