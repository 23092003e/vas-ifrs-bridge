import { afterEach, describe, expect, it, vi } from "vitest";

const auth = vi.hoisted(() => ({
	getUser: vi.fn(),
	getSession: vi.fn(),
}));

vi.mock("../supabase/server", () => ({
	createServerSupabaseClient: () => ({ auth }),
}));

import {
	authenticatedBackendFetch,
	forwardBackendResponse,
	getBackendUrl,
} from "./backend";

describe("getBackendUrl", () => {
	afterEach(() => {
		vi.unstubAllEnvs();
	});

	it("joins the configured backend base and route", () => {
		vi.stubEnv("BACKEND_URL", "https://api.example/base/");
		expect(getBackendUrl("/v1/documents/")).toBe(
			"https://api.example/base/v1/documents/",
		);
	});

	it("rejects non-http backend URLs", () => {
		vi.stubEnv("BACKEND_URL", "file:///tmp/backend");
		expect(() => getBackendUrl("/v1/chat/stream")).toThrow(
			"must use HTTP or HTTPS",
		);
	});
});

describe("forwardBackendResponse", () => {
	it("preserves status and JSON content type", async () => {
		const upstream = new Response(JSON.stringify({ detail: "Not found" }), {
			status: 404,
			headers: { "Content-Type": "application/json" },
		});

		const response = forwardBackendResponse(upstream);
		expect(response.status).toBe(404);
		expect(response.headers.get("Content-Type")).toBe("application/json");
		expect(await response.json()).toEqual({ detail: "Not found" });
	});

	it("sets anti-buffering headers only for a successful stream", () => {
		const response = forwardBackendResponse(new Response("data: ok\n\n"), {
			stream: true,
		});

		expect(response.headers.get("Content-Type")).toBe("text/event-stream");
		expect(response.headers.get("Cache-Control")).toContain("no-transform");
		expect(response.headers.get("X-Accel-Buffering")).toBe("no");
	});
});

describe("authenticatedBackendFetch", () => {
	afterEach(() => {
		vi.restoreAllMocks();
		vi.unstubAllGlobals();
		auth.getUser.mockReset();
		auth.getSession.mockReset();
	});

	it("rejects an unverified session before calling the backend", async () => {
		auth.getUser.mockResolvedValue({
			data: { user: null },
			error: new Error("invalid token"),
		});
		const fetchMock = vi.fn();
		vi.stubGlobal("fetch", fetchMock);

		const response = await authenticatedBackendFetch("/v1/documents/");

		expect(response.status).toBe(401);
		expect(fetchMock).not.toHaveBeenCalled();
	});

	it("forwards only the verified access token", async () => {
		auth.getUser.mockResolvedValue({ data: { user: { id: "user-1" } } });
		auth.getSession.mockResolvedValue({
			data: { session: { access_token: "verified-token" } },
		});
		const fetchMock = vi.fn().mockResolvedValue(new Response("ok"));
		vi.stubGlobal("fetch", fetchMock);

		await authenticatedBackendFetch("/v1/documents/");

		const [, init] = fetchMock.mock.calls[0] as [string, RequestInit];
		const headers = new Headers(init.headers);
		expect(headers.get("Authorization")).toBe("Bearer verified-token");
		expect(headers.has("X-Tenant-Id")).toBe(false);
	});

	it("maps network failures to a safe 502 response", async () => {
		auth.getUser.mockResolvedValue({ data: { user: { id: "user-1" } } });
		auth.getSession.mockResolvedValue({
			data: { session: { access_token: "verified-token" } },
		});
		vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("offline")));
		vi.spyOn(console, "error").mockImplementation(() => undefined);

		const response = await authenticatedBackendFetch("/v1/documents/");

		expect(response.status).toBe(502);
		expect(await response.json()).toEqual({
			detail: "Backend service unavailable",
		});
	});
});
