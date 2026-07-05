# README - Deep Research Multi-Agent Pipeline (WILLMA SURF) in Langflow

## Inleiding

Deze README beschrijft stap voor stap hoe de werkende Langflow is opgebouwd uit het bestand `DEEP-RESEARCH-ALL_MODELS_WILLMA-SURF.json`. 

De flow implementeert een geavanceerde **Multi-Agent Deep Research pipeline** met:

- een `Chat Input` voor het ontvangen van de hoofdvraag van de gebruiker
- een custom `WebSearchNoAPI` component voor het uitvoeren van zoekopdrachten zonder commerciële API keys
- een `URLComponent` voor het fetchen en parsen van webpagina's
- een reeks van 5 gespecialiseerde `Agent (WILLMA SURF)` componenten die achtereenvolgens onderzoek doen, samenvatten, reviewen en uitschrijven.
- meerdere `Chat Output` componenten om de voortgang en het eindresultaat te tonen

Het doel van deze flow is: een complexe gebruikersvraag aannemen, het internet doorzoeken met behulp van AI, de bevindingen analyseren op kwaliteit en relevantie, en uiteindelijk een gedetailleerd, gestructureerd onderzoeksrapport genereren. Dit zorgt voor een traceerbare data lineage (belangrijk voor data stewards) en reproduceerbare truth-finding.

## Overzicht van de flow

Hieronder is de visuele weergave van de architectuur te zien. De keten van agenten is aan elkaar gekoppeld, beginnend bij de input en eindigend bij de verschillende output stappen.


![Langflow Deep Research Pipeline Overview](../FIGs/TOP_TIER_PROMPT_ANSWER_001.pn)
*(Visualisatie van de opstelling in Langflow met de 5 WILLMA SURF Agent nodes gekoppeld aan de Web Search en Chat in/outputs)*

Schematisch ziet de flow er als volgt uit:

```text
[Chat Input] -> [Agent: Research Assistant] -> [Agent: Summarization Expert]
                        |                                |
                        v                                v
                 [WebSearchNoAPI]                  [Agent: Research Reviewer 1]
                        |                                |
                        v                                v
                 [URLComponent]                    [Agent: Research Reviewer 2]
                                                         |
                                                         v
                                              [Agent: Professional Writer]
                                                         |
                                                         v
                                                   [Chat Output]
```

Elke agent heeft zijn eigen specifieke taak in de workflow en maakt gebruik van verschillende LLM modellen gehost op de SURF infrastructuur via de WILLMA OpenAI-compatible API.

---

## De Componenten in detail

Hieronder volgt een gedetailleerde uitleg van de belangrijkste componenten, inclusief de custom code en de specifieke systeemprompts die zijn gebruikt om de agenten aan te sturen.

### 1. Chat Input & Output
De standaard Langflow componenten om het gesprek met de gebruiker te starten en af te sluiten. Ze vereisen geen speciale configuratie behalve de mapping van de invoer naar de eerste Agent.

### 2. Web Search No API (`WebSearchNoAPI`)
Deze custom component maakt het mogelijk om DuckDuckGo (HTML iteratie) te scrapen zonder dat er een betaalde API-key nodig is.

**Kerntaak in Python:**
```python
import re
from urllib.parse import parse_qs, unquote, urlparse
import pandas as pd
import requests
from bs4 import BeautifulSoup

# ... [imports and class definition omitted for brevity] ...

    def fetch_duckduckgo_html(self, query: str, max_results: int = 5) -> list[dict]:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        url = f"https://html.duckduckgo.com/html/?q={requests.utils.quote(query)}"
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            
            results = []
            for result in soup.find_all("div", class_="result"):
                if len(results) >= max_results:
                    break
                    
                title_elem = result.find("h2", class_="result__title")
                snippet_elem = result.find("a", class_="result__snippet")
                
                if title_elem and snippet_elem:
                    raw_url = title_elem.find("a")["href"]
                    parsed_url = urlparse(raw_url)
                    actual_url = parse_qs(parsed_url.query).get("uddg", [raw_url])
                    
                    results.append({
                        "title": title_elem.text.strip(),
                        "url": unquote(actual_url),
                        "snippet": snippet_elem.text.strip()
                    })
            return results
```

### 3. Agent: WILLMA SURF
Dit is de kerncomponent van de flow. Er zijn 5 iteraties van deze component gebruikt, gebaseerd op een aangepaste `AgentComponent` die compatibel is gemaakt voor SURF's WILLMA endpoints (OpenAI-compatible).

**Custom Python Code (Snippet):**
```python
# Agent-WILLMA-langflowv1.10.1.py
# Adapted AgentComponent that uses SURF WILLMA (OpenAI-compatible API)

from typing import cast
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from lfx.base.agents.agent import LCToolCallingAgentComponent

class CustomWILLMAAgent(LCToolCallingAgentComponent):
    display_name = "Agent (WILLMA SURF)"
    description = "Use to perform multi-agent research."
    
    # ... component inputs (api_key, base_url, model_name, etc) ...

    def create_agent_runnable(self):
        # Configure ChatOpenAI to hit WILLMA SURF endpoints
        llm = ChatOpenAI(
            model=self.model_name,
            api_key=self.api_key or "sk-dummy",
            base_url=self.base_url or "https://chat-ai.academiccloud.nl/v1",
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            stream=self.stream
        )
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", self.system_prompt),
            MessagesPlaceholder(variable_name="chat_history", optional=True),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        runnable = create_tool_calling_agent(llm, self.tools, prompt)
        return runnable
```

---

## De 5 Agenten en hun Prompts

De multi-agent orchestratie is opgebouwd door het systematisch doorgeven van data tussen 5 specifieke agenten, elk ingesteld met een eigen SURF model en *System Prompt*.

### Agent 1: The Research Assistant
- **Model:** `mistralai/Mistral-Small-3.2-24B-Instruct-2506`
- **Doel:** Begrijpt de vraag en voert zoekopdrachten uit met de `WebSearchNoAPI` tool.
- **System Prompt (Excerpt):**
  > "You are a research assistant with access to search tools. For each sub-question below, find the most relevant information. Break down complex queries, use multiple search variations, and gather diverse sources. Pass your raw findings to the Summarizer."

### Agent 2: The Summarization Expert
- **Model:** `Qwen/Qwen2.5-VL-32B-Instruct-AWQ`
- **Doel:** Ontvangt de ruwe HTML/zoekresultaten en condenseert deze.
- **System Prompt (Excerpt):**
  > "You are a summarization expert. For each sub-question and its associated sources, extract the most important facts, data points, and context. Discard fluff. Ensure you cite the source URLs for every factual claim you summarize."

### Agent 3 & 4: The Research Reviewers (x2)
- **Model:** `openai/gpt-oss-120b`
- **Doel:** Beoordelen de samengevatte teksten op volledigheid en relevantie ten opzichte van de originele gebruikersvraag. Twee iteraties (of parallelle beoordelaars) worden gebruikt om hallucinaties tegen te gaan.
- **System Prompt (Excerpt):**
  > "You are a research reviewer. Your job is to analyze the current coverage of all sub-questions and identify missing links, logical gaps, or unsupported claims. If the information is insufficient, state exactly what is missing."

### Agent 5: The Professional Research Writer
- **Model:** `openai/gpt-oss-120b`
- **Doel:** Synthetiseert al het goedgekeurde materiaal tot een professioneel eindrapport.
- **System Prompt (Excerpt):**
  > "You are a professional research writer. Your task is to synthesize a structured report that fully answers the user's main query based ONLY on the provided reviewed context. Use Markdown headers, bullet points for readability, and include inline citations [URL] for your claims. Do not invent information."

---

## Praktijkvoorbeeld: "What are top TIER LLMs?"

Om voor data scientists en stewards de validatiestappen en data lineage visueel te maken, tonen we hieronder hoe de architectuur stapsgewijs de complexe vraag *"What are top TIER LLMs?"* verwerkt.

### Stap 1: Het probleem van naïeve bevraging
Wanneer we een dergelijke vraag direct aan een model stellen zonder research-flow, botst het tegen kennislimieten aan en kan het geen up-to-date, gevalideerde lijst genereren.

![Generiek Antwoord Zonder Research](FIGs/TOP_TIER_PROMPT_ANSWER_001.jpg)
*(Standaard LLM output zonder toegang tot live data)*

### Stap 2: Activering van de Reviewer & Summarizer Agents
Zodra de flow start, analyseert *Agent 3 & 4 (Reviewers)* de ontbrekende informatie ('Gaps') op basis van de initiële aannames. Ze instrueren de onderliggende search/summarize agents over wat er precies ontbreekt (zoals benchmark scores, multimodale parameters, etc.). 

![Gaps en Nieuwe Subvragen Deel 1](./FIGs/TOP_TIER_PROMPT_ANSWER_003-4.jpg)
![Gaps en Nieuwe Subvragen Deel 2](../FIGs/TOP_TIER_PROMPT_ANSWER_004-5.jpg)
*(De Reviewer agents identificeren hiaten en sturen iteratief het onderzoek aan)*

*Agent 2 (Summarization Expert)* verzamelt vervolgens de vers geparste web-data en synthetiseert betrouwbare, controleerbare (bron-geciteerde) samenvattingen voor elke subvraag.
![Summaries Subvraag](FIGs/TOP_TIER_PROMPT_ANSWER_002-3.jpg)

### Stap 3: Synthese door de Professional Writer
Ten slotte compileert *Agent 5 (Professional Writer)* alle gevalideerde feiten in één overzichtelijk, methodologisch verantwoord rapport. Hierbij worden definities strak afgebakend en data netjes verwerkt in vergelijkingstabellen, waardoor de informatie direct bruikbaar is voor data stewards.

![Eindrapport Deel 1 - Definitie](../FIGs/TOP_TIER_PROMPT_FINAL_ANSWER_005-6.jpg)
![Eindrapport Deel 2 - Model Overzicht Tabel](../FIGs/TOP_TIER_PROMPT_FINAL_ANSWER_006-7.jpg)
![Eindrapport Deel 3 - Open Source vs Proprietary](../FIGs/TOP_TIER_PROMPT_FINAL_ANSWER_007-8.jpg)
*(Het gegenereerde eindrapport, inclusief gestructureerde vergelijkingen tussen LLM's)*



## Conclusie & Gebruik

Door de Langflow JSON te importeren, installeert u direct de volledige pipeline. Het enige wat lokaal geconfigureerd moet worden:

1.  **SURF API Keys:** Voeg uw WILLMA Bearer tokens toe in de API-key velden van elke `Agent (WILLMA SURF)` node.
2.  **Base URL Check:** Verifieer dat de Base URL overeenkomt met de actieve AI-Hub / SURF omgeving (bijv. `https://chat-ai.academiccloud.nl/v1`).
3.  **Afbeeldingen (FIGs):** Plaats de bijbehorende afbeeldingen in de `FIGs/` map binnen dezelfde repository om de documentatie visueel correct weer te geven.

Zodra de flow draait, zal een simpele prompt in de Chat Input de kettingreactie van de 5 agenten triggeren, wat resulteert in een hoogwaardig, gevalideerd Markdown rapport.
