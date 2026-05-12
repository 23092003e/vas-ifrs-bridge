import { serve } from 'https://deno.land/std@0.208.0/http/server.ts'

serve(async (_req) => {
  // Triggered by Supabase Storage on document upload
  // TODO: enqueue ingestion task via Redis/Celery
  return new Response(JSON.stringify({ ok: true }), {
    headers: { 'Content-Type': 'application/json' },
  })
})
