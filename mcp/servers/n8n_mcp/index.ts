import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";

const N8N_BASE_URL = process.env.N8N_BASE_URL || "http://localhost:5678";
const N8N_API_KEY = process.env.N8N_API_KEY || "";
const REQUEST_TIMEOUT_MS = 15_000;

function normalizeBaseUrl(baseUrl: string): string {
  const url = new URL(baseUrl);
  if (!["http:", "https:"].includes(url.protocol) || url.username || url.password) {
    throw new Error("N8N_BASE_URL must be an HTTP(S) URL without credentials");
  }
  url.search = "";
  url.hash = "";
  return url.toString().replace(/\/$/, "");
}

export function buildWorkflowUrl(baseUrl: string, workflowId: string): string {
  const normalizedId = workflowId.trim();
  if (!normalizedId) {
    throw new Error("workflowId is required");
  }
  return `${normalizeBaseUrl(baseUrl)}/api/v1/workflows/${encodeURIComponent(normalizedId)}`;
}

export function buildWebhookUrl(baseUrl: string, webhookPath: string): string {
  const normalizedPath = webhookPath.replace(/^\/+|\/+$/g, "");
  if (!/^[A-Za-z0-9_-]+(?:\/[A-Za-z0-9_-]+)*$/.test(normalizedPath)) {
    throw new Error("Invalid webhook path");
  }
  return `${normalizeBaseUrl(baseUrl)}/webhook/${normalizedPath}`;
}

const server = new Server(
  {
    name: "n8n-mcp-server",
    version: "0.1.0",
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

// Define tools
const TOOLS = [
  {
    name: "n8n_list_workflows",
    description: "List all workflows configured in the n8n server.",
    inputSchema: {
      type: "object",
      properties: {},
    },
  },
  {
    name: "n8n_get_workflow",
    description: "Fetch details of a specific workflow by its ID.",
    inputSchema: {
      type: "object",
      properties: {
        workflowId: { type: "string", description: "The ID of the workflow" },
      },
      required: ["workflowId"],
    },
  },
  {
    name: "n8n_trigger_webhook",
    description: "Trigger an n8n workflow using a webhook path and payload.",
    inputSchema: {
      type: "object",
      properties: {
        webhookPath: { type: "string", description: "The webhook path (e.g. 'ingest-doc')" },
        payload: { type: "object", description: "JSON payload to send to the webhook" },
      },
      required: ["webhookPath", "payload"],
    },
  },
];

server.setRequestHandler(ListToolsRequestSchema, async () => {
  return { tools: TOOLS };
});

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  const headers: Record<string, string> = {
    "Accept": "application/json",
    "Content-Type": "application/json",
  };
  if (N8N_API_KEY) {
    headers["X-N8N-API-KEY"] = N8N_API_KEY;
  }

  try {
    switch (name) {
      case "n8n_list_workflows": {
        const url = `${normalizeBaseUrl(N8N_BASE_URL)}/api/v1/workflows`;
        const res = await fetch(url, {
          headers,
          signal: AbortSignal.timeout(REQUEST_TIMEOUT_MS),
        });
        if (!res.ok) {
          throw new Error(`n8n responded with status ${res.status}: ${await res.text()}`);
        }
        const data = await res.json();
        return {
          content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
        };
      }

      case "n8n_get_workflow": {
        const { workflowId } = args as { workflowId: string };
        const url = buildWorkflowUrl(N8N_BASE_URL, workflowId);
        const res = await fetch(url, {
          headers,
          signal: AbortSignal.timeout(REQUEST_TIMEOUT_MS),
        });
        if (!res.ok) {
          throw new Error(`n8n responded with status ${res.status}: ${await res.text()}`);
        }
        const data = await res.json();
        return {
          content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
        };
      }

      case "n8n_trigger_webhook": {
        const { webhookPath, payload } = args as { webhookPath: string; payload: object };
        const url = buildWebhookUrl(N8N_BASE_URL, webhookPath);
        const res = await fetch(url, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
          signal: AbortSignal.timeout(REQUEST_TIMEOUT_MS),
        });
        const text = await res.text();
        if (!res.ok) {
          throw new Error(`n8n webhook responded with status ${res.status}: ${text}`);
        }
        return {
          content: [
            {
              type: "text",
              text: `Status: ${res.status}\nResponse: ${text}`,
            },
          ],
        };
      }

      default:
        throw new Error(`Unknown tool: ${name}`);
    }
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : String(err);
    return {
      isError: true,
      content: [{ type: "text", text: message }],
    };
  }
});

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("n8n MCP server running on stdio");
}

if (require.main === module) {
  main().catch((err) => {
    console.error("Fatal error running n8n MCP server:", err);
    process.exit(1);
  });
}
