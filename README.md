# VYN v1.0 - Autonomous Agent System

VYN (Voice Your Needs) is a local-first orchestration layer designed to transform static LLMs into autonomous agents. It provides the "system hands" (tools, sandbox, and protocols) necessary for an AI model to interact safely and effectively with your local environment and remote infrastructure.

---

## Technical Overview

VYN operates as a modular framework that abstracts complex system tasks into executable agentic flows. Unlike cloud-based wrappers, VYN prioritizes data sovereignty by leveraging local inference engines (like Ollama) and executing all operations within the host's security boundary.

---

## Core Functionalities

* Model Orchestration: Dynamic reasoning-path switching based on task complexity, optimized for local inference.
* Smart Web Search: Context-aware query optimization with recursive content extraction.
* Code Sandbox: Isolated execution environment with autonomous traceback analysis and self-correction.
* Infrastructure Management: Secure SSH integration for remote server administration.
* Vision Integration: Local image analysis and terminal error visual diagnostics.
* Long-term Memory: Persistent state management using SQLite databases.
* Configuration: Interactive setup wizard for custom hardware optimization.

---

## Engine Requirements

VYN is model-agnostic but requires a local inference provider to function:

    Ollama Runtime: Must be active on localhost:11434.

    Recommended Models: Llama 3.1 (8B/70B) or Mistral for optimal tool-calling performance.

---

## Deployment

### Prerequisites

1. Ollama Runtime:

```bash
curl -fsSL https://ollama.com/install.sh | sh
sudo systemctl start ollama

```

2. Base Model Requirement:

```bash
ollama pull llama3.1:8b

```

### Binary Installation (Linux x64)

```bash
wget https://github.com/Chriss-devv/vyn/releases/latest/download/vyn-linux-x64-v1.0.0
chmod +x vyn-linux-x64-v1.0.0
./vyn-linux-x64-v1.0.0

```

The interactive setup wizard will initialize upon the first execution to configure local paths and model preferences.

---

## Basic Commands

```text
help            Display available commands and modules
search <query>  Execute optimized web search and synthesis
code <prompt>   Generate and test code in the isolated sandbox
config          View or modify local configuration
exit            Terminate the session

```

---

## Security and Privacy

VYN operates under a Zero-External-Dependency architecture. All inference, scraping, and execution remain within the local network.

* Local-Only Inference: No data is transmitted to external AI providers.
* No Telemetry: Zero tracking or usage reporting.
* Isolated Sandbox: Script execution is contained to prevent system-wide side effects.

---

## License

Proprietary - All rights reserved.

The source code is not publicly available. For commercial licensing or source access, contact: license@vyn-ai.com

---

**Developed by Chris-devv**