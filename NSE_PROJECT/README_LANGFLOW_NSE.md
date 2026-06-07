# Langflow-conversie van de NSE-notebooks

> Dit document beschrijft stap voor stap hoe de notebookworkflow in `D:\OneDrive - Hogeschool Rotterdam\SURF_PILOT\AI_HUB_PILOT\NSE` kan worden omgezet naar **Langflow custom components** die compatibel zijn met de echte Langflow component-API en de Docker-runtime op SURF Ubuntu.

Doel van deze fase: **beginnen met de omzetting van** `NSE-AI-HUB_EXCEL_DATA_PREPROSESSING+NORMALIZATION_V1.ipynb` **naar herbruikbare Langflow componentcode**.

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
| 14.3 | [`nse_tabular_input_loader_component.py`](#nse_tabular_input_loader_componentpy) |
| 14.4 | [`nse_normalizer_component.py`](#nse_normalizer_componentpy) |
| 14.5 | [`nse_analyzer_component.py`](#nse_analyzer_componentpy) |
| 14.6 | [`nse_output_writer_component.py`](#nse_output_writer_componentpy) |
| 14.7 | [`nse_logging_component.py`](#nse_logging_componentpy) |

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
| DNS | werkend A-record, bijvoorbeeld `langflow.src.surf-hosted.nl` |
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
| `.nse-env` beschikbaar op RD | standaardpad: `RD:HR-DATALAB-HEALTHCARE (Projectfolder)/NSE_CODE/.nse-env` |
| Geldige `SHARE_LINK` | moet een echte SURF/RD share token bevatten |
| Schrijfrechten op `RD_OUTPUT_PATH` | vereist voor export van run-output |
| Linux `project_dir` | gebruik `/app/nse_runtime` in plaats van een Windows-pad |
| `rclone.conf` in container | `RD:` moet zichtbaar zijn via `docker exec -it langflow rclone listremotes`.<br> <br>Plaats het echte bestand als `./rclone/rclone.conf` <br> in dezelfde projectmap als `Dockerfile` en `docker-compose.yaml`, <br> zodat de mount `./rclone/rclone.conf:/root/.config/rclone/rclone.conf:ro` <br> werkt.<br> <br> De inhoud moet minimaal een `RD` remote bevatten in deze vorm: <br>`[RD]` <br> `type = webdav` <br> `url = https://hr.data.surf.nl/remote.php/dav/files/Willi@hro.nl` <br>`vendor = nextcloud`<br> `user = Willi@hro.nl` <br> `pass = xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx` <br> <br>

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
            - LANGFLOW_DATABASE_URL=postgresql://langflow:langflow@db:5432/langflow
            - LANGFLOW_AUTO_LOGIN=false
            - LANGFLOW_NEW_USER_SIGNUP=true
            - LANGFLOW_SECRET_KEY=a_long_random_string_here_for_security
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
            - "traefik.http.routers.langflow.rule=Host(`nseflow.analysisnsedata.src.surf-hosted.nl`)"
            - "traefik.http.routers.langflow.entrypoints=websecure"
            - "traefik.http.routers.langflow.tls.certresolver=le"
            - "traefik.http.services.langflow.loadbalancer.server.port=7860"

    db:
        image: postgres:16
        container_name: langflow_db
        restart: unless-stopped
        environment:
            POSTGRES_DB: langflow
            POSTGRES_USER: langflow
            POSTGRES_PASSWORD: langflow
        volumes:
            - postgres_data:/var/lib/postgresql/data
        healthcheck:
            test: ["CMD-SHELL", "pg_isready -U langflow"]
            interval: 10s
            timeout: 5s
            retries: 5

volumes:
    langflow_data:
    postgres_data:
```

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
echo "Step 2.5: Automatically detecting FQDN and creating .env..."
rm -rf .env
touch .env
echo "--------------------------------"
echo "Success! .env file has been created."
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
| `Step 2.5` | Maakt een `.env` bestand aan op basis van de automatisch gedetecteerde hostnaam/FQDN, zodat deploymentvariabelen lokaal beschikbaar zijn. |
| `Step 3` | Controleert of de huidige gebruiker lid is van de `docker`-groep en voegt die gebruiker zo nodig toe. |
| `Step 4` | Bouwt de containers opnieuw en start ze via `docker compose up -d --build`. |
| `Step 5` | Toont de draaiende containers en de Traefik `Host`-routingregel als laatste controle na de deployment. |

| `Step 6` | Maak het script uitvoerbaar en voer het daarna uit vanaf de terminal. |

```bash
# Run script in terminal to create Langflow
ls -la create-langflow.sh  # Check current permissions
chmod +x create-langflow.sh
ls -la create-langflow.sh  # Should show -rwxr-xr-x
./create-langflow.sh       # Now works
sudo bash create-langflow.sh
```

Kleine noot: inhoudelijk zijn `./create-langflow.sh` en `sudo bash create-langflow.sh` twee alternatieve manieren om het script te starten.

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
| `NSEResearchDriveConnector` | share-token extraheren, `rclone obscure` toepassen, inline WebDAV remote opbouwen |
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

Gebruik de opgesplitste componenten in deze keten:

```text
NSEEnvLoaderComponent
    -> NSEResearchDriveConnectorComponent
    -> NSETabularInputLoaderComponent
    -> NSENormalizerComponent
    -> NSEAnalyzerComponent
    -> NSEOutputWriterComponent
    -> NSELoggingComponent
```

### ASCII flowdiagram van de component-keten

```text
[NSEEnvLoaderComponent]
           |
           v
[NSEResearchDriveConnectorComponent]
           |
           v
[NSETabularInputLoaderComponent]
           |
           v
[NSENormalizerComponent]
           |
           v
[NSEAnalyzerComponent]
           |
           v
[NSEOutputWriterComponent]
           |
           v
[NSELoggingComponent]
```

### Betekenis van de keten

| Volgorde | Component | Doel |
| --- | --- | --- |
| 1 | `NSEEnvLoaderComponent` | Laadt `.nse-env`, valideert verplichte variabelen en maakt runtime-mappen aan |
| 2 | `NSEResearchDriveConnectorComponent` | Bouwt de inline `rclone` remote en controleert bron- en doeltoegang |
| 3 | `NSETabularInputLoaderComponent` | Kopieert de bronbestanden naar cache en detecteert load errors |
| 4 | `NSENormalizerComponent` | Normaliseert kolommen en maakt schema-overzicht |
| 5 | `NSEAnalyzerComponent` | Maakt datasetprofielen en numerieke samenvattingen |
| 6 | `NSEOutputWriterComponent` | Schrijft analyses en genormaliseerde datasets lokaal en naar RD |
| 7 | `NSELoggingComponent` | Schrijft de runmetadata en diagnostiek naar logfile |

### Afhandeling van corrupte of verkeerd gelabelde Excelbestanden

De `NSETabularInputLoaderComponent` en `NSENormalizerComponent` gaan nu expliciet robuuster om met ongeldige Excelbestanden.

Belangrijk gedrag:

- `.xlsx` en `.xlsm` worden eerst gelezen met `openpyxl`
- als dat faalt door een niet-geldige zip-structuur of een foutieve workbook-opmaak, volgt een fallback naar `xlrd`
- als ook die fallback faalt, wordt het bestand **niet** meer als fatale componentfout behandeld
- in plaats daarvan wordt een duidelijke melding opgenomen in `load_errors`

Daardoor stopt de Langflow-keten niet meer op fouten zoals:

- `File is not a zip file`
- `Can't find workbook in OLE2 compound document`

Praktisch betekent dit dat verkeerd gelabelde, corrupte of gedeeltelijk beschadigde Excelbestanden zichtbaar blijven in de outputdiagnostiek, terwijl de rest van de geldige bestanden gewoon verder verwerkt wordt.

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
| `.nse-env` via RD laden | Secrets/configuratie komen uit `RD:HR-DATALAB-HEALTHCARE (Projectfolder)/NSE_CODE/.nse-env` in plaats van vanaf lokale `D:` opslag |
| Linux-safe default runtimepad | `project_dir` staat standaard op `/app/nse_runtime` |
| `rclone.conf`-validatie | De component detecteert expliciet of `RD:` in de container beschikbaar is |
| Runtime-artifacts uitsluiten | Eerdere `NSE_OUTPUTS`, `preprocessing_runtime` en `.normalized.csv` bestanden worden niet opnieuw ingelezen |
| Robuustere load error handling | Corrupte Excelbestanden worden in `load_errors` gezet in plaats van de hele component te stoppen |

Omdat de component meerdere parameters nodig heeft, gebruiken we vooral `StrInput` velden en één `BoolInput` voor cleanup. Dat sluit beter aan op gangbare Langflow componenten.

---

## Eerste custom component: `NSEPreprocessingComponent`

Deze eerste component is een **end-to-end preprocessing component** die de complete notebookflow in één component onderbrengt.

### Functionele scope

| Onderdeel | Inbegrepen in eerste component |
| --- | --- |
| `.nse-env` laden | Ja |
| verplichte variabelen valideren | Ja |
| `rclone` inline remote opbouwen | Ja |
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
        StrInput(
            name="project_dir",
            display_name="Project Directory",
            info="Lokale projectmap voor runtime-cache en tijdelijke output.",
            value="/app/nse_runtime",
            required=True,
        ),
        StrInput(
            name="env_remote_path",
            display_name="Environment Remote Path",
            info="Volledig RD-pad naar het .nse-env bestand.",
            value="RD:HR-DATALAB-HEALTHCARE (Projectfolder)/NSE_CODE/.nse-env",
            required=True,
        ),
        StrInput(
            name="env_file_name",
            display_name="Local Environment File Name",
            info="Lokale bestandsnaam voor de tijdelijk gedownloade .env file.",
            value=".nse-env",
            required=True,
        ),
        StrInput(
            name="rd_output_subdir",
            display_name="RD Output Subdirectory",
            info="Submap onder RD_OUTPUT_PATH voor preprocessing runs. Laat leeg om direct RD_OUTPUT_PATH te gebruiken.",
            value="",
        ),
        StrInput(
            name="include_patterns",
            display_name="Include Patterns",
            info="Komma-gescheiden lijst met bestandsfilters voor rclone copy.",
            value="*.csv,*.xlsx,*.xlsm,*.xls,*.json,*.jsonl",
            required=True,
        ),
        StrInput(
            name="rclone_executable",
            display_name="Rclone Executable",
            info="Naam of pad van de rclone executable.",
            value="rclone",
            required=True,
        ),
        BoolInput(
            name="cleanup_local_env_file",
            display_name="Cleanup Local Env File",
            info="Verwijder de tijdelijk gedownloade lokale .nse-env na het inlezen.",
            value=True,
        ),
    ]

    outputs = [
        Output(display_name="Output", name="output", method="build_output"),
    ]

    REQUIRED_ENV_VARS = [
        "WILLMA_BASE_URL",
        "SHARE_LINK",
        "SHARE_PASSWORD",
        "RD_OUTPUT_PATH",
    ]

    SUPPORTED_SUFFIXES = {".csv", ".xlsx", ".xlsm", ".xls", ".json", ".jsonl"}

    RCLONE_ENV_CONFIG_VARS = [
        "RCLONE_CONFIG",
        "RCLONE_CONFIG_RD_TYPE",
        "RCLONE_CONFIG_RD_URL",
        "RCLONE_CONFIG_RD_VENDOR",
        "RCLONE_CONFIG_RD_USER",
        "RCLONE_CONFIG_RD_PASS",
    ]

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

    def _is_rclone_remote_path(self, value: str) -> bool:
        if not value:
            return False
        if value.startswith(":"):
            return True
        remote_name = value.split(":", 1)[0]
        return bool(remote_name) and "/" in value and not Path(value).is_absolute()

    def _validate_rclone_remote_configuration(self, remote_path: str, env: Dict[str, str]) -> None:
        if not self._is_rclone_remote_path(remote_path):
            return

        remote_name = remote_path.split(":", 1)[0]
        if remote_name == "RD":
            has_inline_env_config = all(env.get(name, "").strip() for name in self.RCLONE_ENV_CONFIG_VARS[1:])
            has_explicit_config = bool(env.get("RCLONE_CONFIG", "").strip())
            if not has_inline_env_config and not has_explicit_config:
                raise ValueError(
                    "Rclone remote 'RD:' is not configured inside the Langflow container. "
                    "Configure rclone via /root/.config/rclone/rclone.conf or provide environment variables "
                    "RCLONE_CONFIG_RD_TYPE, RCLONE_CONFIG_RD_URL, RCLONE_CONFIG_RD_VENDOR, "
                    "RCLONE_CONFIG_RD_USER and RCLONE_CONFIG_RD_PASS."
                )

    def _download_env_file(self) -> Path:
        env_file = self._env_file()
        env_file.parent.mkdir(parents=True, exist_ok=True)
        command_env = self._build_command_environment()
        self._validate_rclone_remote_configuration(self.env_remote_path, command_env)
        self._run_command(
            [self.rclone_executable, "copyto", self.env_remote_path, str(env_file)],
            hide_output=True,
            env=command_env,
        )
        return env_file

    def _cache_dir(self) -> Path:
        return self._project_dir() / "rd_cache"

    def _runtime_dir(self) -> Path:
        return self._cache_dir() / "preprocessing_runtime"

    def _output_dir(self) -> Path:
        return self._runtime_dir() / "NSE_OUTPUTS"

    def _log_dir(self) -> Path:
        return self._output_dir() / "logs"

    def _run_command(
        self,
        command: List[str],
        hide_output: bool = False,
        env: Dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess:
        executable = command[0]
        resolved_executable = shutil.which(executable) or (executable if Path(executable).exists() else None)
        if resolved_executable is None:
            raise FileNotFoundError(
                f"Required executable not found: {executable}. Configure 'Rclone Executable' with the full path to rclone."
            )

        resolved_command = [resolved_executable, *command[1:]]
        result = subprocess.run(resolved_command, capture_output=True, text=True, check=False, env=env)
        if result.returncode != 0:
            stderr = result.stderr.strip()
            if "didn't find section in config file" in stderr.lower():
                raise RuntimeError(
                    "Rclone remote configuration is missing inside the Langflow container. "
                    f"The command {' '.join(resolved_command)} failed because remote settings for this path are not available.\n{stderr}"
                )
            raise RuntimeError(
                f"Command failed ({result.returncode}): {' '.join(resolved_command)}\n{stderr}"
            )
        if not hide_output and result.stdout.strip():
            print(result.stdout.strip())
        return result

    def _extract_share_token(self, share_link: str) -> str:
        match = re.search(r"/s/([^/?#]+)", share_link)
        if not match:
            raise ValueError("Could not extract Research Drive share token from SHARE_LINK")
        return match.group(1)

    def _obscure_password(self, password: str) -> str:
        return self._run_command(
            [self.rclone_executable, "obscure", password],
            hide_output=True,
        ).stdout.strip()

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
        runtime_dir = self._runtime_dir()
        output_dir = self._output_dir()
        log_dir = self._log_dir()
        cache_dir = self._cache_dir()

        cache_dir.mkdir(parents=True, exist_ok=True)
        runtime_dir.mkdir(parents=True, exist_ok=True)
        output_dir.mkdir(parents=True, exist_ok=True)
        log_dir.mkdir(parents=True, exist_ok=True)

        return {
            "cache_dir": cache_dir,
            "runtime_dir": runtime_dir,
            "output_dir": output_dir,
            "log_dir": log_dir,
        }

    def _build_inline_remote(self, share_link: str, share_password: str) -> str:
        share_token = self._extract_share_token(share_link)
        obscured_password = self._obscure_password(share_password) if share_password else ""
        return (
            f":webdav,url='https://hr.data.surf.nl/public.php/dav/files/{share_token}',"
            f"vendor='nextcloud',user='{share_token}',pass='{obscured_password}':"
        )

    def _validate_research_drive_access(self, inline_remote: str, rd_output_path: str) -> Dict[str, Any]:
        self._run_command([self.rclone_executable, "version"], hide_output=True)
        remote_listing = self._run_command(
            [self.rclone_executable, "lsjson", inline_remote],
            hide_output=True,
        )
        remote_files = json.loads(remote_listing.stdout or "[]")
        self._run_command([self.rclone_executable, "mkdir", rd_output_path], hide_output=True)
        return {
            "source_items_found": len(remote_files),
            "destination_ready": True,
        }

    def _parse_include_patterns(self) -> List[str]:
        return [item.strip() for item in str(self.include_patterns).split(",") if item.strip()]

    def _is_runtime_artifact(self, file_path: Path, cache_dir: Path) -> bool:
        relative_path = file_path.relative_to(cache_dir)
        relative_parts = {part.lower() for part in relative_path.parts}
        relative_name = relative_path.name.lower()

        if "preprocessing_runtime" in relative_parts or "nse_outputs" in relative_parts:
            return True
        if relative_name.endswith(".normalized.csv"):
            return True
        if relative_name in {"analysis_index.csv", "analysis_results.json", "schema_preview.csv", "load_errors.json"}:
            return True
        return False

    def _copy_input_files(self, inline_remote: str, cache_dir: Path) -> List[Path]:
        command = [self.rclone_executable, "copy", inline_remote, str(cache_dir)]
        for pattern in self._parse_include_patterns():
            command.extend(["--include", pattern])
        command.append("--progress")
        self._run_command(command, hide_output=False)

        return [
            p for p in cache_dir.rglob("*")
            if p.is_file()
            and p.suffix.lower() in self.SUPPORTED_SUFFIXES
            and not self._is_runtime_artifact(p, cache_dir)
        ]

    def _load_tabular_file(self, file_path: Path) -> pd.DataFrame:
        suffix = file_path.suffix.lower()
        if suffix == ".csv":
            return pd.read_csv(file_path)
        if suffix in {".xlsx", ".xlsm"}:
            try:
                return pd.read_excel(file_path, engine="openpyxl")
            except Exception as exc:
                if "zip" in str(exc).lower() or "ole2" in str(exc).lower():
                    return pd.read_excel(file_path, engine="xlrd")
                raise
        if suffix == ".xls":
            return pd.read_excel(file_path, engine="xlrd")
        if suffix == ".json":
            raw = pd.read_json(file_path)
            return raw if isinstance(raw, pd.DataFrame) else pd.json_normalize(raw)
        if suffix == ".jsonl":
            return pd.read_json(file_path, lines=True)
        raise ValueError(f"Unsupported file type: {file_path.suffix}")

    def _load_frames(self, cached_files: List[Path], cache_dir: Path) -> tuple[Dict[str, pd.DataFrame], Dict[str, str]]:
        frames: Dict[str, pd.DataFrame] = {}
        load_errors: Dict[str, str] = {}
        for file_path in cached_files:
            key = str(file_path.relative_to(cache_dir))
            try:
                frames[key] = self._load_tabular_file(file_path)
            except (ValueError, OSError, ParserError, ImportError) as exc:
                load_errors[key] = str(exc)
            except Exception as exc:
                load_errors[key] = f"Unexpected load error ({type(exc).__name__}): {exc}"
        return frames, load_errors

    def _normalize_column_name(self, name: str) -> str:
        normalized = re.sub(r"[^0-9a-zA-Z]+", "_", str(name).strip().lower())
        normalized = re.sub(r"_+", "_", normalized).strip("_")
        return normalized or "unnamed_column"

    def _normalize_frame(self, df: pd.DataFrame) -> pd.DataFrame:
        clean = df.copy()
        clean.columns = [self._normalize_column_name(col) for col in clean.columns]
        clean = clean.replace({"": np.nan, "null": np.nan, "None": np.nan})
        for col in clean.columns:
            if clean[col].dtype == object:
                try:
                    clean[col] = pd.to_datetime(clean[col])
                except (ValueError, TypeError, ParserError):
                    try:
                        clean[col] = pd.to_numeric(clean[col])
                    except (ValueError, TypeError):
                        pass
        return clean

    def _build_schema_preview(self, normalized_frames: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        rows = []
        for name, df in normalized_frames.items():
            rows.append(
                {
                    "file": name,
                    "rows": len(df),
                    "columns": len(df.columns),
                    "column_names": list(df.columns),
                    "missing_values": int(df.isna().sum().sum()),
                }
            )
        return pd.DataFrame(rows)

    def _analyze_frame(self, name: str, df: pd.DataFrame) -> Dict[str, Any]:
        numeric_summary = (
            df.describe(include=[np.number])
            .transpose()
            .reset_index()
            .rename(columns={"index": "column"})
        )
        return {
            "file": name,
            "row_count": int(len(df)),
            "column_count": int(len(df.columns)),
            "columns": list(df.columns),
            "missing_by_column": df.isna().sum().to_dict(),
            "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
            "numeric_summary": numeric_summary.to_dict(orient="records"),
        }

    def _build_analysis_outputs(self, normalized_frames: Dict[str, pd.DataFrame]) -> tuple[List[Dict[str, Any]], pd.DataFrame]:
        analysis_results = [self._analyze_frame(name, df) for name, df in normalized_frames.items()]
        analysis_index_df = pd.DataFrame(
            [
                {
                    "file": item["file"],
                    "row_count": item["row_count"],
                    "column_count": item["column_count"],
                    "missing_total": sum(item["missing_by_column"].values()),
                }
                for item in analysis_results
            ]
        )
        return analysis_results, analysis_index_df

    def _resolve_rd_output_path(self, base_rd_output_path: str) -> str:
        cleaned = base_rd_output_path.rstrip("/")
        subdir = str(self.rd_output_subdir).strip().strip("/")
        if subdir:
            return f"{cleaned}/{subdir}"
        return cleaned

    def _write_outputs(
        self,
        normalized_frames: Dict[str, pd.DataFrame],
        analysis_results: List[Dict[str, Any]],
        analysis_index_df: pd.DataFrame,
        schema_preview_df: pd.DataFrame,
        load_errors: Dict[str, str],
        output_dir: Path,
        rd_output_path: str,
    ) -> Dict[str, Any]:
        run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        run_output_dir = output_dir / f"run_{run_id}"
        run_output_dir.mkdir(parents=True, exist_ok=True)

        summary_csv = run_output_dir / "analysis_index.csv"
        summary_json = run_output_dir / "analysis_results.json"
        schema_csv = run_output_dir / "schema_preview.csv"
        error_json = run_output_dir / "load_errors.json"

        remote_run_output_path = f"{rd_output_path.rstrip('/')}/run_{run_id}"
        self._run_command([self.rclone_executable, "mkdir", remote_run_output_path], hide_output=True)

        schema_preview_df.to_csv(schema_csv, index=False)
        analysis_index_df.to_csv(summary_csv, index=False)
        summary_json.write_text(json.dumps(analysis_results, indent=2, default=str), encoding="utf-8")
        error_json.write_text(json.dumps(load_errors, indent=2), encoding="utf-8")

        written_files = [summary_csv, summary_json, schema_csv, error_json]

        for name, df in normalized_frames.items():
            export_name = re.sub(r"[^0-9a-zA-Z._-]+", "_", name)
            target_csv = run_output_dir / f"{export_name}.normalized.csv"
            df.to_csv(target_csv, index=False)
            written_files.append(target_csv)

        self._run_command(
            [self.rclone_executable, "copy", str(run_output_dir), remote_run_output_path, "--progress"],
            hide_output=False,
        )

        return {
            "run_id": run_id,
            "run_output_dir": str(run_output_dir),
            "remote_run_output_path": remote_run_output_path,
            "written_files": [str(path) for path in written_files],
        }

    def _setup_logger(self, log_dir: Path, run_id: str) -> Path:
        log_file = log_dir / f"nse_analyzer_{run_id}.log"
        logger = logging.getLogger(f"nse_preprocessing_{run_id}")
        logger.setLevel(logging.INFO)
        logger.handlers.clear()

        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
        logger.addHandler(file_handler)

        logger.info("Langflow preprocessing component initialized")
        logger.info("Project directory: %s", self._project_dir())
        logger.info("Cache directory: %s", self._cache_dir())
        return log_file

    def build_output(self) -> Data:
        config = self._load_config()
        dirs = self._prepare_directories()

        rd_output_path = self._resolve_rd_output_path(config["RD_OUTPUT_PATH"])
        inline_remote = self._build_inline_remote(config["SHARE_LINK"], config["SHARE_PASSWORD"])
        validation = self._validate_research_drive_access(inline_remote, rd_output_path)

        cached_files = self._copy_input_files(inline_remote, dirs["cache_dir"])
        frames, load_errors = self._load_frames(cached_files, dirs["cache_dir"])
        normalized_frames = {name: self._normalize_frame(df) for name, df in frames.items()}

        schema_preview_df = self._build_schema_preview(normalized_frames)
        analysis_results, analysis_index_df = self._build_analysis_outputs(normalized_frames)

        write_result = self._write_outputs(
            normalized_frames=normalized_frames,
            analysis_results=analysis_results,
            analysis_index_df=analysis_index_df,
            schema_preview_df=schema_preview_df,
            load_errors=load_errors,
            output_dir=dirs["output_dir"],
            rd_output_path=rd_output_path,
        )

        log_file = self._setup_logger(dirs["log_dir"], write_result["run_id"])

        payload = {
            "component": self.name,
            "project_dir": str(self._project_dir()),
            "env_remote_path": str(self.env_remote_path),
            "env_file": str(self._env_file()),
            "rd_output_path": rd_output_path,
            "source_items_found": validation["source_items_found"],
            "cached_file_count": len(cached_files),
            "loaded_files": list(frames.keys()),
            "load_errors": load_errors,
            "normalized_file_count": len(normalized_frames),
            "schema_preview": schema_preview_df.to_dict(orient="records"),
            "analysis_index": analysis_index_df.to_dict(orient="records"),
            "run_id": write_result["run_id"],
            "remote_run_output_path": write_result["remote_run_output_path"],
            "written_files": write_result["written_files"],
            "log_file": str(log_file),
        }

        data = Data(data=payload, text="NSE preprocessing completed")
        setattr(self, "status", data)
        return data

```

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

### Voorbeeld van logische vervolgkoppelingen in Langflow

| Upstream / downstream | Doel |
| --- | --- |
| `NSEPreprocessingComponent` → `NSEMinimalizerComponent` | Alleen genormaliseerde output doorzetten |
| `NSEPreprocessingComponent` → inspectiecomponent | Schema en missings visueel tonen |
| `NSEPreprocessingComponent` → logging/audit component | Runmetadata vastleggen |

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

Daarmee ontstaat uiteindelijk een volledige Langflow-native NSE-pipeline.

---

## Opmerking over productiegeschiktheid

De code hierboven is bedoeld als **eerste functionele migratiestap** van notebook naar component. Voor productie is verdere hardening wenselijk.

| Onderwerp | Aanbevolen verbetering |
| --- | --- |
| Inputvalidatie | strengere validatie van pad- en patrooninputs |
| Logging | centrale logroutering in plaats van alleen lokaal logfile |
| Secrets | waar mogelijk Langflow secret inputs gebruiken in plaats van alleen `.nse-env` |
| Grote bestanden | streaming of incrementele verwerking overwegen |
| Data contracts | afzonderlijke typed outputs voor schema, analyse en exports |
| Foutafhandeling | fijnmaziger exception classes en herstelpaden |

---

Dit document beschrijft dus de **eerste omzetting van de preprocessing-notebook naar een Langflow custom component**. De volgende migratiestappen kunnen op exact dezelfde wijze worden gedocumenteerd voor de minimalizer en interrogator notebooks.

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
        StrInput(
            name="env_remote_path",
            display_name="Environment Remote Path",
            value="RD:HR-DATALAB-HEALTHCARE (Projectfolder)/NSE_CODE/.nse-env",
            required=True,
        ),
        StrInput(name="env_file_name", display_name="Local Environment File Name", value=".nse-env", required=True),
        StrInput(name="rclone_executable", display_name="Rclone Executable", value="rclone", required=True),
        BoolInput(name="cleanup_local_env_file", display_name="Cleanup Local Env File", value=True),
    ]

    outputs = [Output(display_name="Output", name="output", method="build_output")]

    REQUIRED_ENV_VARS = ["WILLMA_BASE_URL", "SHARE_LINK", "SHARE_PASSWORD", "RD_OUTPUT_PATH"]
    RCLONE_ENV_CONFIG_VARS = [
        "RCLONE_CONFIG",
        "RCLONE_CONFIG_RD_TYPE",
        "RCLONE_CONFIG_RD_URL",
        "RCLONE_CONFIG_RD_VENDOR",
        "RCLONE_CONFIG_RD_USER",
        "RCLONE_CONFIG_RD_PASS",
    ]

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

    def _is_rclone_remote_path(self, value: str) -> bool:
        if not value:
            return False
        if value.startswith(":"):
            return True
        remote_name = value.split(":", 1)[0]
        return bool(remote_name) and "/" in value and not Path(value).is_absolute()

    def _validate_rclone_remote_configuration(self, remote_path: str, env: Dict[str, str]) -> None:
        if not self._is_rclone_remote_path(remote_path):
            return
        remote_name = remote_path.split(":", 1)[0]
        if remote_name == "RD":
            has_inline_env_config = all(env.get(name, "").strip() for name in self.RCLONE_ENV_CONFIG_VARS[1:])
            has_explicit_config = bool(env.get("RCLONE_CONFIG", "").strip())
            if not has_inline_env_config and not has_explicit_config:
                raise ValueError("Rclone remote 'RD:' is not configured inside the Langflow container.")

    def build_output(self) -> Data:
        project_dir = self._project_dir()
        env_file = self._env_file()
        env_file.parent.mkdir(parents=True, exist_ok=True)

        command_env = self._build_command_environment()
        self._validate_rclone_remote_configuration(self.env_remote_path, command_env)
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
            "config": normalized_config,
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
    description = "Bouwt een inline WebDAV remote en valideert toegang tot bronshare en outputpad op Research Drive."
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
        share_token = self._extract_share_token(config["SHARE_LINK"])
        obscured_password = self._run_command([self.rclone_executable, "obscure", config["SHARE_PASSWORD"]]).stdout.strip()
        inline_remote = (
            f":webdav,url='https://hr.data.surf.nl/public.php/dav/files/{share_token}',"
            f"vendor='nextcloud',user='{share_token}',pass='{obscured_password}':"
        )
        rd_output_path = self._resolve_rd_output_path(config["RD_OUTPUT_PATH"])

        self._run_command([self.rclone_executable, "version"])
        remote_listing = self._run_command([self.rclone_executable, "lsjson", inline_remote])
        remote_files = json.loads(remote_listing.stdout or "[]")
        self._run_command([self.rclone_executable, "mkdir", rd_output_path])

        payload: Dict[str, Any] = {
            **env_payload,
            "share_token": share_token,
            "inline_remote": inline_remote,
            "rd_output_path": rd_output_path,
            "source_items_found": len(remote_files),
            "destination_ready": True,
        }
        data = Data(data=payload, text="Research Drive connection validated")
        setattr(self, "status", data)
        return data
```

### `nse_tabular_input_loader_component.py`

```python
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Dict, List

import pandas as pd
import xlrd
from langflow.custom import Component
from langflow.io import DataInput, Output, StrInput
from langflow.schema import Data
from pandas.errors import ParserError
from zipfile import BadZipFile


class NSEInputLoadError(Exception):
    """Raised when a cached tabular input cannot be loaded."""


class NSEInvalidSpreadsheetError(NSEInputLoadError):
    """Raised when a spreadsheet file is corrupt or does not match its extension."""


SPREADSHEET_EXCEPTIONS = (BadZipFile, ValueError, OSError, ImportError, xlrd.biffh.XLRDError)


class NSETabularInputLoaderComponent(Component):
    display_name = "NSE Tabular Input Loader"
    description = "Kopieert ondersteunde bestanden via rclone naar lokale cache en laadt ze in pandas DataFrames."
    documentation: str = "https://docs.langflow.org/components-custom-components"
    icon = "table"
    name = "NSETabularInputLoaderComponent"

    inputs = [
        DataInput(name="rd_data", display_name="Research Drive Data", required=True),
        StrInput(
            name="include_patterns",
            display_name="Include Patterns",
            value="*.csv,*.xlsx,*.xlsm,*.xls,*.json,*.jsonl",
            required=True,
        ),
        StrInput(name="rclone_executable", display_name="Rclone Executable", value="rclone", required=True),
    ]

    outputs = [Output(display_name="Output", name="output", method="build_output")]

    SUPPORTED_SUFFIXES = {".csv", ".xlsx", ".xlsm", ".xls", ".json", ".jsonl"}

    def _run_command(self, command: List[str]) -> subprocess.CompletedProcess:
        executable = command[0]
        resolved_executable = shutil.which(executable) or (executable if Path(executable).exists() else None)
        if resolved_executable is None:
            raise FileNotFoundError(f"Required executable not found: {executable}")
        resolved_command = [resolved_executable, *command[1:]]
        result = subprocess.run(resolved_command, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            raise RuntimeError(f"Command failed ({result.returncode}): {' '.join(resolved_command)}\n{result.stderr.strip()}")
        return result

    def _parse_include_patterns(self) -> List[str]:
        return [item.strip() for item in str(self.include_patterns).split(",") if item.strip()]

    def _is_runtime_artifact(self, file_path: Path, cache_dir: Path) -> bool:
        relative_path = file_path.relative_to(cache_dir)
        relative_parts = {part.lower() for part in relative_path.parts}
        relative_name = relative_path.name.lower()
        if "preprocessing_runtime" in relative_parts or "nse_outputs" in relative_parts:
            return True
        if relative_name.endswith(".normalized.csv"):
            return True
        if relative_name in {"analysis_index.csv", "analysis_results.json", "schema_preview.csv", "load_errors.json"}:
            return True
        return False

    def _load_tabular_file(self, file_path: Path) -> pd.DataFrame:
        suffix = file_path.suffix.lower()
        if suffix == ".csv":
            return pd.read_csv(file_path)
        if suffix in {".xlsx", ".xlsm"}:
            try:
                return pd.read_excel(file_path, engine="openpyxl")
            except SPREADSHEET_EXCEPTIONS as exc:
                if "zip" in str(exc).lower() or "ole2" in str(exc).lower():
                    try:
                        return pd.read_excel(file_path, engine="xlrd")
                    except SPREADSHEET_EXCEPTIONS as fallback_exc:
                        raise NSEInvalidSpreadsheetError(
                            f"Invalid Excel workbook '{file_path.name}': {fallback_exc}"
                        ) from fallback_exc
                raise
        if suffix == ".xls":
            try:
                return pd.read_excel(file_path, engine="xlrd")
            except SPREADSHEET_EXCEPTIONS as exc:
                raise NSEInvalidSpreadsheetError(f"Invalid Excel workbook '{file_path.name}': {exc}") from exc
        if suffix == ".json":
            raw = pd.read_json(file_path)
            return raw if isinstance(raw, pd.DataFrame) else pd.json_normalize(raw)
        if suffix == ".jsonl":
            return pd.read_json(file_path, lines=True)
        raise ValueError(f"Unsupported file type: {file_path.suffix}")

    def build_output(self) -> Data:
        payload = self.rd_data.data if hasattr(self.rd_data, "data") else self.rd_data
        cache_dir = Path(payload["cache_dir"])
        inline_remote = payload["inline_remote"]

        command = [self.rclone_executable, "copy", inline_remote, str(cache_dir)]
        for pattern in self._parse_include_patterns():
            command.extend(["--include", pattern])
        command.append("--progress")
        self._run_command(command)

        cached_files = [
            p for p in cache_dir.rglob("*")
            if p.is_file() and p.suffix.lower() in self.SUPPORTED_SUFFIXES and not self._is_runtime_artifact(p, cache_dir)
        ]

        load_errors: Dict[str, str] = {}
        loaded_files: List[str] = []
        for file_path in cached_files:
            key = str(file_path.relative_to(cache_dir))
            try:
                self._load_tabular_file(file_path)
                loaded_files.append(key)
            except (ValueError, OSError, ParserError, ImportError, NSEInputLoadError) as exc:
                load_errors[key] = str(exc)

        data = Data(
            data={**payload, "cached_files": [str(p) for p in cached_files], "loaded_files": loaded_files, "load_errors": load_errors},
            text="Tabular input loaded",
        )
        setattr(self, "status", data)
        return data
```

### `nse_normalizer_component.py`

```python
from __future__ import annotations

import re
from pathlib import Path
from typing import Dict

import numpy as np
import pandas as pd
import xlrd
from langflow.custom import Component
from langflow.io import DataInput, Output
from langflow.schema import Data
from pandas.errors import ParserError
from zipfile import BadZipFile


SPREADSHEET_EXCEPTIONS = (BadZipFile, ValueError, OSError, ImportError, xlrd.biffh.XLRDError)


class NSENormalizerComponent(Component):
    display_name = "NSE Normalizer"
    description = "Normaliseert kolomnamen en eenvoudige datatypes voor lokaal gecachete tabulaire bestanden."
    documentation: str = "https://docs.langflow.org/components-custom-components"
    icon = "wand-2"
    name = "NSENormalizerComponent"

    inputs = [DataInput(name="input_data", display_name="Input Data", required=True)]
    outputs = [Output(display_name="Output", name="output", method="build_output")]

    def _normalize_column_name(self, name: str) -> str:
        normalized = re.sub(r"[^0-9a-zA-Z]+", "_", str(name).strip().lower())
        normalized = re.sub(r"_+", "_", normalized).strip("_")
        return normalized or "unnamed_column"

    def _load_tabular_file(self, file_path: Path) -> pd.DataFrame:
        suffix = file_path.suffix.lower()
        if suffix == ".csv":
            return pd.read_csv(file_path)
        if suffix in {".xlsx", ".xlsm"}:
            try:
                return pd.read_excel(file_path, engine="openpyxl")
            except SPREADSHEET_EXCEPTIONS as exc:
                if "zip" in str(exc).lower() or "ole2" in str(exc).lower():
                    try:
                        return pd.read_excel(file_path, engine="xlrd")
                    except SPREADSHEET_EXCEPTIONS as fallback_exc:
                        raise ValueError(f"Invalid Excel workbook '{file_path.name}': {fallback_exc}") from fallback_exc
                raise
        if suffix == ".xls":
            try:
                return pd.read_excel(file_path, engine="xlrd")
            except SPREADSHEET_EXCEPTIONS as exc:
                raise ValueError(f"Invalid Excel workbook '{file_path.name}': {exc}") from exc
        if suffix == ".json":
            raw = pd.read_json(file_path)
            return raw if isinstance(raw, pd.DataFrame) else pd.json_normalize(raw)
        if suffix == ".jsonl":
            return pd.read_json(file_path, lines=True)
        raise ValueError(f"Unsupported file type: {file_path.suffix}")

    def _normalize_frame(self, df: pd.DataFrame) -> pd.DataFrame:
        clean = df.copy()
        clean.columns = [self._normalize_column_name(col) for col in clean.columns]
        clean = clean.replace({"": np.nan, "null": np.nan, "None": np.nan})
        for col in clean.columns:
            if clean[col].dtype == object:
                try:
                    clean[col] = pd.to_datetime(clean[col])
                except (ValueError, TypeError, ParserError):
                    try:
                        clean[col] = pd.to_numeric(clean[col])
                    except (ValueError, TypeError):
                        pass
        return clean

    def build_output(self) -> Data:
        payload = self.input_data.data if hasattr(self.input_data, "data") else self.input_data
        normalized_frames: Dict[str, pd.DataFrame] = {}
        schema_preview = []
        cache_dir = Path(payload["cache_dir"])

        for file_path_str in payload.get("cached_files", []):
            file_path = Path(file_path_str)
            key = str(file_path.relative_to(cache_dir))
            if key in payload.get("load_errors", {}):
                continue
            df = self._load_tabular_file(file_path)
            normalized = self._normalize_frame(df)
            normalized_frames[key] = normalized
            schema_preview.append(
                {
                    "file": key,
                    "rows": len(normalized),
                    "columns": len(normalized.columns),
                    "column_names": list(normalized.columns),
                    "missing_values": int(normalized.isna().sum().sum()),
                }
            )

        data = Data(
            data={
                **payload,
                "normalized_frames": {name: df.to_dict(orient="records") for name, df in normalized_frames.items()},
                "schema_preview": schema_preview,
            },
            text="Data normalized",
        )
        setattr(self, "status", data)
        return data
```

### `nse_analyzer_component.py`

```python
from __future__ import annotations

from typing import Any, Dict, List

import numpy as np
import pandas as pd
from langflow.custom import Component
from langflow.io import DataInput, Output
from langflow.schema import Data


class NSEAnalyzerComponent(Component):
    display_name = "NSE Analyzer"
    description = "Genereert datasetprofielen, schema-overzicht en numerieke samenvattingen per bestand."
    documentation: str = "https://docs.langflow.org/components-custom-components"
    icon = "bar-chart-3"
    name = "NSEAnalyzerComponent"

    inputs = [DataInput(name="input_data", display_name="Input Data", required=True)]
    outputs = [Output(display_name="Output", name="output", method="build_output")]

    def _analyze_frame(self, name: str, df: pd.DataFrame) -> Dict[str, Any]:
        numeric_summary = (
            df.describe(include=[np.number]).transpose().reset_index().rename(columns={"index": "column"})
            if not df.empty else pd.DataFrame(columns=["column"])
        )
        return {
            "file": name,
            "row_count": int(len(df)),
            "column_count": int(len(df.columns)),
            "columns": list(df.columns),
            "missing_by_column": df.isna().sum().to_dict(),
            "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
            "numeric_summary": numeric_summary.to_dict(orient="records"),
        }

    def build_output(self) -> Data:
        payload = self.input_data.data if hasattr(self.input_data, "data") else self.input_data
        normalized_frames = {
            name: pd.DataFrame(rows)
            for name, rows in payload.get("normalized_frames", {}).items()
        }
        analysis_results: List[Dict[str, Any]] = [self._analyze_frame(name, df) for name, df in normalized_frames.items()]
        analysis_index = [
            {
                "file": item["file"],
                "row_count": item["row_count"],
                "column_count": item["column_count"],
                "missing_total": sum(item["missing_by_column"].values()),
            }
            for item in analysis_results
        ]
        data = Data(data={**payload, "analysis_results": analysis_results, "analysis_index": analysis_index}, text="Analysis completed")
        setattr(self, "status", data)
        return data
```

### `nse_output_writer_component.py`

```python
from __future__ import annotations

import json
import logging
import re
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import List

import pandas as pd
from langflow.custom import Component
from langflow.io import DataInput, Output, StrInput
from langflow.schema import Data


class NSEOutputWriterComponent(Component):
    display_name = "NSE Output Writer"
    description = "Maakt outputpaden aan, schrijft resultaten lokaal weg en synchroniseert ze naar Research Drive."
    documentation: str = "https://docs.langflow.org/components-custom-components"
    icon = "folder-output"
    name = "NSEOutputWriterComponent"

    inputs = [
        DataInput(name="input_data", display_name="Input Data", required=True),
        StrInput(name="rclone_executable", display_name="Rclone Executable", value="rclone", required=True),
    ]
    outputs = [Output(display_name="Output", name="output", method="build_output")]

    def _run_command(self, command: List[str]) -> subprocess.CompletedProcess:
        executable = command[0]
        resolved_executable = shutil.which(executable) or (executable if Path(executable).exists() else None)
        if resolved_executable is None:
            raise FileNotFoundError(f"Required executable not found: {executable}")
        resolved_command = [resolved_executable, *command[1:]]
        result = subprocess.run(resolved_command, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            raise RuntimeError(f"Command failed ({result.returncode}): {' '.join(resolved_command)}\n{result.stderr.strip()}")
        return result

    def _setup_logger(self, log_dir: Path, run_id: str) -> Path:
        log_file = log_dir / f"nse_analyzer_{run_id}.log"
        logger = logging.getLogger(f"nse_preprocessing_{run_id}")
        logger.setLevel(logging.INFO)
        logger.handlers.clear()
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
        logger.addHandler(file_handler)
        logger.info("Langflow preprocessing component initialized")
        return log_file

    def build_output(self) -> Data:
        payload = self.input_data.data if hasattr(self.input_data, "data") else self.input_data
        output_dir = Path(payload["output_dir"])
        log_dir = Path(payload["log_dir"])
        rd_output_path = payload["rd_output_path"]
        run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        run_output_dir = output_dir / f"run_{run_id}"
        run_output_dir.mkdir(parents=True, exist_ok=True)

        summary_csv = run_output_dir / "analysis_index.csv"
        summary_json = run_output_dir / "analysis_results.json"
        schema_csv = run_output_dir / "schema_preview.csv"
        error_json = run_output_dir / "load_errors.json"

        analysis_index_df = pd.DataFrame(payload.get("analysis_index", []))
        schema_preview_df = pd.DataFrame(payload.get("schema_preview", []))
        analysis_results = payload.get("analysis_results", [])
        load_errors = payload.get("load_errors", {})
        normalized_frames = {name: pd.DataFrame(rows) for name, rows in payload.get("normalized_frames", {}).items()}

        remote_run_output_path = f"{rd_output_path.rstrip('/')}/run_{run_id}"
        self._run_command([self.rclone_executable, "mkdir", remote_run_output_path])

        schema_preview_df.to_csv(schema_csv, index=False)
        analysis_index_df.to_csv(summary_csv, index=False)
        summary_json.write_text(json.dumps(analysis_results, indent=2, default=str), encoding="utf-8")
        error_json.write_text(json.dumps(load_errors, indent=2), encoding="utf-8")

        written_files = [summary_csv, summary_json, schema_csv, error_json]
        for name, df in normalized_frames.items():
            export_name = re.sub(r"[^0-9a-zA-Z._-]+", "_", name)
            target_csv = run_output_dir / f"{export_name}.normalized.csv"
            df.to_csv(target_csv, index=False)
            written_files.append(target_csv)

        self._run_command([self.rclone_executable, "copy", str(run_output_dir), remote_run_output_path, "--progress"])
        log_file = self._setup_logger(log_dir, run_id)

        data = Data(
            data={
                **payload,
                "run_id": run_id,
                "run_output_dir": str(run_output_dir),
                "remote_run_output_path": remote_run_output_path,
                "written_files": [str(path) for path in written_files],
                "log_file": str(log_file),
            },
            text="Outputs written",
        )
        setattr(self, "status", data)
        return data
```

### `nse_logging_component.py`

```python
from __future__ import annotations

import logging
from pathlib import Path

from langflow.custom import Component
from langflow.io import DataInput, Output
from langflow.schema import Data


class NSELoggingComponent(Component):
    display_name = "NSE Logging"
    description = "Schrijft runmetadata en basisdiagnostiek weg naar een logfile op basis van de preprocessing-payload."
    documentation: str = "https://docs.langflow.org/components-custom-components"
    icon = "logs"
    name = "NSELoggingComponent"

    inputs = [DataInput(name="input_data", display_name="Input Data", required=True)]
    outputs = [Output(display_name="Output", name="output", method="build_output")]

    def build_output(self) -> Data:
        payload = self.input_data.data if hasattr(self.input_data, "data") else self.input_data
        log_dir = Path(payload["log_dir"])
        run_id = payload.get("run_id", "manual")
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / f"nse_analyzer_{run_id}.log"

        logger = logging.getLogger(f"nse_logging_{run_id}")
        logger.setLevel(logging.INFO)
        logger.handlers.clear()

        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
        logger.addHandler(file_handler)

        logger.info("Logging component initialized")
        logger.info("Project directory: %s", payload.get("project_dir"))
        logger.info("Cache directory: %s", payload.get("cache_dir"))
        logger.info("RD output path: %s", payload.get("rd_output_path"))
        logger.info("Loaded files: %s", len(payload.get("loaded_files", [])))
        logger.info("Load errors: %s", len(payload.get("load_errors", {})))
        logger.info("Analysis rows: %s", len(payload.get("analysis_index", [])))

        data = Data(data={**payload, "log_file": str(log_file)}, text="Logging completed")
        setattr(self, "status", data)
        return data
```
