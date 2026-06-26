# Local Persian ERP AI Agent 🧠🤖

An autonomous, fully local AI Agent built to interact with an ERP database using a Lightweight Large Language Model (SLM). The system converts natural language Persian queries into structured SQL commands, executes them safely, and returns clean, structured responses entirely offline.

## ✨ Key Features
* **100% Local & Private:** Powered by Ollama (`llama3.2:1b`), ensuring no data leaves the local machine.
* **Agentic Workflow:** Implements an autonomous agent capable of database schema inspection, tool calling, and structured reasoning.
* **Optimized for SLMs:** Custom prompt engineering designed to eliminate hallucinations in 1B/3B parameter models by structuring outputs into clean Persian bulleted lists instead of heavy markdown tables.
* **Interactive UI:** Built with Streamlit for a smooth, user-friendly Persian (RTL) chat interface.

## 🛠️ Tech Stack
* **LLM Engine:** Ollama (`llama3.2:1b` / `qwen2.5`)
* **Framework:** Python, Streamlit
* **Database:** SQLite (Simulated ERP System)
* **Agent Architecture:** Tool-use & Custom System Prompts
* ## 🚀 How to Run

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/12345zahraa/local-persian-erp-ai-agent.git](https://github.com/12345zahraa/local-persian-erp-ai-agent.git)
   cd local-persian-erp-ai-agent
   Install dependencies:
Make sure you have your virtual environment activated, then run:
pip install -r requirements.txt
2. Start Ollama Engine:
Ensure Ollama is running locally and you have the model pulled:
ollama pull llama3.2:1b
3. Run the Application:
Launch the Streamlit dashboard using:

Bas
