import { createServerSupabaseClient } from "@/lib/supabase/server";
import type { NextRequest } from "next/server";

const BACKEND = process.env.BACKEND_URL ?? "http://localhost:8000";

export async function POST(req: NextRequest) {
	let body: unknown;
	try {
		body = await req.json();
	} catch {
		return new Response("Invalid JSON", { status: 400 });
	}

	const supabase = createServerSupabaseClient();
	const {
		data: { session },
	} = await supabase.auth.getSession();
	if (!session) {
		return new Response("Unauthorized", { status: 401 });
	}

	const headers: Record<string, string> = {
		"Content-Type": "application/json",
		Authorization: `Bearer ${session.access_token}`,
	};

	const tenantId = session.user.user_metadata?.tenant_id;
	if (tenantId) {
		headers["X-Tenant-Id"] = tenantId;
	}

	const upstream = await fetch(`${BACKEND}/v1/chat/stream`, {
		method: "POST",
		headers,
		body: JSON.stringify(body),
	});

	if (!upstream.ok || !upstream.body) {
		const text = await upstream.text().catch(() => `HTTP ${upstream.status}`);
		return new Response(text, { status: upstream.status });
	}

	return new Response(upstream.body, {
		status: 200,
		headers: {
			"Content-Type": "text/event-stream",
			"Cache-Control": "no-cache",
			"X-Accel-Buffering": "no",
		},
	});
}
