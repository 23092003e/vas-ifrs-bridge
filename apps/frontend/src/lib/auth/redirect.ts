const DEFAULT_AUTH_REDIRECT = "/chat";

export function getSafeRedirectPath(value: string | null): string {
	if (!value || !value.startsWith("/") || value.startsWith("//")) {
		return DEFAULT_AUTH_REDIRECT;
	}

	try {
		const base = new URL("https://local.invalid");
		const target = new URL(value, base);
		if (target.origin !== base.origin) return DEFAULT_AUTH_REDIRECT;
		return `${target.pathname}${target.search}${target.hash}`;
	} catch {
		return DEFAULT_AUTH_REDIRECT;
	}
}
