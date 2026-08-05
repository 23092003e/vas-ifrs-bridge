import assert from "node:assert/strict";
import test from "node:test";

import { handler as documentHandler } from "./on-document-upload/handler.mjs";
import { handler as glHandler } from "./on-gl-upload/handler.mjs";
import { handler as tenantHandler } from "./tenant-provisioner/handler.mjs";

const cases = [
  ["document ingestion", documentHandler],
  ["GL processing", glHandler],
  ["tenant provisioning", tenantHandler],
];

for (const [feature, handler] of cases) {
  test(`${feature} webhook does not acknowledge work it cannot enqueue`, async () => {
    const response = await handler(new Request("http://localhost", { method: "POST" }));
    const body = await response.json();

    assert.equal(response.status, 501);
    assert.deepEqual(body, {
      ok: false,
      error: `${feature} is not implemented`,
    });
  });

  test(`${feature} webhook only accepts POST`, async () => {
    const response = await handler(new Request("http://localhost", { method: "GET" }));

    assert.equal(response.status, 405);
    assert.equal(response.headers.get("allow"), "POST");
  });
}
