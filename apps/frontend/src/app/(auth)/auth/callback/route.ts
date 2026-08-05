import { getSafeRedirectPath } from "@/lib/auth/redirect";
import { createServerSupabaseClient } from "@/lib/supabase/server";
import { NextResponse } from "next/server";

export async function GET(request: Request) {
	const requestUrl = new URL(request.url);
	const code = requestUrl.searchParams.get("code");
	const next = getSafeRedirectPath(requestUrl.searchParams.get("next"));

	if (code) {
		const supabase = createServerSupabaseClient();
		const { error } = await supabase.auth.exchangeCodeForSession(code);
		if (!error) {
			return NextResponse.redirect(new URL(next, requestUrl.origin));
		}
	}

	const loginUrl = new URL("/login", requestUrl.origin);
	loginUrl.searchParams.set("error", "oauth_callback_failed");
	return NextResponse.redirect(loginUrl);
}
