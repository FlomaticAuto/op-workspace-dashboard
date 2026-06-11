# LanceDB Semantic Memory MCP Server
## Flowmatic Automation — Agent OS Memory Layer

### Architecture

```
Agent OS Agents (OLY-01, OLY-02, OLY-03, FLO-01, TIM-01, JBY-01)
        │
        ▼  MCP tool calls
┌─────────────────────┐
│   mcp_server.py     │  ← MCP server (port 8770)
│   FastMCP / SSE     │    Exposes: memory_search, memory_store,
└─────────────────────┘              memory_delete, memory_list
        │
        ▼  HTTP
┌─────────────────────┐
│   flask_api.py      │  ← Flask API (port 5000)
│   LanceDB adapter   │    Handles embedding + vector search
└─────────────────────┘
        │
        ├── LanceDB (local, ./lancedb_data/)
        └── Voyage AI API (embeddings)
```

### Token savings

| Approach              | Tokens per agent call | Notes                          |
|-----------------------|-----------------------|--------------------------------|
| Full context loading  | ~8,000–20,000         | Current approach               |
| MCP memory_search     | ~400–800              | top_k=3, ~200 tokens/result    |
| Savings               | **90–95%**            |                                |

### Setup

1. **Install dependencies**
```bash
pip install flask lancedb voyageai mcp[cli] fastmcp python-dotenv pyarrow httpx
```

2. **Create .env**
```
VOYAGE_API_KEY=your_voyage_key
LANCEDB_PATH=./lancedb_data
FLASK_PORT=5000
MCP_PORT=8770
FLASK_API_URL=http://localhost:5000
DEFAULT_TOP_K=5
```

3. **Start Flask API**
```bash
python flask_api.py
```

4. **Start MCP server**
```bash
python mcp_server.py
```

5. **Bootstrap documents**
   - Run n8n workflow using snippets in `n8n_snippets.yaml`
   - Or POST directly to `/store` for each existing SOP/document

6. **Expose Flask API to n8n cloud**
```bash
ngrok http 5000
# Use the ngrok URL in your n8n HTTP Request nodes
```

### Namespace map (Agent OS)

| Agent  | Namespace                | Contents                              |
|--------|--------------------------|---------------------------------------|
| OLY-01 | olympic_sales            | SOPs, price lists, sales reports      |
| OLY-02 | olympic_ops              | Clocking, OHS, factory SOPs           |
| OLY-03 | olympic_merchandising    | Visit reports, JotForm data           |
| FLO-01 | flowmatic_general        | Flowmatic contracts, general          |
| FLO-02 | flowmatic_projects       | TradeCraft, SuperBuys, client work    |
| TIM-01 | timion                   | Timion NPC docs, Daniel/Carl/Wian     |
| JBY-01 | jeffreys_bay             | STR ops, Krislie handoffs             |
| GLB-01 | global_shared            | Cross-agent shared knowledge          |
| HR-01  | hr_shared                | Megan/Advius, job descriptions        |

### Adding to Claude Code (claude_code_config.json)

```json
{
  "mcpServers": {
    "lancedb-memory": {
      "url": "http://localhost:8770/sse",
      "type": "sse"
    }
  }
}
```

### Metadata conventions

Always include these fields for consistent filtering:
```json
{
  "doc_type": "SOP | report | email | visit_report | contract | policy",
  "department": "sales | ops | merchandising | hr | finance",
  "date": "YYYY-MM-DD",
  "agent": "OLY-01",
  "source": "jotform | quicksight | email | manual | n8n",
  "version": "1.0"
}
```

### Health check

```bash
curl http://localhost:5000/health
```
