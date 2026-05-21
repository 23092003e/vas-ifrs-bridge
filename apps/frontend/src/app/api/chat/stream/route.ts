import { NextRequest } from 'next/server'

const BACKEND = process.env.BACKEND_URL ?? 'http://localhost:8000'

export async function POST(req: NextRequest) {
  let body: unknown
  try {
    body = await req.json()
  } catch {
    return new Response('Invalid JSON', { status: 400 })
  }

  const upstream = await fetch(`${BACKEND}/v1/chat/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })

  if (!upstream.ok || !upstream.body) {
    const text = await upstream.text().catch(() => `HTTP ${upstream.status}`)
    return new Response(text, { status: upstream.status })
  }

  return new Response(upstream.body, {
    status: 200,
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      'X-Accel-Buffering': 'no',
    },
  })
}
