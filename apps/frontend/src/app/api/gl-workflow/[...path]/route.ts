import {
	authenticatedBackendFetch,
	forwardBackendResponse,
} from "@/lib/server/backend";
import type { NextRequest } from "next/server";

const uuid = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
type Context = { params: Promise<{ path: string[] }> };

function backendPath(method: string, segments: string[]) {
	const [resource, id, action] = segments;
	if (
		!id &&
		method === "GET" &&
		["gl", "mappings", "adjustments", "reports"].includes(resource)
	) {
		return `/v1/${resource}/`;
	}
	if (segments.length === 2) {
		if (
			method === "POST" &&
			((resource === "gl" && id === "upload") ||
				(resource === "reports" && id === "generate"))
		) {
			return `/v1/${resource}/${id}`;
		}
		if (
			method === "PUT" &&
			resource === "mappings" &&
			/^[\p{L}\p{N}_.-]{1,50}$/u.test(id) &&
			id !== "." &&
			id !== ".."
		) {
			return `/v1/mappings/${encodeURIComponent(id)}`;
		}
		if (method === "GET" && resource === "reports" && uuid.test(id))
			return `/v1/reports/${id}`;
	}
	if (segments.length === 3 && uuid.test(id)) {
		if (
			(method === "GET" &&
				((resource === "gl" && action === "status") ||
					(resource === "reports" && action === "download"))) ||
			(method === "POST" &&
				((resource === "gl" && action === "remap") ||
					(resource === "adjustments" &&
						(action === "approve" || action === "reject"))))
		)
			return `/v1/${resource}/${id}/${action}`;
	}
	if (segments.length === 1 && method === "POST" && resource === "adjustments")
		return "/v1/adjustments/";
	return null;
}

async function handler(req: NextRequest, { params }: Context) {
	const { path } = await params;
	const upstreamPath = backendPath(req.method, path);
	if (!upstreamPath)
		return Response.json({ detail: "Route not found" }, { status: 404 });

	const headers = new Headers();
	const contentType = req.headers.get("Content-Type");
	const key = req.headers.get("Idempotency-Key");
	if (contentType) headers.set("Content-Type", contentType);
	if (key) headers.set("Idempotency-Key", key);
	const uploadId = req.nextUrl.searchParams.get("upload_id");
	const filteredList =
		upstreamPath === "/v1/reports/" || upstreamPath === "/v1/adjustments/";
	if (uploadId !== null && filteredList && !uuid.test(uploadId)) {
		return Response.json({ detail: "Invalid upload ID" }, { status: 422 });
	}
	const upstream = await authenticatedBackendFetch(upstreamPath, {
		query:
			uploadId && filteredList
				? new URLSearchParams({ upload_id: uploadId })
				: undefined,
		method: req.method,
		headers,
		...(req.body ? { body: req.body, duplex: "half" } : {}),
		signal: req.signal,
	});
	const response = forwardBackendResponse(upstream);
	const disposition = upstream.headers.get("Content-Disposition");
	if (disposition) response.headers.set("Content-Disposition", disposition);
	response.headers.set("Cache-Control", "no-store");
	return response;
}

export { handler as GET, handler as POST, handler as PUT };
