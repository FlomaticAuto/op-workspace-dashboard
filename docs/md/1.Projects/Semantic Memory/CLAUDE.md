# Olympic Paints — LanceDB Semantic Memory MCP Server

## What this is
FastMCP server wrapping LanceDB + Voyage AI for Agent OS semantic memory.
Reduces token usage by 90%+ vs loading full context into every conversation.

## How to run (PowerShell)
Start Flask API first:
  python flask_api.py

Then start MCP server (separate terminal):
  python mcp_server.py

Health check:
  Invoke-RestMethod http://localhost:5000/health

## Paths
LanceDB data:  C:\Users\quint\lancedb_data        (outside OneDrive — do not move)
Logs:          C:\Users\quint\.claude\logs\lancedb-mcp\
Scripts:       C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints\1.Projects\Seimentic Memory\

## Port assignments
Flask API:  5000
MCP/SSE:    8770

## Agent namespaces
OLY-01 → olympic_sales
OLY-02 → olympic_ops
OLY-03 → olympic_merchandising
FLO-01 → flowmatic_general
FLO-02 → flowmatic_projects
TIM-01 → timion
JBY-01 → jeffreys_bay
GLB-01 → global_shared
HR-01 → hr_shared

## Key rules
- NEVER change agent namespace names — n8n workflows depend on them
- NEVER hardcode VOYAGE_API_KEY — always load from .env
- NEVER skip embedding on store — always call embed() before writing to LanceDB
- Flask API MUST be running before MCP server starts
- NEVER move lancedb_data into OneDrive — binary files cause sync lock conflicts
- truststore.inject_into_ssl() is called at startup in flask_api.py — do not remove it
  (local AV does TLS inspection; Voyage AI HTTPS calls fail without it)

## MCP server URL for Claude Code config
http://localhost:8770/sse

## Adding this to Claude Code
In Claude Code settings, add an MCP server entry:
  Name: lancedb-memory
  URL:  http://localhost:8770/sse
  Type: sse
Both flask_api.py and mcp_server.py must be running first.
