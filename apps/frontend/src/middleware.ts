import { type CookieOptions, createServerClient } from "@supabase/ssr";
import { type NextRequest, NextResponse } from "next/server";

import { getSupabaseConfig } from "@/lib/supabase/config";

export async function middleware(request: NextRequest) {
	let response = NextResponse.next({
		request: {
			headers: request.headers,
		},
	});

	const { url, anonKey } = getSupabaseConfig();
	const supabase = createServerClient(url, anonKey, {
		cookies: {
			getAll() {
				return request.cookies.getAll();
			},
			setAll(
				cookiesToSet: {
					name: string;
					value: string;
					options: CookieOptions;
				}[],
			) {
				for (const { name, value } of cookiesToSet) {
					request.cookies.set({ name, value });
				}
				response = NextResponse.next({
					request: {
						headers: request.headers,
					},
				});
				for (const { name, value, options } of cookiesToSet) {
					response.cookies.set({ name, value, ...options });
				}
			},
		},
	});

	const {
		data: { user },
	} = await supabase.auth.getUser();

	const path = request.nextUrl.pathname;
	const isAuthPage =
		path.startsWith("/login") ||
		path.startsWith("/signup") ||
		path.startsWith("/auth/callback");

	const isPublicPage = path === "/" || isAuthPage;

	// Bypass static and api endpoints
	const isStaticOrApi =
		path.startsWith("/_next") ||
		path.startsWith("/api") ||
		path.includes(".") ||
		path === "/favicon.ico";

	if (isStaticOrApi) {
		return response;
	}

	if (!user && !isPublicPage) {
		// Redirect to login if trying to access app without session
		return NextResponse.redirect(new URL("/login", request.url));
	}

	if (user && isAuthPage) {
		// Redirect to chat if already logged in
		return NextResponse.redirect(new URL("/chat", request.url));
	}

	return response;
}

export const config = {
	matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};
