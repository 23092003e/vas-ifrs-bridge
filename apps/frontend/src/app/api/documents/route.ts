import { createServerSupabaseClient } from "@/lib/supabase/server";
import { type NextRequest, NextResponse } from "next/server";

const BACKEND = process.env.BACKEND_URL ?? "http://localhost:8000";

export async function GET(_req: NextRequest) {
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

	const res = await fetch(`${BACKEND}/v1/documents/`, {
		headers,
	});

	if (!res.ok) {
		return NextResponse.json(
			{ detail: "Failed to fetch documents" },
			{ status: res.status },
		);
	}

	const data = await res.json();
	return NextResponse.json(data);
}

export async function POST(req: NextRequest) {
	const supabase = createServerSupabaseClient();
	const {
		data: { session },
	} = await supabase.auth.getSession();
	if (!session) {
		return NextResponse.json({ detail: "Unauthorized" }, { status: 401 });
	}

	try {
		const formData = await req.formData();
		const headers: Record<string, string> = {
			Authorization: `Bearer ${session.access_token}`,
		};
		const tenantId = session.user.user_metadata?.tenant_id;
		if (tenantId) {
			headers["X-Tenant-Id"] = tenantId;
		}

		const res = await fetch(`${BACKEND}/v1/documents/upload`, {
			method: "POST",
			headers,
			body: formData,
		});

		if (!res.ok) {
			const text = await res.text();
			return NextResponse.json(
				{ detail: text || "Failed to upload document" },
				{ status: res.status },
			);
		}

		const data = await res.json();
		return NextResponse.json(data);
	} catch (exc: any) {
		return NextResponse.json(
			{ detail: exc.message || "Failed to upload document" },
			{ status: 500 },
		);
	}
}
