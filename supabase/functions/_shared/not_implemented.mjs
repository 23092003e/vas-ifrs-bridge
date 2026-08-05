const JSON_HEADERS = { "Content-Type": "application/json" };

export function createNotImplementedHandler(feature) {
  return async function handler(request) {
    if (request.method !== "POST") {
      return new Response(JSON.stringify({ ok: false, error: "Method not allowed" }), {
        status: 405,
        headers: { ...JSON_HEADERS, Allow: "POST" },
      });
    }

    return new Response(
      JSON.stringify({ ok: false, error: `${feature} is not implemented` }),
      { status: 501, headers: JSON_HEADERS },
    );
  };
}
