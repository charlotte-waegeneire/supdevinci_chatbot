# SupdeVinci Intelligent Chatbot 🤖

An intelligent multi-agent chatbot system designed for SupdeVinci school, built with LLM technology and RAG (Retrieval-Augmented Generation) capabilities.

## 🎯 Project Overview

This project implements a sophisticated chatbot that can:
- Answer questions about SupdeVinci school using web content knowledge
- Provide detailed information from institutional documents via RAG
- Collect visitor information (students, companies, professionals) and export to Excel
- Route conversations intelligently between specialized agents

## 🏗️ Architecture

The system follows a multi-agent architecture:

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Main Agent    │───▶│   Web Agent      │    │   Doc Agent     │
│  (Orchestrator) │    │ (Website Info)   │    │ (RAG Documents) │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │
         ▼
┌─────────────────┐
│  Action Agent   │
│ (Data Collection)│
└─────────────────┘
```

### Agents Description

- **Main Agent**: Orchestrates conversations, detects user intent, and routes to appropriate specialized agents
- **Web Agent**: Provides information about SupdeVinci using vectorized website content
- **Document Agent**: Answers questions using RAG on institutional documents (PDFs, guides, regulations)
- **Action Agent**: Collects user information through intelligent forms and exports to Excel

## 🛠️ Development Setup

### Prerequisites
- Python 3.8+
- Git

### Quick Setup
```bash
# Clone the repository
git clone <repository-url>
cd supdevinci_chatbot

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Setup development environment (installs deps + pre-commit hooks)
make setup-dev
```

### Development Commands
```bash
# Show all available commands
make help

# Run linting
make lint

# Run linting with auto-fix
make lint-fix

# Format code
make format

# Run all checks
make check

# Run the app
make run

# Clean cache files
make clean
```

### Code Quality
This project uses **Ruff** for linting and formatting, configured to run automatically on every commit via pre-commit hooks.

- **Automatic**: Ruff runs on every `git commit`
- **Manual**: Use `make lint-fix` and `make format`
- **Skip hooks**: Use `git commit --no-verify` (not recommended)

The configuration includes:
- Code formatting (Black-compatible)
- Import sorting (isort)
- Security checks (bandit)
- Performance optimizations
- PEP 8 compliance

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👥 Team

- **Project Lead**: Charlotte Waegeneire
- **Development Team**: Chloé Gerardin, Denis Kirat, Steven Sivakaran, Amine Benyahya
- **Academic Supervisor**: Ali Mokh

**Note**: This is an academic project for SupdeVinci school. All data collection respects GDPR regulations and uses simulated data for demonstration purposes.
