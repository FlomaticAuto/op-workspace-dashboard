# Ollama Dashboard

## Prerequisites
- Ollama installed and running: `ollama serve`
- Model pulled: `ollama pull nomic-embed-text-v1.5`
- Python 3.8+

## Start
```bash
cd ollama-dashboard
./start.sh
```
Open `ollama-dashboard.html` in your browser.

## Endpoints
| Endpoint | Method | Purpose |
|---|---|---|
| /status | GET | Health check + pulled models |
| /loaded | GET | Models in memory |
| /embed | POST | Generate 768-dim embedding |
| /pull | POST | Pull a new model |
