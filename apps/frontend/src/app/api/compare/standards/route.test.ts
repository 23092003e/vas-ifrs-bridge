import { afterEach, describe, expect, it, vi } from "vitest";

const backend = vi.hoisted(() => ({
	authenticatedBackendFetch: vi.fn(),
}));

vi.mock("@/lib/server/backend", () => ({
	authenticatedBackendFetch: backend.authenticatedBackendFetch,
}));

import { GET } from "./route";

describe("GET /api/compare/standards", () => {
	afterEach(() => {
		vi.restoreAllMocks();
		backend.authenticatedBackendFetch.mockReset();
	});

	it("returns upstream standards data when backend responds ok", async () => {
		const mockData = {
			vas_standards: [
				{ code: "VAS-14", name: "Doanh thu", category: "Income" },
			],
			ifrs_standards: [
				{ code: "IFRS-15", name: "Revenue", category: "Income" },
			],
			relations: [],
			topics: [],
		};

		backend.authenticatedBackendFetch.mockResolvedValue(
			new Response(JSON.stringify(mockData), {
				status: 200,
				headers: { "Content-Type": "application/json" },
			}),
		);

		const response = await GET();
		expect(response.status).toBe(200);
		const data = await response.json();
		expect(data.vas_standards).toHaveLength(1);
		expect(data.vas_standards[0].code).toBe("VAS-14");
		expect(data.ifrs_standards[0].code).toBe("IFRS-15");
	});

	it("returns fallback catalog when backend returns non-ok", async () => {
		backend.authenticatedBackendFetch.mockResolvedValue(
			new Response("Service unavailable", { status: 503 }),
		);

		const response = await GET();
		expect(response.status).toBe(200);
		const data = await response.json();
		expect(data.vas_standards.length).toBeGreaterThan(10);
		expect(data.ifrs_standards.length).toBeGreaterThan(10);
		expect(data.relations.length).toBeGreaterThan(0);
		expect(data.topics.length).toBeGreaterThan(0);
	});

	it("returns fallback catalog when backend fetch throws network error", async () => {
		backend.authenticatedBackendFetch.mockRejectedValue(
			new Error("Connection refused"),
		);

		const response = await GET();
		expect(response.status).toBe(200);
		const data = await response.json();
		expect(
			data.vas_standards.some((v: { code: string }) => v.code === "VAS-06"),
		).toBe(true);
		expect(
			data.ifrs_standards.some((i: { code: string }) => i.code === "IFRS-16"),
		).toBe(true);
	});
});
