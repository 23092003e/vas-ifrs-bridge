import {
	authenticatedBackendFetch,
	forwardBackendResponse,
} from "@/lib/server/backend";
import type { NextRequest } from "next/server";

export async function GET() {
	const upstream = await authenticatedBackendFetch("/v1/documents/");
	return forwardBackendResponse(upstream);
}

export async function POST(req: NextRequest) {
	try {
		const formData = await req.formData();
		const upstream = await authenticatedBackendFetch("/v1/documents/upload", {
			method: "POST",
			body: formData,
		});
		return forwardBackendResponse(upstream);
	} catch {
		return new Response(JSON.stringify({ detail: "Invalid multipart form" }), {
			status: 400,
			headers: { "Content-Type": "application/json" },
		});
	}
}
