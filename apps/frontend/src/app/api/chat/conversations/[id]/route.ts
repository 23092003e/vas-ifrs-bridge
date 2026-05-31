import { createServerSupabaseClient } from "@/lib/supabase/server";
import { type NextRequest, NextResponse } from "next/server";

const BACKEND = process.env.BACKEND_URL ?? "http://localhost:8000";

export async function GET(
	_req: NextRequest,
	{ params }: { params: { id: string } },
) {
	const supabase = createServerSupabaseClient();
	const {
		data: { session },
	} = await supabase.auth.getSession();
	if (!session) {
		return NextResponse.json({ detail: "Unauthorized" }, { status: 401 });
	}

	const headers: Record<string, string> = {
		Authorization: `Bearer ${session.access_token}`,
	};
	const tenantId = session.user.user_metadata?.tenant_id;
	if (tenantId) {
		headers["X-Tenant-Id"] = tenantId;
	}

	const res = await fetch(`${BACKEND}/v1/chat/conversations/${params.id}`, {
		headers,
	});

	if (!res.ok) {
		return NextResponse.json(
			{ detail: "Conversation not found" },
			{ status: res.status },
		);
	}

	const data = await res.json();
	return NextResponse.json(data);
}

export async function DELETE(
	_req: NextRequest,
	{ params }: { params: { id: string } },
) {
	const supabase = createServerSupabaseClient();
	const {
		data: { session },
	} = await supabase.auth.getSession();
	if (!session) {
		return NextResponse.json({ detail: "Unauthorized" }, { status: 401 });
	}

	const headers: Record<string, string> = {
		Authorization: `Bearer ${session.access_token}`,
	};
	const tenantId = session.user.user_metadata?.tenant_id;
	if (tenantId) {
		headers["X-Tenant-Id"] = tenantId;
	}

	const res = await fetch(`${BACKEND}/v1/chat/conversations/${params.id}`, {
		method: "DELETE",
		headers,
	});

	if (!res.ok) {
		return NextResponse.json(
			{ detail: "Failed to delete conversation" },
			{ status: res.status },
		);
	}

	const data = await res.json();
	return NextResponse.json(data);
}
