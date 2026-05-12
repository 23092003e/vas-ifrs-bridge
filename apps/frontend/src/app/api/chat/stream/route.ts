import { NextRequest } from 'next/server'

export async function POST(req: NextRequest) {
  // Proxy SSE to FastAPI /v1/chat/stream
  return new Response('Not implemented', { status: 501 })
}
