import { createServerSupabaseClient } from "../supabase/server";

const DEVELOPMENT_BACKEND_URL = "http://localhost:8000";

export function getBackendUrl(path: string, query?: URLSearchParams): string {
	const configured = process.env.BACKEND_URL;
	if (!configured && process.env.NODE_ENV === "production") {
		throw new Error("BACKEND_URL is required in production");
	}

	const base = new URL(configured || DEVELOPMENT_BACKEND_URL);
	if (base.protocol !== "http:" && base.protocol !== "https:") {
		throw new Error("BACKEND_URL must use HTTP or HTTPS");
	}

	base.pathname = `${base.pathname.replace(/\/$/, "")}/${path.replace(/^\//, "")}`;
	base.search = query?.toString() ?? "";
	base.hash = "";
	return base.toString();
}

function jsonError(detail: string, status: number) {
	return new Response(JSON.stringify({ detail }), {
		status,
		headers: { "Content-Type": "application/json" },
	});
}

export async function authenticatedBackendFetch(
	path: string,
	init: RequestInit & { duplex?: "half"; query?: URLSearchParams } = {},
): Promise<Response> {
	const supabase = await createServerSupabaseClient();
	const {
		data: { user },
		error: userError,
	} = await supabase.auth.getUser();

	if (userError || !user) {
		return jsonError("Unauthorized", 401);
	}

	const {
		data: { session },
	} = await supabase.auth.getSession();
	if (!session?.access_token) {
		return jsonError("Unauthorized", 401);
	}

	const { query, ...requestInit } = init;
	const headers = new Headers(requestInit.headers);
	headers.set("Authorization", `Bearer ${session.access_token}`);

	try {
		return await fetch(getBackendUrl(path, query), {
			...requestInit,
			headers,
			cache: "no-store",
		});
	} catch (error) {
		console.error("Backend request failed", error);
		return jsonError("Backend service unavailable", 502);
	}
}

export function forwardBackendResponse(
	upstream: Response,
	options: { stream?: boolean } = {},
): Response {
	const headers = new Headers();
	const contentType = upstream.headers.get("Content-Type");
	if (contentType) headers.set("Content-Type", contentType);

	if (options.stream) {
		headers.set("Content-Type", "text/event-stream");
		headers.set("Cache-Control", "no-cache, no-transform");
		headers.set("X-Accel-Buffering", "no");
	}

	return new Response(upstream.body, {
		status: upstream.status,
		statusText: upstream.statusText,
		headers,
	});
}
