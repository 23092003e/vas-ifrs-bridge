import { describe, expect, it } from "vitest";

import { getSafeRedirectPath } from "./redirect";

describe("getSafeRedirectPath", () => {
	it.each([null, "", "https://evil.example", "//evil.example/path"])(
		"falls back for unsafe target %s",
		(value) => {
			expect(getSafeRedirectPath(value)).toBe("/chat");
		},
	);

	it("preserves a local path and query string", () => {
		expect(getSafeRedirectPath("/documents?status=pending#latest")).toBe(
			"/documents?status=pending#latest",
		);
	});
});
