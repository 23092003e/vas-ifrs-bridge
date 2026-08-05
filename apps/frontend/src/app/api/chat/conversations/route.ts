import {
	authenticatedBackendFetch,
	forwardBackendResponse,
} from "@/lib/server/backend";

export async function GET() {
	const upstream = await authenticatedBackendFetch("/v1/chat/conversations");
	return forwardBackendResponse(upstream);
}
