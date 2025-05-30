# SupdeVinci Intelligent Chatbot 🤖

An intelligent multi-agent chatbot system designed for SupdeVinci school, built with LLM technology and RAG (Retrieval-Augmented Generation) capabilities using Azure OpenAI and LangChain.

## 🎯 Project Overview

This project implements a sophisticated chatbot that can:
- **Answer questions about SupdeVinci school** using web content knowledge via vector search
- **Provide detailed information** from institutional documents using RAG (Retrieval-Augmented Generation)
- **Collect visitor information** (students, companies, professionals) through intelligent forms
- **Export collected data** to Excel for CRM integration
- **Route conversations intelligently** between specialized agents based on user intent

## 🚀 Features

### For End Users
- 🌐 **School Information**: Get answers about formations, admissions, campus locations
- 📚 **Document Search**: Query institutional documents, regulations, and guides
- 📝 **Contact Forms**: Interactive data collection with validation
- 💬 **Natural Conversations**: Multi-turn conversations with context awareness
- 📱 **User-Friendly Interface**: Clean Streamlit web interface

### For Administrators
- 📊 **Data Export**: Automatic Excel export of collected user information
- 📈 **Analytics**: Conversation statistics and agent performance metrics
- 🔧 **Modular Architecture**: Easy to extend with new agents and capabilities
- 🛡️ **Data Validation**: Built-in validation for phone numbers, emails, names

## 🏗️ Architecture

The system follows a multi-agent architecture with intelligent routing:

```
┌──────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│    Main Agent    │───▶│   Web Agent      │    │   Doc Agent     │
│   (Orchestrator) │    │ (Website Info)   │    │ (RAG Documents) │
└──────────────────┘    └──────────────────┘    └─────────────────┘
         │
         ▼
┌──────────────────┐    ┌──────────────────┐
│   Action Agent   │    │  Web Scraper     │
│ (Data Collection)│    │  (Content Sync)  │
└──────────────────┘    └──────────────────┘
```

### Agents Description

- **Main Agent**: Orchestrates conversations, detects user intent, and routes to appropriate specialized agents
- **Web Agent**: Provides information about SupdeVinci using vectorized website content (Chroma DB + HuggingFace embeddings)
- **Document Agent**: Answers questions using RAG on institutional documents (PDFs, guides, regulations)
- **Action Agent**: Collects user information through intelligent forms with state management
- **Web Scraper**: Automatically scrapes and updates website content for the Web Agent

## 🛠️ Development Setup

### Prerequisites
- Python 3.8+
- Git
- Azure OpenAI access (API key and endpoint)

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

### Environment Configuration

Create a `.env` file in the project root:

```env
# Azure OpenAI Configuration (Required)
AZURE_OPENAI_API_KEY=your_api_key_here
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_VERSION=2024-02-15-preview
AZURE_DEPLOYMENT_NAME=your_deployment_name

# Data Storage Paths
EXCEL_FILEPATH=./data/exports/
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

### Project Structure
```
supdevinci_chatbot/
├── chatbot/
│   ├── agents/                 # Multi-agent system
│   │   ├── main_agent.py      # Main orchestrator
│   │   ├── web_agent.py       # Website information agent
│   │   ├── doc_agent.py       # Document RAG agent
│   │   ├── form_agent.py      # Data collection agent
│   │   └── sdv_scrapper.py    # Website scraper
│   ├── pages/                 # Streamlit pages
│   │   ├── home.py           # Homepage
│   │   └── chatbot.py        # Chat interface
│   ├── data/                 # Data storage
│   │   ├── documents/        # PDF documents for RAG
│   │   ├── website_pages/    # Scraped website content
│   │   ├── vectorstore/      # Chroma vector databases
│   │   └── exports/          # Excel exports
│   └── utils.py             # Utility functions
├── app.py                   # Main Streamlit application
├── requirements.txt         # Python dependencies
├── .env                    # Environment variables
└── README.md              # This file
```

## 🚀 Quick Start

### 1. For End Users (Using the Chatbot)

1. **Access the Application**
   ```bash
   streamlit run chatbot/app.py
   ```
   or
   ```bash
   make run
   ```

2. **Navigate the Interface**
   - **Home Page**: Overview of SupdeVinci school and statistics
   - **Chatbot Page**: Interactive conversation interface

3. **Ask Questions**
   - "Quelles formations proposez-vous ?"
   - "Comment candidater chez SupdeVinci ?"
   - "Où sont situés vos campus ?"

4. **Contact Process**
   - Say "Je suis intéressé" to start information collection
   - Follow the guided form (name, phone, email)
   - Receive confirmation and next steps

### 2. For Developers (Extending the System)

#### Adding a New Agent

1. **Create Agent Class**
   ```python
   # chatbot/agents/new_agent.py
   class NewAgent:
       def __init__(self):
           # Initialize your agent
           pass

       def query(self, question: str) -> str:
           # Process the question
           return "Response"
   ```

2. **Register in Main Agent**
   ```python
   # In main_agent.py
   def _initialize_agents(self):
       self.new_agent = NewAgent()

   def detect_intent(self, user_input: str) -> str:
       # Add new intent detection logic
       if "new_keyword" in user_input.lower():
           return "new_intent"
   ```

#### Adding New Data Sources

1. **For Web Agent**: Update `sdv_scrapper.py` to include new URLs
2. **For Doc Agent**: Add PDF files to `chatbot/data/documents/`
3. **Rebuild Vector Stores**: Delete existing vectorstore folders to trigger rebuild

### Vector Store Configuration

The system uses Chroma for vector storage with HuggingFace embeddings:

- **Embedding Model**: `sentence-transformers/all-MiniLM-L6-v2`
- **Chunk Size**: 800-1000 characters
- **Chunk Overlap**: 150-200 characters
- **Search Type**: MMR (Maximal Marginal Relevance)

## 📊 Data Management

### Excel Export Format

Collected user data is exported to Excel with the following columns:

| Column | Description | Example |
|--------|-------------|---------|
| nom | Last name | Dupont |
| prenom | First name | Marie |
| telephone | Phone number | 06.12.34.56.78 |
| email | Email address | marie.dupont@email.com |
| timestamp | Collection time | 2024-01-15T10:30:00 |

### Data Validation

The system includes comprehensive validation:

- **Phone Numbers**: French mobile/landline formats
- **Email Addresses**: RFC-compliant email validation
- **Names**: Alphabetic characters, hyphens, spaces allowed
- **Required Fields**: All fields are mandatory

### GDPR Compliance

- ✅ Explicit consent collection
- ✅ Data minimization (only necessary fields)
- ✅ Transparent processing (clear purpose)
- ✅ User rights information provided
- ✅ Secure data storage and export
