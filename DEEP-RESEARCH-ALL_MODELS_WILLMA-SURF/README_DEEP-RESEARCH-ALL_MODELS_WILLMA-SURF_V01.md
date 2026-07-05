# DEEP-RESEARCH-ALL_MODELS_WILLMA-SURF in Langflow

This folder contains the Langflow JSON export for the **DEEP-RESEARCH-ALL_MODELS_WILLMA-SURF** flow [file:1]. 
This advanced multi-agent workflow is designed to perform comprehensive, automated research on a specific question or topic [file:1].

## 🧠 Flow Overview

The flow uses a multi-step agentic architecture powered by WILLMA (SURF) endpoints. It breaks down complex research queries, searches the web, summarizes findings, reviews the content, and synthesizes a final, professional research report.

### Key Components

The architecture relies on the following core Langflow node types:
*   **Chat Input**: Receives the initial research topic/question from the user [file:1].
*   **Web Search (No API)** & **URL Component**: Fetches and aggregates external information directly from the web without requiring commercial search API keys [file:1].
*   **Multi-Agent Research Pipeline**: 5 specialized `Agent` nodes, utilizing various LLM models from SURF:
    *   **Research Assistant** (`mistralai/Mistral-Small-3.2-24B-Instruct-2506`): Explores the query and directs the search [file:1].
    *   **Summarization Expert** (`Qwen/Qwen2.5-VL-32B-Instruct-AWQ`): Condenses findings for each sub-question [file:1].
    *   **Research Reviewer** (`openai/gpt-oss-120b`): Analyzes and reviews the gathered information for quality and relevance (x2 instances) [file:1].
    *   **Professional Research Writer** (`openai/gpt-oss-120b`): Synthesizes the reviewed content into a cohesive, comprehensive final report [file:1].
*   **Chat Output**: Delivers the final generated report (and intermediate steps, as configured) back to the user interface [file:1].

## 🚀 How to Import and Use

### Prerequisites
*   A running instance of Langflow.
*   Access to the **SURF WILLMA** API endpoints for the specified open-weight models (Mistral, Qwen, and custom endpoints like `gpt-oss-120b`).

### Import Steps
1.  Download the `DEEP-RESEARCH-ALL_MODELS_WILLMA-SURF.json` file from this repository.
2.  Open your Langflow UI.
3.  Click on the **Import** button (usually represented by a cloud upload icon) in the top right corner of the dashboard.
4.  Select the downloaded JSON file.
5.  Once imported, open the flow.

### Configuration
1.  **API Keys & Endpoints**: Check each `Agent (WILLMA SURF)` node. You will need to input your SURF WILLMA API Key and ensure the Base URLs are pointing to your active infrastructure.
2.  **Web Search**: Ensure your Langflow environment has the necessary network access to execute the `WebSearchNoAPI` and `URL` components.

### Execution
1.  Click the chat icon in the bottom right corner of the Langflow UI.
2.  Type your broad research question (e.g., "What are the latest developments in Digital Twin architecture for healthcare?").
3.  Watch as the multi-agent system breaks down the query, searches, reviews, and writes the final report.

## 🛠️ Customization

You can easily adapt this template for your own infrastructure:
*   **Swap Models**: If you want to use different endpoints (e.g., Azure OpenAI or local Ollama), you can replace the WILLMA SURF agent nodes with standard LLM nodes.
*   **Adjust Prompts**: The system prompts for the Assistant, Summarizer, Reviewer, and Writer agents can be customized within their respective nodes to change the tone, format, or strictness of the final output.