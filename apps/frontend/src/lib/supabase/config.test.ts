import { afterEach, describe, expect, it, vi } from "vitest";

import { getSupabaseConfig } from "./config";

describe("getSupabaseConfig", () => {
	afterEach(() => {
		vi.unstubAllEnvs();
	});

	it("returns configured public credentials", () => {
		vi.stubEnv("NEXT_PUBLIC_SUPABASE_URL", "https://example.supabase.co");
		vi.stubEnv("NEXT_PUBLIC_SUPABASE_ANON_KEY", "anon-key");

		expect(getSupabaseConfig()).toEqual({
			url: "https://example.supabase.co",
			anonKey: "anon-key",
		});
	});

	it("fails clearly when configuration is incomplete", () => {
		vi.stubEnv("NEXT_PUBLIC_SUPABASE_URL", "");
		vi.stubEnv("NEXT_PUBLIC_SUPABASE_ANON_KEY", "");

		expect(() => getSupabaseConfig()).toThrow("Missing NEXT_PUBLIC_SUPABASE");
	});
});
