import {
	authenticatedBackendFetch,
	forwardBackendResponse,
} from "@/lib/server/backend";
import type { NextRequest } from "next/server";

export async function POST(req: NextRequest) {
	let body: unknown;
	try {
		body = await req.json();
	} catch {
		return new Response("Invalid JSON", { status: 400 });
	}

	const upstream = await authenticatedBackendFetch("/v1/chat/stream", {
		method: "POST",
		headers: { "Content-Type": "application/json" },
		body: JSON.stringify(body),
		signal: req.signal,
	});

	return forwardBackendResponse(upstream, { stream: upstream.ok });
}
