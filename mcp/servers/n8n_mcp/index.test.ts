import assert from "node:assert/strict";
import test from "node:test";

import { buildWebhookUrl, buildWorkflowUrl } from "./index.js";

test("workflow IDs cannot change the n8n API path", () => {
  assert.equal(
    buildWorkflowUrl("http://localhost:5678", "workflow/with?controls"),
    "http://localhost:5678/api/v1/workflows/workflow%2Fwith%3Fcontrols",
  );
});

test("webhook paths stay below the webhook endpoint", () => {
  assert.equal(
    buildWebhookUrl("http://localhost:5678", "documents/ingest-1"),
    "http://localhost:5678/webhook/documents/ingest-1",
  );
  assert.throws(
    () => buildWebhookUrl("http://localhost:5678", "../api/v1/workflows"),
    /invalid webhook path/i,
  );
  assert.throws(
    () => buildWebhookUrl("http://localhost:5678", "hook?token=leak"),
    /invalid webhook path/i,
  );
});
