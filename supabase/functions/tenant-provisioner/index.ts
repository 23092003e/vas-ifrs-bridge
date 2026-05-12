import { serve } from 'https://deno.land/std@0.208.0/http/server.ts'

serve(async (_req) => {
  // Provisions Qdrant collection and GCS folder for a new tenant
  // TODO: call backend /admin/tenants/:id/provision
  return new Response(JSON.stringify({ ok: true }), {
    headers: { 'Content-Type': 'application/json' },
  })
})
