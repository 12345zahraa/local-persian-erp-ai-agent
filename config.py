"""Project-wide constants for the local ERP MCP agent."""
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
DB_PATH = ROOT_DIR / "erp_demo.db"
DB_NAME = "erp_demo.db"
MODEL_NAME = "llama3.2:1b"
OLLAMA_MODEL = MODEL_NAME
OLLAMA_HOST = "http://localhost:11434"
MAX_TOOL_STEPS = 6
