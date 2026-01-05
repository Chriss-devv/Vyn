# VYN v1.0

VYN (Voice Your Needs) is an autonomous local AI agent designed for advanced web search, isolated code execution, remote infrastructure management, and image analysis.

---

## Technical Overview

VYN is built to operate as a local-first system, prioritizing data sovereignty and low-latency execution. Unlike cloud-based assistants, VYN functions as an extension of the local environment, interacting directly with the system kernel and remote nodes via secure protocols.

---

## Core Functionalities

* Smart Web Search: Context-aware query optimization with recursive content extraction.
* Code Sandbox: Isolated execution environment with autonomous traceback analysis and self-correction.
* Intelligent Orchestration: Dynamic model switching based on intent detection.
* Infrastructure Management: Secure SSH integration for remote server administration.
* Vision Integration: Local image analysis and terminal error visual diagnostics.
* Long-term Memory: Persistent state management using SQLite databases.
* Configuration: Interactive setup wizard for custom hardware optimization.

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