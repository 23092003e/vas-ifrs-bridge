import {
	authenticatedBackendFetch,
	forwardBackendResponse,
} from "@/lib/server/backend";
import type { NextRequest } from "next/server";

export async function GET(
	_req: NextRequest,
	{ params }: { params: Promise<{ id: string }> },
) {
	const { id } = await params;
	const conversationId = encodeURIComponent(id);
	const upstream = await authenticatedBackendFetch(
		`/v1/chat/conversations/${conversationId}`,
	);
	return forwardBackendResponse(upstream);
}

export async function DELETE(
	_req: NextRequest,
	{ params }: { params: Promise<{ id: string }> },
) {
	const { id } = await params;
	const conversationId = encodeURIComponent(id);
	const upstream = await authenticatedBackendFetch(
		`/v1/chat/conversations/${conversationId}`,
		{
			method: "DELETE",
		},
	);
	return forwardBackendResponse(upstream);
}
