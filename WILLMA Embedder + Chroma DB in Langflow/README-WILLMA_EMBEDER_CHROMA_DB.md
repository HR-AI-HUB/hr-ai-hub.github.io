# README - WILLMA Embedder + Chroma DB in Langflow

## Inleiding

Deze README beschrijft stap voor stap hoe de werkende Langflow is opgebouwd uit het bestand `WILLMa VectorStore RAG CHROMADB +AGENT.json`.

De flow implementeert een eenvoudige Retrieval-Augmented Generation (RAG) pipeline met:

- een document-innamepad voor het lezen en opsplitsen van bestanden
- een custom WILLMA embedding component voor vectorisatie
- een custom Chroma DB component voor opslag en retrieval
- een prompt die de opgehaalde context combineert met de gebruikersvraag
- een WILLMA modelcomponent die het uiteindelijke antwoord genereert

Het doel van deze flow is: een document inlezen, opslaan in Chroma als embeddings, daarna op basis van een gebruikersvraag relevante context ophalen en die context gebruiken om een antwoord te genereren.

## Overzicht van de flow

```text
[Read File] -> [Split Text] -> [Chroma DB] -> [Parser] -> [Prompt.context]
                                 ^
                                 |
                    [WillmaEmbeddings]

[Chat Input] -> [Chroma.search_query]
[Chat Input] -> [Prompt.question]

[Prompt] -> [WillmaModel] -> [Chat Output]
```

## Stap voor stap opbouw van de flow

### Stap 1. Chat Input

De `Chat Input` component ontvangt de vraag van de gebruiker vanuit de Langflow Playground.

In deze flow wordt dezelfde gebruikersvraag naar twee plaatsen gestuurd:

- naar `Prompt.question`
- naar `Chroma.search_query`

Daardoor wordt de vraag niet alleen aan het taalmodel gegeven, maar ook gebruikt om relevante documentfragmenten op te zoeken in de vector store.

Praktisch voorbeeld uit de flow:

- standaard invoer: `What is this document about?`

Rol van deze component:

- startpunt van de vraag-antwoordstroom
- levert de zoekvraag voor retrieval
- levert de uiteindelijke vraag voor de prompt

## Stap 2. Read File

De `Read File` component leest het bronbestand in en geeft de ruwe inhoud door als bericht.

Rol van deze component:

- laadt het document dat geïndexeerd moet worden
- zet de inhoud om naar een formaat dat `Split Text` kan verwerken

Deze component vormt het begin van het ingest-pad.

## Stap 3. Split Text

De `Split Text` component splitst de documentinhoud op in kleinere stukken zodat de tekst geschikt wordt voor embedding en retrieval.

Instellingen uit de werkende flow:

- `chunk_size = 1000`
- `chunk_overlap = 200`
- `separator = "\n"`
- `text_key = "text"`
- `clean_output = false`

Waarom dit nodig is:

- grote documenten zijn ongeschikt om als een enkel blok te embedden
- kleinere chunks verbeteren retrieval
- overlap helpt om context op chunkgrenzen niet te verliezen

## Stap 4. WillmaEmbeddings

De `WillmaEmbeddings` component is een custom embedding component die embeddings opvraagt via de WILLMA SURF API.

Instellingen uit de component:

- model: `Qwen/Qwen3-Embedding-8B`
- base URL: `https://willma.surf.nl/api/v0`
- authenticatie via `X-API-KEY`

Rol van deze component:

- zet tekst om naar numerieke vectoren
- levert een `Embeddings` object aan de Chroma component
- ondersteunt zowel document embeddings als query embeddings

Belangrijk ontwerpbesluit:

Deze component gebruikt een directe `requests.post(...)` call naar de embeddings endpoint in plaats van `OpenAIEmbeddings`. Dat voorkomt het eerdere probleem waarbij token-arrays in plaats van strings naar de WILLMA API werden gestuurd.

### Code van de custom WILLMA embedding component

Bestand: `WiLLMa-Embedder-custom-component.py`

```python
from typing import Any

import requests
from pydantic import SecretStr

from langflow.base.embeddings.model import LCEmbeddingsModel
from langflow.field_typing import Embeddings
from lfx.inputs.inputs import DropdownInput, SecretStrInput, StrInput, IntInput

WILLMA_EMBED_MODELS = [
    "Qwen/Qwen3-Embedding-8B",
]


class WillmaEmbeddingsClient:
    def __init__(self, *, model: str, api_key: str, base_url: str, chunk_size: int) -> None:
        self.model = model
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.chunk_size = max(1, int(chunk_size))

    def _normalize_embedding(self, embedding: Any) -> list[float]:
        if isinstance(embedding, str):
            msg = (
                "WILLMA returned a string instead of a numeric embedding vector. "
                "Verify that the configured model and base URL point to the embeddings API."
            )
            raise TypeError(msg)

        if isinstance(embedding, list):
            normalized: list[float] = []
            for value in embedding:
                if isinstance(value, bool):
                    msg = "WILLMA returned boolean values in the embedding vector."
                    raise TypeError(msg)
                if not isinstance(value, (int, float)):
                    msg = f"WILLMA returned a non-numeric embedding value: {type(value).__name__}."
                    raise TypeError(msg)
                normalized.append(float(value))
            return normalized

        msg = f"WILLMA returned an unsupported embedding payload type: {type(embedding).__name__}."
        raise TypeError(msg)

    def _post_embeddings(self, texts: list[str]) -> list[list[float]]:
        response = requests.post(
            f"{self.base_url}/embeddings",
            headers={
                "X-API-KEY": self.api_key,
                "Content-Type": "application/json",
            },
            json={
                "model": self.model,
                "input": texts,
            },
            timeout=120,
        )

        response.raise_for_status()
        payload = response.json()
        data = payload.get("data")
        if not isinstance(data, list):
            raise TypeError("WILLMA embeddings response did not contain a valid 'data' list.")

        embeddings: list[list[float]] = []
        for item in data:
            if not isinstance(item, dict) or "embedding" not in item:
                raise TypeError("WILLMA embeddings response items must contain an 'embedding' field.")
            embeddings.append(self._normalize_embedding(item["embedding"]))

        return embeddings

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        embeddings: list[list[float]] = []
        for start in range(0, len(texts), self.chunk_size):
            chunk = texts[start : start + self.chunk_size]
            if any(not isinstance(text, str) for text in chunk):
                raise TypeError("WILLMA embeddings input must be a list of strings.")
            embeddings.extend(self._post_embeddings(chunk))
        return embeddings

    def embed_query(self, text: str) -> list[float]:
        if not isinstance(text, str):
            raise TypeError("WILLMA embeddings query input must be a string.")
        embeddings = self._post_embeddings([text])
        if not embeddings:
            raise ValueError("WILLMA embeddings response was empty for the query input.")
        return embeddings[0]


class WillmaEmbeddings(LCEmbeddingsModel):
    display_name = "WILLMA SURF Embeddings"
    description = "Embeddings via WILLMA (SURF) using X-API-KEY. Supports Qwen3-Embedding-8B."
    icon = "Cloud"
    name = "WillmaEmbeddings"

    inputs = [
        DropdownInput(
            name="model_name",
            display_name="Model Name",
            options=WILLMA_EMBED_MODELS,
            value="Qwen/Qwen3-Embedding-8B",
            combobox=True,
        ),
        SecretStrInput(
            name="willma_api_key",
            display_name="WILLMA API Key",
            required=True,
        ),
        StrInput(
            name="base_url",
            display_name="Base URL",
            value="https://willma.surf.nl/api/v0",
            required=True,
        ),
        IntInput(
            name="chunk_size",
            display_name="Chunk Size",
            value=512,
            advanced=True,
        ),
    ]

    def build_embeddings(self) -> Embeddings:
        api_key_value = None
        if self.willma_api_key:
            if isinstance(self.willma_api_key, SecretStr):
                api_key_value = self.willma_api_key.get_secret_value()
            else:
                api_key_value = str(self.willma_api_key)

        if not api_key_value:
            raise ValueError("WILLMA API Key is required.")

        return WillmaEmbeddingsClient(
            model=self.model_name,
            api_key=api_key_value,
            base_url=self.base_url,
            chunk_size=self.chunk_size,
        )
```

## Stap 5. Chroma DB

De `Chroma DB` component is de centrale vector store in deze flow.

Deze component doet twee dingen:

- ingest van documentchunks
- retrieval van relevante chunks op basis van de gebruikersvraag

In de flow krijgt Chroma:

- `ingest_data` van `Split Text`
- `embedding` van `WillmaEmbeddings`
- `search_query` van `Chat Input`

Rol van deze component:

- slaat documentchunks op in een Chroma collectie
- maakt embeddings voor de chunks via de custom WILLMA embedder
- gebruikt dezelfde embedder om de zoekvraag te embedden
- haalt relevante records op voor de promptcontext

Belangrijke beveiliging in deze custom versie:

- controleert of de embedding echt een `list[float]` teruggeeft
- filtert complexe metadata voordat documenten aan Chroma worden toegevoegd
- voorkomt duplicaten als `allow_duplicates` uit staat

### Code van de custom Chroma component

Bestand: `Chroma-DB-custom-component.py`

```python
from copy import deepcopy
from typing import TYPE_CHECKING

from chromadb.config import Settings
from langchain_chroma import Chroma
from typing_extensions import override

from lfx.base.vectorstores.chroma_security import chroma_langchain_collection_kwargs
from lfx.base.vectorstores.model import LCVectorStoreComponent, check_cached_vector_store
from lfx.base.vectorstores.utils import chroma_collection_to_data
from lfx.inputs.inputs import BoolInput, DropdownInput, HandleInput, IntInput, StrInput
from lfx.schema.data import Data

if TYPE_CHECKING:
    from lfx.schema.dataframe import DataFrame


class ChromaVectorStoreComponent(LCVectorStoreComponent):
    display_name: str = "Chroma DB"
    description: str = "Chroma Vector Store with search capabilities"
    name = "Chroma"
    icon = "Chroma"

    inputs = [
        StrInput(name="collection_name", display_name="Collection Name", value="langflow"),
        StrInput(name="persist_directory", display_name="Persist Directory"),
        *LCVectorStoreComponent.inputs,
        HandleInput(name="embedding", display_name="Embedding", input_types=["Embeddings"]),
        StrInput(name="chroma_server_cors_allow_origins", display_name="Server CORS Allow Origins", advanced=True),
        StrInput(name="chroma_server_host", display_name="Server Host", advanced=True),
        IntInput(name="chroma_server_http_port", display_name="Server HTTP Port", advanced=True),
        IntInput(name="chroma_server_grpc_port", display_name="Server gRPC Port", advanced=True),
        BoolInput(name="chroma_server_ssl_enabled", display_name="Server SSL Enabled", advanced=True),
        BoolInput(
            name="allow_duplicates",
            display_name="Allow Duplicates",
            advanced=True,
            info="If false, will not add documents that are already in the Vector Store.",
        ),
        DropdownInput(
            name="search_type",
            display_name="Search Type",
            options=["Similarity", "MMR"],
            value="Similarity",
            advanced=True,
        ),
        IntInput(
            name="number_of_results",
            display_name="Number of Results",
            advanced=True,
            value=10,
        ),
        IntInput(
            name="limit",
            display_name="Limit",
            advanced=True,
        ),
    ]

    @override
    @check_cached_vector_store
    def build_vector_store(self) -> Chroma:
        try:
            from chromadb import Client
            from langchain_chroma import Chroma
        except ImportError as e:
            raise ImportError(
                "Could not import Chroma integration package. Please install it with `pip install langchain-chroma`."
            ) from e

        chroma_settings = None
        client = None
        if self.chroma_server_host:
            chroma_settings = Settings(
                chroma_server_cors_allow_origins=self.chroma_server_cors_allow_origins or [],
                chroma_server_host=self.chroma_server_host,
                chroma_server_http_port=self.chroma_server_http_port or None,
                chroma_server_grpc_port=self.chroma_server_grpc_port or None,
                chroma_server_ssl_enabled=self.chroma_server_ssl_enabled,
            )
            client = Client(settings=chroma_settings)

        persist_directory = self.resolve_path(self.persist_directory) if self.persist_directory is not None else None

        chroma = Chroma(
            persist_directory=persist_directory,
            client=client,
            embedding_function=self.embedding,
            collection_name=self.collection_name,
            **chroma_langchain_collection_kwargs(),
        )

        self._add_documents_to_vector_store(chroma)
        limit = int(self.limit) if self.limit is not None and str(self.limit).strip() else None
        self.status = chroma_collection_to_data(chroma.get(limit=limit))
        return chroma

    def _add_documents_to_vector_store(self, vector_store: "Chroma") -> None:
        ingest_data: list | Data | DataFrame = self.ingest_data
        if not ingest_data:
            self.status = ""
            return

        ingest_data = self._prepare_ingest_data()

        stored_documents_without_id = []
        if self.allow_duplicates:
            stored_data = []
        else:
            limit = int(self.limit) if self.limit is not None and str(self.limit).strip() else None
            stored_data = chroma_collection_to_data(vector_store.get(limit=limit))
            for value in deepcopy(stored_data):
                del value.id
                stored_documents_without_id.append(value)

        documents = []
        for _input in ingest_data or []:
            if isinstance(_input, Data):
                if _input not in stored_documents_without_id:
                    documents.append(_input.to_lc_document())
            else:
                raise TypeError("Vector Store Inputs must be Data objects.")

        if documents and self.embedding is not None:
            sample_text = documents[0].page_content if documents[0].page_content else ""
            sample_embedding = self.embedding.embed_query(sample_text)
            if not isinstance(sample_embedding, list) or any(not isinstance(value, float) for value in sample_embedding):
                sample_type = type(sample_embedding).__name__
                raise TypeError(
                    "Embedding component must return a list of floats for ChromaDB. "
                    f"Received {sample_type} from the configured embedding model."
                )

            try:
                from langchain_community.vectorstores.utils import filter_complex_metadata

                filtered_documents = filter_complex_metadata(documents)
                vector_store.add_documents(filtered_documents)
            except ImportError:
                vector_store.add_documents(documents)
```

## Stap 6. Parser

De `Parser` component zet de output van Chroma om naar platte tekst die in de prompt kan worden gebruikt.

Rol van deze component:

- neemt de tabel- of data-output van Chroma
- extraheert de relevante tekst
- levert die tekst aan `Prompt.context`

Zonder deze stap krijgt het promptcomponent geen bruikbare contextstring.

## Stap 7. Prompt Template

De `Prompt Template` component combineert de opgehaalde context met de vraag van de gebruiker.

Variabelen in deze flow:

- `context`
- `question`

Template uit de werkende flow:

```text
{context}

---

Given the context above, answer the question as best as possible.

Question: {question}

Answer:
```

Rol van deze component:

- dwingt het model om eerst naar de opgehaalde context te kijken
- combineert retrieval en vraag in een enkel promptbericht
- vormt de brug tussen RAG en generatie

## Stap 8. WillmaModel

De `WillmaModel` component ontvangt de samengestelde prompt en genereert het antwoord.

Rol van deze component:

- gebruikt de prompt met context en vraag
- produceert een tekstueel antwoord
- stuurt dat antwoord door naar `Chat Output`

Deze component is het generatieve deel van de flow.

### Code van de custom WILLMA model component

Bestand: `WiLLMa-Model-custom-component.py`

```python
from typing import Any
from langchain_openai import ChatOpenAI
from pydantic.v1 import SecretStr

from lfx.base.models.model import LCModelComponent
from lfx.field_typing import LanguageModel
from lfx.field_typing.range_spec import RangeSpec
from lfx.inputs.inputs import BoolInput, DictInput, DropdownInput, IntInput, SecretStrInput, SliderInput, StrInput
from lfx.log.logger import logger


class WillmaModel(LCModelComponent):
    display_name = "WILLMA SURF Model"
    description = "Custom component for WILLMA (SURF) with X-API-KEY support."
    icon = "Cloud"
    name = "WillmaModel"

    inputs = [
        *LCModelComponent.get_base_inputs(),
        DropdownInput(
            name="model_name",
            display_name="Model Name",
            options=[
                "Qwen 2.5 VL 32B Instruct AWQ",
                "Qwen 2.5 Coder 32B Instruct AWQ",
                "mistralai/Mistral-Small-3.2-24B-Instruct-2506",
                "openai/gpt-oss-120b",
                "default-text-large"
            ],
            value="Qwen 2.5 Coder 32B Instruct AWQ",
            combobox=True,
        ),
        SecretStrInput(
            name="willma_api_key",
            display_name="WILLMA API Key",
            info="Enter your SURF WILLMA API Key (starts with 7769...).",
            required=True,
        ),
        StrInput(
            name="base_url",
            display_name="Base URL",
            value="https://willma.surf.nl/api/v0",
            required=True,
        ),
        SliderInput(
            name="temperature",
            display_name="Temperature",
            value=0.1,
            range_spec=RangeSpec(min=0, max=1, step=0.01),
        ),
        IntInput(
            name="max_tokens",
            display_name="Max Tokens",
            value=2048,
            advanced=True,
        ),
        BoolInput(
            name="stream",
            display_name="Stream",
            value=False,
            advanced=True,
        ),
        DictInput(
            name="model_kwargs",
            display_name="Model Kwargs",
            advanced=True,
            info="Additional keyword arguments.",
        ),
    ]

    def build_model(self) -> LanguageModel:
        api_key_value = None
        if self.willma_api_key:
            if isinstance(self.willma_api_key, SecretStr):
                api_key_value = self.willma_api_key.get_secret_value()
            else:
                api_key_value = str(self.willma_api_key)

        custom_headers = {
            "X-API-KEY": api_key_value,
            "Content-Type": "application/json"
        }

        model_kwargs = self.model_kwargs or {}

        parameters = {
            "model": self.model_name,
            "openai_api_key": api_key_value,
            "openai_api_base": self.base_url,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "streaming": self.stream,
            "default_headers": custom_headers,
            "model_kwargs": model_kwargs,
        }

        return ChatOpenAI(**parameters)

    def update_build_config(self, build_config: dict, field_value: Any, field_name: str | None = None) -> dict:
        if "system_message" not in build_config:
            build_config["system_message"] = {"show": False, "value": ""}
        if "input_value" not in build_config:
            build_config["input_value"] = {"show": False, "value": ""}
        return build_config
```

### Wat deze modelcomponent precies doet

Deze custom modelcomponent gebruikt `ChatOpenAI` als compatibiliteitslaag, maar stuurt de requests naar de WILLMA SURF endpoint via:

- `openai_api_base = https://willma.surf.nl/api/v0`
- custom header `X-API-KEY`

Dat betekent dat de component zich voor Langflow en LangChain gedraagt als een standaard chatmodel, terwijl de authenticatie en endpoint-routing aangepast zijn voor WILLMA.

Belangrijke punten in deze implementatie:

- de API key wordt veilig uit `SecretStr` gehaald
- de WILLMA authenticatie gebeurt via `default_headers`
- temperatuur, max tokens, streaming en extra kwargs zijn configureerbaar
- `update_build_config()` voegt intern `system_message` en `input_value` toe zodat agent-achtige componenten geen build errors geven

Hiermee is `WillmaModel` het generatieve eindpunt van de flow: de prompt uit de `Prompt Template` wordt naar WILLMA gestuurd en het antwoord komt terug als `text_output`.

## Stap 9. Chat Output

De `Chat Output` component toont het antwoord in de Langflow Playground.

Rol van deze component:

- presenteert het modelantwoord aan de gebruiker
- kan het antwoord opslaan in de chatgeschiedenis

## Hoe de volledige flow werkt

### Ingest-fase

1. `Read File` leest het document.
2. `Split Text` verdeelt het document in chunks.
3. `WillmaEmbeddings` maakt embeddings voor die chunks.
4. `Chroma DB` slaat de chunks en embeddings op in de collectie.

### Vraag-fase

1. `Chat Input` ontvangt de gebruikersvraag.
2. De vraag gaat naar `Chroma.search_query`.
3. `Chroma DB` zoekt relevante chunks op.
4. `Parser` zet de gevonden resultaten om naar tekst.
5. Die tekst gaat naar `Prompt.context`.
6. Dezelfde gebruikersvraag gaat naar `Prompt.question`.
7. `Prompt Template` bouwt de definitieve prompt.
8. `WillmaModel` genereert het antwoord.
9. `Chat Output` toont het antwoord.

## Waarom deze flow werkt

Deze flow werkt omdat de drie noodzakelijke RAG-verbindingen aanwezig zijn:

- documentinhoud gaat naar `Chroma.ingest_data`
- gebruikersvraag gaat naar `Chroma.search_query`
- opgehaalde context gaat naar `Prompt.context`

Als een van deze verbindingen ontbreekt, krijg je meestal generieke antwoorden zoals dat het model het document niet kan zien of dat er geen context beschikbaar is.

## Belangrijkste aandachtspunten

### 1. Embeddings moeten strings ontvangen

De WILLMA embeddings endpoint verwacht ruwe tekststrings. Daarom gebruikt de custom embedder directe HTTP-calls met:

```json
{
  "model": "Qwen/Qwen3-Embedding-8B",
  "input": ["tekst chunk 1", "tekst chunk 2"]
}
```

### 2. Chroma verwacht `list[float]`

De custom Chroma component valideert expliciet dat de embedding output een lijst van floats is.

### 3. Promptcontext moet echt gevuld worden

De parser-output moet verbonden zijn met `Prompt.context`. Zonder die verbinding is er geen echte RAG-context in de prompt.

## Bestanden die bij deze flow horen

- `WORKING_FLOW/WILLMa VectorStore RAG CHROMADB +AGENT.json`
- `WiLLMa-Embedder-custom-component.py`
- `Chroma-DB-custom-component.py`
- `WiLLMa-Model-custom-component.py`

## Samenvatting

Deze Langflow is een werkende RAG-opzet waarin:

- documenten worden ingelezen en opgesplitst
- chunks via WILLMA embeddings worden gevectoriseerd
- Chroma de vector store en retrieval verzorgt
- de opgehaalde context in een prompt wordt geplaatst
- het WILLMA model een antwoord genereert op basis van die context

De twee belangrijkste custom onderdelen zijn de WILLMA embedding component en de Chroma DB component. Samen lossen ze de integratie op tussen de SURF WILLMA embeddings API en ChromaDB binnen Langflow.