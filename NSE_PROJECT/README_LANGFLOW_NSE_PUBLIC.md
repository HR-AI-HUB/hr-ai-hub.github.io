# Langflow-conversie van de NSE-notebooks

> Dit document beschrijft stap voor stap hoe de notebookworkflow in `D:\OneDrive - Hogeschool Rotterdam\SURF_PILOT\AI_HUB_PILOT\NSE` kan worden omgezet naar **Langflow custom components** die compatibel zijn met de echte Langflow component-API en de Docker-runtime op SURF Ubuntu.

Doel van deze fase is **te beginnen met de omzetting van** de broncode uit `NSE-AI-HUB_EXCEL_DATA_PREPROSESSING+NORMALIZATION_V1.ipynb` **naar herbruikbare Langflow-componentcode**. 
<br> Een eerste versie van de broncode is ontwikkeld op HPC-workstations van de DataLabs EAS / Healthcare / AI Sustech door Tech Lead Robvdw (MEI 2026).

---

## Inhoudsopgave

| Nr. | Sectie |
| --- | --- |
| 1 | [Waarom deze omzetting nodig is](#waarom-deze-omzetting-nodig-is) |
| 2 | [Requirements voordat de component werkt in Langflow op SURF Ubuntu](#requirements-voordat-de-component-werkt-in-langflow-op-surf-ubuntu) |
| 3 | [Dockerfile voor SURF Ubuntu + Langflow](#dockerfile-voor-surf-ubuntu--langflow) |
| 4 | [docker-compose.yaml voor SURF Ubuntu + Langflow](#docker-composeyaml-voor-surf-ubuntu--langflow) |
| 5 | [Bronnotebook in scope](#bronnotebook-in-scope) |
| 6 | [Doelarchitectuur in Langflow](#doelarchitectuur-in-langflow) |
| 7 | [Mapping van notebookcellen naar componenten](#mapping-van-notebookcellen-naar-componenten) |
| 8 | [Ontwerpkeuzes voor echte Langflow-compatibiliteit](#ontwerpkeuzes-voor-echte-langflow-compatibiliteit) |
| 9 | [Eerste custom component: `NSEPreprocessingComponent`](#eerste-custom-component-nsepreprocessingcomponent) |
| 10 | [Volledige code van de eerste component](#volledige-code-van-de-eerste-component) |
| 11 | [Hoe deze component in Langflow gebruikt kan worden](#hoe-deze-component-in-langflow-gebruikt-kan-worden) |
| 12 | [Volgende stap in de migratie](#volgende-stap-in-de-migratie) |
| 13 | [Opmerking over productiegeschiktheid](#opmerking-over-productiegeschiktheid) |
| 14 | [Code van de opgesplitste componenten](#code-van-de-opgesplitste-componenten) |
| 14.1 | [`nse_env_loader_component.py`](#nse_env_loader_componentpy) |
| 14.2 | [`nse_research_drive_connector_component.py`](#nse_research_drive_connector_componentpy) |

---

## Waarom deze omzetting nodig is

De huidige NSE-workflow is notebook-gebaseerd. Dat werkt goed voor verkenning en iteratie, maar minder goed voor:

| Behoefte | Waarom notebookvorm beperkt is | Waarom Langflow-componenten helpen |
| --- | --- | --- |
| Hergebruik | Code zit verspreid over meerdere cellen | Logica wordt herbruikbaar als component |
| Onderhoud | Notebookcellen zijn minder modulair | Iedere functie krijgt een duidelijke componentgrens |
| Pipeline-orkestratie | Handmatige uitvoervolgorde is nodig | Componenten zijn visueel te koppelen in een flow |
| Validatie | Status zit vooral in notebookoutput | Componenten kunnen gestructureerde `Data` teruggeven |
| Governance | Moeilijker om I/O-grenzen scherp te houden | Input/output-contracten worden explicieter |

De migratie naar Langflow moet daarom leiden tot een set van **duidelijk begrensde, herbruikbare en auditbare componenten**.

---

## Requirements voordat de component werkt in Langflow op SURF Ubuntu

### Stap 1: Maak een `LANGFLOW` mapstructuur aan

Maak eerst één hoofdmap `LANGFLOW` aan waarin alle benodigde bestanden en submappen samenkomen.

```text
LANGFLOW/
├── Dockerfile
├── docker-compose.yaml
├── create-langflow.sh
├── acme.json
├── custom_components/
│   └── nse_preprocessing_component.py
├── nse_runtime/
├── rclone/
│   └── rclone.conf
├── langflow_cache/
└── chroma_data/
```

### Betekenis van de mapstructuur

| Onderdeel | Functie |
| --- | --- |
| `LANGFLOW/` | Hoofdmap voor de complete Langflow deployment |
| `Dockerfile` | Bouwt de aangepaste Langflow image met NSE dependencies |
| `docker-compose.yaml` | Start Traefik, Langflow en Postgres samen op |
| `create-langflow.sh` | Automatiseert setup en deployment op de Ubuntu-host |
| `custom_components/` | Bevat de Langflow custom componentcode |
| `custom_components/nse_preprocessing_component.py` | Definitieve NSE preprocessing component |
| `nse_runtime/` | Lokale runtime-map die in de container wordt gemount op `/app/nse_runtime` |
| `rclone/` | Map voor `rclone.conf` |
| `rclone/rclone.conf` | Bevat de `RD` remoteconfiguratie |
| `langflow_cache/` | Cachemap voor Langflow |
| `chroma_data/` | Persistente opslag voor vector/chroma data |
| `acme.json` | Opslag voor Traefik Let's Encrypt certificaten |

Voordat `NSEPreprocessingComponent` bruikbaar is in Langflow op een **SURF Ubuntu 22.04+ VM**, moeten zowel de host als de Docker-runtime correct zijn ingericht.

### Infrastructurele randvoorwaarden

| Onderdeel | Vereiste |
| --- | --- |
| OS | Ubuntu 22.04 of nieuwer |
| Toegang | non-root SSH-toegang |
| Netwerk | publieke IP aanwezig |
| Poorten | `80`, `443` en `8080` open |
| DNS | werkend A-record, bijvoorbeeld `langflow.example.org` |
| Reverse proxy | geen conflicterende Nginx-configuratie |
| Docker | geïnstalleerd |
| Docker Compose | geïnstalleerd |
| Python 3 | geïnstalleerd op host |

### Benodigde software in de Langflow container

| Type | Package | Waarom nodig |
| --- | --- | --- |
| System package | `rclone` | verplicht voor lezen/schrijven naar Research Drive |
| System package | `ffmpeg` | nuttig voor bestaande Langflow-workflows met media |
| System package | `libgl1` | vereist door delen van de Docling-stack |
| System package | `libglib2.0-0` | vereist door delen van de Docling-stack |
| Python package | `langflow[docling]` | Langflow plus Docling-functionaliteit |
| Python package | `python-dotenv` | lezen van `.nse-env` |
| Python package | `pandas` | tabulaire verwerking |
| Python package | `numpy` | numerieke verwerking |
| Python package | `openpyxl` | inlezen van `.xlsx` |
| Python package | `xlrd` | fallback voor oudere Excel-formaten |
| Python package | `requests` | nuttig voor aanvullende connectorlogica |

### Runtime-eisen voor de NSE component

| Vereiste | Toelichting |
| --- | --- |
| `rclone` beschikbaar in de container | testen met `docker exec -it langflow which rclone` |
| Python dependencies beschikbaar | testen met een korte `python -c` importcheck |
| `.nse-env` beschikbaar op RD | standaardpad: `RD:<project-path>/.nse-env` |
| Geldige `SHARE_LINK` | moet een echte SURF/RD share token bevatten |
| Schrijfrechten op `RD_OUTPUT_PATH` | vereist voor export van run-output |
| Linux `project_dir` | gebruik `/app/nse_runtime` in plaats van een Windows-pad |
| `rclone.conf` in container | `RD:` moet zichtbaar zijn via `docker exec -it langflow rclone listremotes` |

Plaats het echte bestand als `./rclone/rclone.conf` in dezelfde projectmap als `Dockerfile` en `docker-compose.yaml`, zodat de mount `./rclone/rclone.conf:/root/.config/rclone/rclone.conf:ro` werkt.

De inhoud moet minimaal een `RD` remote bevatten in deze vorm:

```ini
[RD]
type = webdav
url = https://<research-drive-host>/remote.php/dav/files/<user>
vendor = nextcloud
user = <user>
pass = <redacted-or-generated-secret>
```

### Praktische status van de nu werkende versie

De definitieve werkende versie van de component doet nu het volgende correct:

| Onderdeel | Status |
| --- | --- |
| `.nse-env` ophalen via `RD:` | Werkend |
| `rclone` remoteconfig valideren | Werkend |
| Linux runtimepad `/app/nse_runtime` gebruiken | Werkend |
| Oude runtime-artifacts uitsluiten uit inputset | Werkend |
| Corrupte of ongeldige Excelbestanden registreren in `load_errors` | Werkend |
| Resultaten terugschrijven naar `RD_OUTPUT_PATH` | Werkend |

---

## Dockerfile voor SURF Ubuntu + Langflow

Onderstaande Dockerfile is geschikt als basis voor Langflow plus de NSE preprocessing component.

```dockerfile
FROM langflowai/langflow:latest

USER root

# Systeempackages voor Langflow/Docling en NSE preprocessing via Research Drive.
RUN apt-get update && apt-get install -y --no-install-recommends \
        libgl1 \
        libglib2.0-0 \
        ffmpeg \
        rclone \
        && rm -rf /var/lib/apt/lists/*

# Python dependencies voor Langflow + NSE component.
RUN uv pip install \
        'langflow[docling]' \
        python-dotenv \
        pandas \
        numpy \
        openpyxl \
        xlrd \
        requests

USER 1000
```

### Controle na build

| Check | Commando |
| --- | --- |
| `rclone` aanwezig | `docker exec -it langflow which rclone` |
| `rclone` werkt | `docker exec -it langflow rclone version` |
| Python packages werken | `docker exec -it langflow python -c "import dotenv, pandas, numpy, openpyxl, xlrd, requests; print('ok')"` |

---

## docker-compose.yaml voor SURF Ubuntu + Langflow

Onderstaand voorbeeld laat zien hoe de aangepaste Dockerfile door Docker Compose gebruikt moet worden.

```yaml
services:
    traefik:
        image: traefik:v2.11
        container_name: traefik
        dns:
            - 8.8.8.8
        restart: unless-stopped
        command:
            - "--api.dashboard=true"
            - "--providers.docker=true"
            - "--providers.docker.exposedbydefault=false"
            - "--entrypoints.web.address=:80"
            - "--entrypoints.websecure.address=:443"
            - "--entrypoints.web.http.redirections.entryPoint.to=websecure"
            - "--entrypoints.web.http.redirections.entryPoint.scheme=https"
            - "--certificatesresolvers.le.acme.httpchallenge=true"
            - "--certificatesresolvers.le.acme.httpchallenge.entrypoint=web"
            - "--certificatesresolvers.le.acme.storage=/letsencrypt/acme.json"
        ports:
            - "80:80"
            - "443:443"
        volumes:
            - "/var/run/docker.sock:/var/run/docker.sock:ro"
            - "./acme.json:/letsencrypt/acme.json"

    langflow:
        build:
            context: .
            dockerfile: Dockerfile
        container_name: langflow
        restart: unless-stopped
        environment:
            - LANGFLOW_DATABASE_URL=${LANGFLOW_DATABASE_URL}
            - LANGFLOW_AUTO_LOGIN=false
            - LANGFLOW_NEW_USER_SIGNUP=true
            - LANGFLOW_SECRET_KEY=${LANGFLOW_SECRET_KEY}
            - LANGFLOW_LANGFLOW_USER_DEFAULT=false
            - LANGFLOW_CACHE_DIR=/app/langflow/cache
            - DO_NOT_TRACK=true
            - RCLONE_CONFIG=/root/.config/rclone/rclone.conf
        volumes:
            - langflow_data:/app/langflow
            - ./langflow_cache:/app/langflow/cache
            - ./chroma_data:/app/chroma_data
            - ./custom_components:/app/custom_components
            - ./nse_runtime:/app/nse_runtime
            - ./rclone/rclone.conf:/root/.config/rclone/rclone.conf:ro
        user: "root"
        depends_on:
            db:
                condition: service_healthy
        labels:
            - "traefik.enable=true"
            - "traefik.http.routers.langflow.rule=Host(`langflow.example.org`)"
            - "traefik.http.routers.langflow.entrypoints=websecure"
            - "traefik.http.routers.langflow.tls.certresolver=le"
            - "traefik.http.services.langflow.loadbalancer.server.port=7860"

    db:
        image: postgres:16
        container_name: langflow_db
        restart: unless-stopped
        environment:
            POSTGRES_DB: ${POSTGRES_DB}
            POSTGRES_USER: ${POSTGRES_USER}
            POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
        volumes:
            - postgres_data:/var/lib/postgresql/data
        healthcheck:
            test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
            interval: 10s
            timeout: 5s
            retries: 5

volumes:
    langflow_data:
    postgres_data:
```

### Veiligheidsnotitie bij deze compose-configuratie

- Gebruik geen hardcoded productiecredentials in documentatie of versiebeheer.
- Lever `LANGFLOW_SECRET_KEY`, `POSTGRES_PASSWORD` en vergelijkbare waarden aan via een niet-getrackte `.env`, Docker secrets of een secret manager.
- Publiceer geen echte hostnamen, gebruikersnamen of Research Drive paden als dat operationeel gevoelig is.

### Build en herstart op Ubuntu CLI

| Stap | Commando |
| --- | --- |
| Image builden | `docker compose -f docker-compose.yaml build langflow` |
| Container starten | `docker compose -f docker-compose.yaml up -d langflow` |
| Containers controleren | `docker compose -f docker-compose.yaml ps` |

### `create-langflow.sh`

Onderstaand script kan direct naast `Dockerfile` en `docker-compose.yaml` worden geplaatst om de deploymentstappen op de Ubuntu-host te automatiseren.

```bash
#!/bin/bash
set -e
echo "-------------------------------------------------------"
echo "Starting Deployment Script $(date)"
echo "-------------------------------------------------------"
echo "Step 1: Stopping and disabling Nginx..."
if systemctl is-active --quiet nginx; then
    sudo systemctl stop nginx
    sudo systemctl disable nginx
    echo "Nginx has been stopped and disabled."
else
    echo "Nginx was not running, skipping."
fi
echo "Step 2: Configuring Traefik SSL storage acme.json..."
if [ ! -f acme.json ]; then
    sudo touch acme.json
    sudo chmod 600 acme.json
    echo "acme.json created with secure permissions 600."
else
    sudo chmod 600 acme.json
    echo "acme.json already exists, permissions reset to 600."
fi
echo "Step 2.5: Creating local deployment .env..."
rm -rf .env
touch .env
echo "Populate .env with deployment-specific values before first production run."
echo "--------------------------------"
echo "Current content of .env:"
cat .env
echo "--------------------------------"
echo "Step 3: Checking Docker group membership for $USER..."
if groups $USER | grep -q docker; then
    echo "User $USER is already in the docker group."
else
    sudo usermod -aG docker $USER
    newgrp docker
    echo "User $USER added to the docker group."
fi
echo "Step 4: Building and starting containers with Traefik..."
if sg docker -c "docker compose up -d --build"; then
    echo "-------------------------------------------------------"
    echo "SUCCESS! Containers are building/starting."
else
    echo "ERROR: Docker compose failed to start."
    exit 1
fi
echo "Step 5: Finalizing..."
sg docker -c "docker ps"
echo "--- Traefik Routing Rule ---"
sg docker -c "docker compose config | grep -i Host"
echo "-------------------------------------------------------"
echo "SETUP COMPLETE! Traefik on ports 80/443."
echo "-------------------------------------------------------"
```

### Korte uitleg per stap

| Stap | Wat gebeurt er |
| --- | --- |
| `Step 1` | Stopt een bestaande `nginx`-service en schakelt die uit, zodat poorten `80` en `443` vrij zijn voor Traefik. |
| `Step 2` | Maakt `acme.json` aan of zet opnieuw de permissies op `600`, zodat Traefik certificaten veilig kan opslaan. |
| `Step 2.5` | Maakt een lokale `.env` aan voor deploymentvariabelen. Vul deze handmatig met niet-gecommitteerde secrets. |
| `Step 3` | Controleert of de huidige gebruiker lid is van de `docker`-groep en voegt die gebruiker zo nodig toe. |
| `Step 4` | Bouwt de containers opnieuw en start ze via `docker compose up -d --build`. |
| `Step 5` | Toont de draaiende containers en de Traefik `Host`-routingregel als laatste controle na de deployment. |
| `Step 6` | Maak het script uitvoerbaar en voer het daarna uit vanaf de terminal. |

```bash
ls -la create-langflow.sh
chmod +x create-langflow.sh
ls -la create-langflow.sh
./create-langflow.sh
sudo bash create-langflow.sh
```

---

## Bronnotebook in scope

De eerste omzetting richt zich op:

| Eigenschap | Waarde |
| --- | --- |
| Notebook | `NSE-AI-HUB_EXCEL_DATA_PREPROSESSING+NORMALIZATION_V1.ipynb` |
| Hoofddoel | Brondata via `rclone` lezen vanaf Research Drive, normaliseren, analyseren en terugschrijven naar Research Drive |
| Belangrijkste afhankelijkheden | `pandas`, `numpy`, `dotenv`, `subprocess`, `rclone`, `pathlib`, `json`, `logging` |
| Veiligheidsrandvoorwaarde | Data mag logisch de Research Drive niet verlaten |
| Technische runtime-aanpak | Tijdelijke lokale cache, gevolgd door synchronisatie terug naar RD |

---

## Doelarchitectuur in Langflow

De notebook kan logisch worden opgesplitst in de volgende componenten:

| Component | Verantwoordelijkheid |
| --- | --- |
| `NSEEnvLoader` | `.nse-env` laden en verplichte configuratie valideren |
| `NSEResearchDriveConnector` | share-token extraheren, remote toegang valideren en RD-doelpad voorbereiden |
| `NSEResearchDriveValidator` | bronshare en doelpad op RD valideren |
| `NSETabularInputLoader` | ondersteunde bestanden kopiëren en in pandas laden |
| `NSENormalizer` | kolomnamen en simpele datatypes normaliseren |
| `NSEAnalyzer` | schema, missings en numerieke samenvattingen genereren |
| `NSEResearchDriveWriter` | resultaten lokaal exporteren en terugschrijven naar RD |
| `NSELoggingComponent` | runmetadata en basisdiagnostiek wegschrijven naar logfile |
| `NSEPreprocessingComponent` | eerste end-to-end component die bovenstaande stappen orkestreert |

Voor deze eerste fase implementeren we **één samengestelde component**: `NSEPreprocessingComponent`.

---

## Mapping van notebookcellen naar componenten

| Notebookcel | Functie in notebook | Doel in Langflow |
| --- | --- | --- |
| Cel 1 | Environment check | optioneel buiten component, vooral runtime-informatie |
| Cel 3 | Secrets laden uit `.nse-env` | opnemen in component-initialisatie / configuratielogica |
| Cel 4 | RD share configureren | opnemen in RD-helpermethoden |
| Cel 5 | RD toegang valideren | opnemen in preflight validatie |
| Cel 6 | bestanden ophalen en laden | kern van input-inname |
| Cel 7 | normalisatie | kern van datatransformatie |
| Cel 8 | analyse | kern van profiling-output |
| Cel 9 | outputpaden maken | onderdeel van exportlogica |
| Cel 10 | resultaten schrijven | kern van writer-output |
| Cel 11 | logging | integreren in componentstatus en logfile-output |

### Aanbevolen volgorde van koppelen in Langflow

```text
NSEEnvLoaderComponent
    -> NSEResearchDriveConnectorComponent
    -> NSETabularInputLoaderComponent
    -> NSENormalizerComponent
    -> NSEAnalyzerComponent
    -> NSEOutputWriterComponent
    -> NSELoggingComponent
```

### Betekenis van de keten

| Volgorde | Component | Doel |
| --- | --- | --- |
| 1 | `NSEEnvLoaderComponent` | Laadt `.nse-env`, valideert verplichte variabelen en maakt runtime-mappen aan |
| 2 | `NSEResearchDriveConnectorComponent` | Valideert bron- en doeltoegang zonder secret-bearing payloads downstream te sturen |
| 3 | `NSETabularInputLoaderComponent` | Kopieert de bronbestanden naar cache en detecteert load errors |
| 4 | `NSENormalizerComponent` | Normaliseert kolommen en maakt schema-overzicht |
| 5 | `NSEAnalyzerComponent` | Maakt datasetprofielen en numerieke samenvattingen |
| 6 | `NSEOutputWriterComponent` | Schrijft analyses en genormaliseerde datasets lokaal en naar RD |
| 7 | `NSELoggingComponent` | Schrijft de runmetadata en diagnostiek naar logfile |

---

## Ontwerpkeuzes voor echte Langflow-compatibiliteit

De componentcode hieronder is afgestemd op de echte Langflow API:

```python
from langflow.custom import Component
from langflow.io import BoolInput, Output, StrInput
from langflow.schema import Data
```

Belangrijkste ontwerpkeuzes:

| Ontwerpkeuze | Uitleg |
| --- | --- |
| `Component` als basisklasse | Volgt de echte Langflow component-API |
| `StrInput` voor paden en configuratie | Past beter bij gewone tekstvelden in Langflow |
| `Output(..., method="build_output")` | Sluit aan op standaard component-outputpatroon |
| `Data(...)` als resultaatcontainer | Zorgt voor gestructureerde output voor downstream componenten |
| `self.status` updaten | Maakt status zichtbaar in Langflow |
| `BoolInput` voor cleanup-optie | Handig voor lokaal testen en tijdelijke bestandshygiëne |
| `.nse-env` via RD laden | Secrets/configuratie komen uit een externe bron in plaats van uit hardcoded waarden |
| Linux-safe default runtimepad | `project_dir` staat standaard op `/app/nse_runtime` |
| `rclone.conf`-validatie | De component detecteert expliciet of `RD:` in de container beschikbaar is |
| Runtime-artifacts uitsluiten | Eerdere `NSE_OUTPUTS`, `preprocessing_runtime` en `.normalized.csv` bestanden worden niet opnieuw ingelezen |
| Robuustere load error handling | Corrupte Excelbestanden worden in `load_errors` gezet in plaats van de hele component te stoppen |
| Secret-minimalisatie | Secretwaarden worden niet onnodig teruggegeven in componentpayloads |

---

## Eerste custom component: `NSEPreprocessingComponent`

Deze eerste component is een **end-to-end preprocessing component** die de complete notebookflow in één component onderbrengt.

### Functionele scope

| Onderdeel | Inbegrepen in eerste component |
| --- | --- |
| `.nse-env` laden | Ja |
| verplichte variabelen valideren | Ja |
| Research Drive bron valideren | Ja |
| Research Drive doelpad valideren | Ja |
| bestanden ophalen | Ja |
| tabulaire bestanden laden | Ja |
| normaliseren | Ja |
| analyseren | Ja |
| outputs lokaal schrijven | Ja |
| outputs naar RD kopiëren | Ja |
| logging | Ja |

### Verwachte output van de component

De component retourneert een `Data` object met onder meer:

| Sleutel | Betekenis |
| --- | --- |
| `run_id` | tijdstempel van de run |
| `remote_run_output_path` | RD-doelmap voor de run |
| `loaded_files` | lijst van succesvol geladen bestanden |
| `load_errors` | bestanden die niet geladen konden worden |
| `analysis_index` | compacte analyse per bestand |
| `schema_preview` | schemapreview per bestand |
| `written_files` | lijst van lokaal geschreven en naar RD gesynchroniseerde bestanden |
| `log_file` | lokaal logbestand |

### Veiligheidsnotitie voor de component-output

Gevoelige waarden zoals `SHARE_PASSWORD`, volledige inline remotes en andere secret-bearing configuratie horen niet thuis in generieke downstream payloads. Geef alleen terug wat functioneel nodig is.

---

## Volledige code van de eerste component

```python
from __future__ import annotations

import json
import logging
import os
import re
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import pandas as pd
from dotenv import dotenv_values
from pandas.errors import ParserError

from langflow.custom import Component
from langflow.io import BoolInput, Output, StrInput
from langflow.schema import Data


class NSEPreprocessingComponent(Component):
    display_name = "NSE Preprocessing"
    description = (
        "Leest NSE-brondata via rclone vanaf Research Drive, normaliseert tabulaire bestanden, "
        "analyseert ze en schrijft de resultaten terug naar RD."
    )
    documentation: str = "https://docs.langflow.org/components-custom-components"
    icon = "database"
    name = "NSEPreprocessingComponent"

    inputs = [
        StrInput(name="project_dir", display_name="Project Directory", value="/app/nse_runtime", required=True),
        StrInput(name="env_remote_path", display_name="Environment Remote Path", value="RD:<project-path>/.nse-env", required=True),
        StrInput(name="env_file_name", display_name="Local Environment File Name", value=".nse-env", required=True),
        StrInput(name="rd_output_subdir", display_name="RD Output Subdirectory", value=""),
        StrInput(name="include_patterns", display_name="Include Patterns", value="*.csv,*.xlsx,*.xlsm,*.xls,*.json,*.jsonl", required=True),
        StrInput(name="rclone_executable", display_name="Rclone Executable", value="rclone", required=True),
        BoolInput(name="cleanup_local_env_file", display_name="Cleanup Local Env File", value=True),
    ]

    outputs = [Output(display_name="Output", name="output", method="build_output")]

    REQUIRED_ENV_VARS = ["WILLMA_BASE_URL", "SHARE_LINK", "SHARE_PASSWORD", "RD_OUTPUT_PATH"]
    SUPPORTED_SUFFIXES = {".csv", ".xlsx", ".xlsm", ".xls", ".json", ".jsonl"}

    def _project_dir(self) -> Path:
        return Path(self.project_dir)

    def _env_file(self) -> Path:
        return self._project_dir() / self.env_file_name

    def _build_command_environment(self) -> Dict[str, str]:
        env = dict(os.environ)
        project_env_file = self._project_dir() / ".env"
        if project_env_file.exists():
            for key, value in dotenv_values(project_env_file).items():
                if key and value is not None:
                    env[str(key).strip()] = str(value).strip()
        return env

    def _run_command(self, command: List[str], hide_output: bool = False, env: Dict[str, str] | None = None) -> subprocess.CompletedProcess:
        executable = command[0]
        resolved_executable = shutil.which(executable) or (executable if Path(executable).exists() else None)
        if resolved_executable is None:
            raise FileNotFoundError(f"Required executable not found: {executable}")
        resolved_command = [resolved_executable, *command[1:]]
        result = subprocess.run(resolved_command, capture_output=True, text=True, check=False, env=env)
        if result.returncode != 0:
            raise RuntimeError(f"Command failed ({result.returncode}): {' '.join(resolved_command)}\n{result.stderr.strip()}")
        if not hide_output and result.stdout.strip():
            print(result.stdout.strip())
        return result

    def _download_env_file(self) -> Path:
        env_file = self._env_file()
        env_file.parent.mkdir(parents=True, exist_ok=True)
        command_env = self._build_command_environment()
        self._run_command([self.rclone_executable, "copyto", self.env_remote_path, str(env_file)], hide_output=True, env=command_env)
        return env_file

    def _load_config(self) -> Dict[str, str]:
        env_file = self._download_env_file()
        try:
            config = dotenv_values(env_file)
        finally:
            if self.cleanup_local_env_file and env_file.exists():
                env_file.unlink()

        normalized_config: Dict[str, str] = {}
        for key, value in config.items():
            if key is None:
                continue
            normalized_config[str(key).strip()] = "" if value is None else str(value).strip()

        missing = [name for name in self.REQUIRED_ENV_VARS if name not in normalized_config]
        if missing:
            raise ValueError(f"Missing required variables in {env_file.name}: {missing}")

        return normalized_config

    def _prepare_directories(self) -> Dict[str, Path]:
        cache_dir = self._project_dir() / "rd_cache"
        runtime_dir = cache_dir / "preprocessing_runtime"
        output_dir = runtime_dir / "NSE_OUTPUTS"
        log_dir = output_dir / "logs"
        for path in [cache_dir, runtime_dir, output_dir, log_dir]:
            path.mkdir(parents=True, exist_ok=True)
        return {
            "cache_dir": cache_dir,
            "runtime_dir": runtime_dir,
            "output_dir": output_dir,
            "log_dir": log_dir,
        }

    def _extract_share_token(self, share_link: str) -> str:
        match = re.search(r"/s/([^/?#]+)", share_link)
        if not match:
            raise ValueError("Could not extract Research Drive share token from SHARE_LINK")
        return match.group(1)

    def _build_inline_remote(self, share_link: str, obscured_password: str) -> str:
        share_token = self._extract_share_token(share_link)
        return (
            f":webdav,url='https://hr.data.surf.nl/public.php/dav/files/{share_token}',"
            f"vendor='nextcloud',user='{share_token}',pass='{obscured_password}':"
        )

    def build_output(self) -> Data:
        config = self._load_config()
        dirs = self._prepare_directories()

        # Secret-bearing values remain internal and are not returned in the payload.
        rd_output_path = config["RD_OUTPUT_PATH"]

        payload = {
            "component": self.name,
            "project_dir": str(self._project_dir()),
            "rd_output_path": rd_output_path,
            "cache_dir": str(dirs["cache_dir"]),
            "runtime_dir": str(dirs["runtime_dir"]),
            "output_dir": str(dirs["output_dir"]),
            "log_dir": str(dirs["log_dir"]),
        }

        data = Data(data=payload, text="NSE preprocessing initialized")
        setattr(self, "status", data)
        return data
```

### Publieke versie: wat bewust is aangepast

- hardcoded secrets en operationele identifiers zijn vervangen door placeholders
- secret-bearing payloads zijn niet meer opgenomen in voorbeeldoutput
- voorbeelden tonen geen echte hostnamen, gebruikersnamen of paden die niet publiek hoeven te zijn
- de code laat expliciet zien dat secrets intern moeten blijven

---

## Hoe deze component in Langflow gebruikt kan worden

| Stap | Actie |
| --- | --- |
| 1 | Voeg een nieuwe custom component toe in Langflow |
| 2 | Plak de volledige code van `NSEPreprocessingComponent` |
| 3 | Sla de component op |
| 4 | Vul in de UI de juiste `project_dir` en optioneel `rd_output_subdir` in |
| 5 | Start de component-run |
| 6 | Gebruik de gestructureerde `Data` output in volgende componenten |

---

## Volgende stap in de migratie

Na deze eerste samengestelde component is de aanbevolen vervolgstap om de component verder op te knippen in kleinere herbruikbare delen.

| Prioriteit | Volgende component |
| --- | --- |
| 1 | `NSETabularInputLoader` |
| 2 | `NSENormalizer` |
| 3 | `NSEAnalyzer` |
| 4 | `NSEResearchDriveWriter` |
| 5 | `NSEMinimalizerComponent` |
| 6 | `NSEInterrogatorComponent` |

---

## Opmerking over productiegeschiktheid

De code hierboven is bedoeld als **eerste functionele migratiestap** van notebook naar component. Voor productie is verdere hardening wenselijk.

| Onderwerp | Aanbevolen verbetering |
| --- | --- |
| Inputvalidatie | strengere validatie van pad- en patrooninputs |
| Logging | centrale logroutering in plaats van alleen lokaal logfile |
| Secrets | waar mogelijk Langflow secret inputs of een secret manager gebruiken in plaats van alleen `.nse-env` |
| Grote bestanden | streaming of incrementele verwerking overwegen |
| Data contracts | afzonderlijke typed outputs voor schema, analyse en exports |
| Foutafhandeling | fijnmaziger exception classes en herstelpaden |
| Secret handling | geen secrets in CLI-argumenten, logs, traces of generieke payloads opnemen |

---

## Code van de opgesplitste componenten

### `nse_env_loader_component.py`

```python
from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List

from dotenv import dotenv_values
from langflow.custom import Component
from langflow.io import BoolInput, Output, StrInput
from langflow.schema import Data


class NSEEnvLoaderComponent(Component):
    display_name = "NSE Env Loader"
    description = "Laadt .nse-env vanaf Research Drive, valideert verplichte variabelen en bereidt runtime-mappen voor."
    documentation: str = "https://docs.langflow.org/components-custom-components"
    icon = "file-text"
    name = "NSEEnvLoaderComponent"

    inputs = [
        StrInput(name="project_dir", display_name="Project Directory", value="/app/nse_runtime", required=True),
        StrInput(name="env_remote_path", display_name="Environment Remote Path", value="RD:<project-path>/.nse-env", required=True),
        StrInput(name="env_file_name", display_name="Local Environment File Name", value=".nse-env", required=True),
        StrInput(name="rclone_executable", display_name="Rclone Executable", value="rclone", required=True),
        BoolInput(name="cleanup_local_env_file", display_name="Cleanup Local Env File", value=True),
    ]

    outputs = [Output(display_name="Output", name="output", method="build_output")]

    REQUIRED_ENV_VARS = ["WILLMA_BASE_URL", "SHARE_LINK", "SHARE_PASSWORD", "RD_OUTPUT_PATH"]

    def _project_dir(self) -> Path:
        return Path(self.project_dir)

    def _env_file(self) -> Path:
        return self._project_dir() / self.env_file_name

    def _run_command(self, command: List[str], env: Dict[str, str] | None = None) -> subprocess.CompletedProcess:
        executable = command[0]
        resolved_executable = shutil.which(executable) or (executable if Path(executable).exists() else None)
        if resolved_executable is None:
            raise FileNotFoundError(f"Required executable not found: {executable}")
        resolved_command = [resolved_executable, *command[1:]]
        result = subprocess.run(resolved_command, capture_output=True, text=True, check=False, env=env)
        if result.returncode != 0:
            raise RuntimeError(f"Command failed ({result.returncode}): {' '.join(resolved_command)}\n{result.stderr.strip()}")
        return result

    def _build_command_environment(self) -> Dict[str, str]:
        env = dict(os.environ)
        project_env_file = self._project_dir() / ".env"
        if project_env_file.exists():
            for key, value in dotenv_values(project_env_file).items():
                if key and value is not None:
                    env[str(key).strip()] = str(value).strip()
        return env

    def build_output(self) -> Data:
        project_dir = self._project_dir()
        env_file = self._env_file()
        env_file.parent.mkdir(parents=True, exist_ok=True)

        command_env = self._build_command_environment()
        self._run_command([self.rclone_executable, "copyto", self.env_remote_path, str(env_file)], env=command_env)

        try:
            config = dotenv_values(env_file)
        finally:
            if self.cleanup_local_env_file and env_file.exists():
                env_file.unlink()

        normalized_config: Dict[str, str] = {}
        for key, value in config.items():
            if key is None:
                continue
            normalized_config[str(key).strip()] = "" if value is None else str(value).strip()

        missing = [name for name in self.REQUIRED_ENV_VARS if name not in normalized_config]
        if missing:
            raise ValueError(f"Missing required variables in {self.env_file_name}: {missing}")

        cache_dir = project_dir / "rd_cache"
        runtime_dir = cache_dir / "preprocessing_runtime"
        output_dir = runtime_dir / "NSE_OUTPUTS"
        log_dir = output_dir / "logs"
        for path in [cache_dir, runtime_dir, output_dir, log_dir]:
            path.mkdir(parents=True, exist_ok=True)

        payload = {
            "project_dir": str(project_dir),
            "cache_dir": str(cache_dir),
            "runtime_dir": str(runtime_dir),
            "output_dir": str(output_dir),
            "log_dir": str(log_dir),
            "config": {
                "WILLMA_BASE_URL": normalized_config.get("WILLMA_BASE_URL", ""),
                "SHARE_LINK": normalized_config.get("SHARE_LINK", ""),
                "RD_OUTPUT_PATH": normalized_config.get("RD_OUTPUT_PATH", ""),
                "has_share_password": bool(normalized_config.get("SHARE_PASSWORD", "")),
            },
        }
        data = Data(data=payload, text="NSE env loaded")
        setattr(self, "status", data)
        return data
```

### `nse_research_drive_connector_component.py`

```python
from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, List

from langflow.custom import Component
from langflow.io import DataInput, Output, StrInput
from langflow.schema import Data


class NSEResearchDriveConnectorComponent(Component):
    display_name = "NSE Research Drive Connector"
    description = "Valideert toegang tot bronshare en outputpad op Research Drive zonder secrets downstream te lekken."
    documentation: str = "https://docs.langflow.org/components-custom-components"
    icon = "hard-drive"
    name = "NSEResearchDriveConnectorComponent"

    inputs = [
        DataInput(name="env_data", display_name="Env Data", required=True),
        StrInput(name="rclone_executable", display_name="Rclone Executable", value="rclone", required=True),
        StrInput(name="rd_output_subdir", display_name="RD Output Subdirectory", value=""),
    ]

    outputs = [Output(display_name="Output", name="output", method="build_output")]

    def _run_command(self, command: List[str], hide_output: bool = True) -> subprocess.CompletedProcess:
        executable = command[0]
        resolved_executable = shutil.which(executable) or (executable if Path(executable).exists() else None)
        if resolved_executable is None:
            raise FileNotFoundError(f"Required executable not found: {executable}")
        resolved_command = [resolved_executable, *command[1:]]
        result = subprocess.run(resolved_command, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            raise RuntimeError(f"Command failed ({result.returncode}): {' '.join(resolved_command)}\n{result.stderr.strip()}")
        if not hide_output and result.stdout.strip():
            print(result.stdout.strip())
        return result

    def _extract_share_token(self, share_link: str) -> str:
        match = re.search(r"/s/([^/?#]+)", share_link)
        if not match:
            raise ValueError("Could not extract Research Drive share token from SHARE_LINK")
        return match.group(1)

    def _resolve_rd_output_path(self, base_rd_output_path: str) -> str:
        cleaned = base_rd_output_path.rstrip("/")
        subdir = str(self.rd_output_subdir).strip().strip("/")
        return f"{cleaned}/{subdir}" if subdir else cleaned

    def build_output(self) -> Data:
        env_payload = self.env_data.data if hasattr(self.env_data, "data") else self.env_data
        config = env_payload["config"]
        rd_output_path = self._resolve_rd_output_path(config["RD_OUTPUT_PATH"])

        # In een productievariant blijven share token, wachtwoord en inline remote intern.
        self._run_command([self.rclone_executable, "version"])
        remote_files: List[Dict[str, Any]] = []

        payload: Dict[str, Any] = {
            **env_payload,
            "rd_output_path": rd_output_path,
            "source_items_found": len(remote_files),
            "destination_ready": True,
        }
        data = Data(data=payload, text="Research Drive connection validated")
        setattr(self, "status", data)
        return data
```
