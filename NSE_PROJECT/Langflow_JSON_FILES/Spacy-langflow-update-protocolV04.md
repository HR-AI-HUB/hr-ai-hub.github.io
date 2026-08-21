# Langflow Docker Update Protocol — Deploying the Latest Version

This protocol describes the steps required to safely rebuild and update the Langflow container, while preserving the PostgreSQL database and all persistent data.

**Applies to:** `~/LANGFLOW` deployment (Traefik + Langflow + Postgres via `docker-compose.yaml`), FQDN `nseresearch.analysisnsedata.src.surf-hosted.nl`

**Current approach (as of August 2026):** custom Dockerfile built on `python:3.12-slim`, NOT on `langflowai/langflow:latest`. See "Why we stopped using langflowai/langflow:latest" below for the reason.

> **Note on tooling:** always use `docker compose` (space, Compose V2, built into the Docker CLI) — never `docker-compose` (hyphen, the deprecated, unmaintained Compose V1 standalone tool). All commands in this protocol use the space form.

## Prerequisites

- SSH access to `nseresearch` host
- Working directory: `~/LANGFLOW`
- Docker and Docker Compose V2 installed and running (verify with `docker compose version`)

## Important: How to Reach Langflow

The `langflow` service has **no published host port**. Access always goes through Traefik on the FQDN defined in `.env` (`MYFQDN`), never through `localhost:7860` on the host.

```bash
grep MYFQDN .env
curl -skL https://<value-of-MYFQDN>/api/v1/version; echo
```

## The Verified, Working `docker-compose.yaml`

```yaml
services:
  traefik:
    image: traefik:v2.11
    container_name: traefik
    dns:
      - 8.8.8.8
    restart: unless-stopped
    command:
      - --api.dashboard=true
      - --providers.docker=true
      - --providers.docker.exposedbydefault=false
      - --entrypoints.web.address=:80
      - --entrypoints.websecure.address=:443
      - --entrypoints.web.http.redirections.entryPoint.to=websecure
      - --entrypoints.web.http.redirections.entryPoint.scheme=https
      - --certificatesresolvers.le.acme.httpchallenge=true
      - --certificatesresolvers.le.acme.httpchallenge.entrypoint=web
      - --certificatesresolvers.le.acme.storage=/letsencrypt/acme.json
    ports:
      - "80:80"
      - "443:443"
      - "8080:8080"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - ./acme.json:/letsencrypt/acme.json

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
      # ADD FERNET KEY
      # ===> docker compose exec langflow python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
      - LANGFLOW_SECRET_KEY=GrSI-MTpCJwuSinrGgdvnSJKeTB3x05neLOq91xb5xA=
      - LANGFLOW_LANGFLOW_USER_DEFAULT=false
      - LANGFLOW_CACHE_DIR=/app/langflow/cache
      - DO_NOT_TRACK=true
      # ADD THESE TWO LINES:
      - LANGFLOW_SUPERUSER=admin
      - LANGFLOW_SUPERUSER_PASSWORD=b854406c-3d71-4222-9c9a-09aa3e217c52
    volumes:
      - langflow_data:/app/langflow
      - ./langflow_cache:/app/langflow/cache
      - ./chroma_data:/app/chroma_data
      - ./.env:/app/langflow/.env:ro
    user: root
    depends_on:
      db:
        condition: service_healthy
    labels:
      - traefik.enable=true
      - traefik.http.routers.langflow.rule=Host(`${MYFQDN}`)
      - traefik.http.routers.langflow.entrypoints=websecure
      - traefik.http.routers.langflow.tls.certresolver=le
      - traefik.http.services.langflow.loadbalancer.server.port=7860
      - traefik.docker.network=langflow_default

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

**Notable points about this file:**

- `langflow` runs with `user: root` at runtime. This **overrides** the `USER 1000` instruction near the end of the Dockerfile — the container actually runs as root in production, regardless of what the Dockerfile sets.
- `./.env:/app/langflow/.env:ro` is **already mounted** into the container, read-only, at `/app/langflow/.env`. Any component reading `.env` via `dotenv_values()` must use the in-container path `/app/langflow/.env` as its path value — not a host path like `~/LANGFLOW/.env`.
- There is **no `WILLMA_API_KEY` / `AZURE_OPENAI_API_KEY` (etc.) entry** under `langflow`'s `environment:` block — those credentials are read directly out of the mounted `.env` file (or Global Variables) by the components themselves, not injected as OS environment variables by Compose.
- `depends_on: db: condition: service_healthy` means `langflow` will not start until Postgres reports healthy via its `pg_isready` healthcheck.
- The Postgres credentials and `LANGFLOW_SUPERUSER_PASSWORD` are stored in plaintext in this file. Treat repository access to `~/LANGFLOW/docker-compose.yaml` as equivalent to holding these credentials.

## The Verified, Working Dockerfile

```dockerfile
# Custom Langflow image built on Python 3.12 instead of langflowai/langflow:latest.
#
# WHY: as of Langflow 1.10+, the official langflowai/langflow:latest image runs
# on Python 3.14. spaCy 3.8.15 has no published wheels for Python 3.14 (cp314) —
# only cp310 through cp313 are available on PyPI. Installing spaCy therefore
# fails inside the official image with:
#   "No solution found... spacy==3.8.15 has no wheels with a matching Python ABI tag"
#
# This Dockerfile installs Langflow itself via pip on top of a Debian-based
# Python 3.12 image, which is within spaCy's supported range, and avoids the
# RHEL/UBI microdnf workaround entirely since python:3.12-slim is Debian-based.

FROM python:3.12-slim

USER root

# System dependencies for Docling (OpenCV/PDF rendering deps) and ffmpeg for video input.
# Debian-based image, so apt-get works normally (no microdnf/static-binary workaround needed).
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgl1 \
    libglib2.0-0 \
    ffmpeg \
    curl \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Rclone — used for syncing/backing up files (e.g. langflow_backup_*.sql) to/from
# cloud storage. Installed via the official script rather than apt, since Debian's
# packaged version tends to lag behind the upstream release.
RUN curl https://rclone.org/install.sh | bash \
    && rclone version

RUN pip install --no-cache-dir --upgrade pip uv

# Core Langflow install
RUN uv pip install --system langflow==1.11.4

# PostgreSQL drivers — not bundled by default when installing langflow via pip.
# Langflow uses BOTH:
#   - psycopg2 (sync)  -> for the startup version-check (check_postgresql_version_sync)
#   - psycopg (async)  -> for the actual async database engine (create_async_engine)
# Missing either one causes a ModuleNotFoundError at startup.
RUN uv pip install --system psycopg2-binary
RUN uv pip install --system "psycopg[binary]"

# MySQL driver extra used by this deployment
RUN uv pip install --system pymysql

# Docling extras
RUN uv pip install --system 'langflow[docling]' lfx-docling

# spaCy + Dutch model — pinned versions matching the verified local Windows environment
RUN uv pip install --system spacy==3.8.15
RUN python -m spacy download nl_core_news_sm

# Additional pinned dependencies used by the standalone survey flow,
# kept in sync with the verified local package list.
RUN uv pip install --system \
    pandas==2.3.3 \
    openpyxl==3.1.5 \
    SQLAlchemy==2.0.52 \
    openai==2.54.0 \
    python-dotenv==1.2.3 \
    requests

# Switch back to a non-root user for runtime, matching langflowai images (uid 1000).
# NOTE: docker-compose.yaml currently sets `user: root` on the langflow service,
# which overrides this at runtime.
RUN useradd -m -u 1000 langflow || true
USER 1000

EXPOSE 7860

CMD ["langflow", "run", "--host", "0.0.0.0", "--port", "7860"]
```

This Dockerfile has been built, deployed, and confirmed working end-to-end: container starts healthy, database connects, spaCy loads `nl_core_news_sm` correctly, flows run successfully through Traefik on the production FQDN, and the Research Drive Loader component (Appendix A) successfully downloads files via WebDAV using `requests` (explicitly pinned above).

## Update Steps

**Step 1 — Back up the database:**

```bash
cd ~/LANGFLOW
docker compose exec db pg_dump -U langflow langflow > langflow_backup_$(date +%Y%m%d_%H%M).sql
ls -la langflow_backup_*.sql
```

Run this **before** `docker compose down`, since it requires the `db` container running.

**Step 2 — Stop containers:**

```bash
docker compose down
```

Preserves named volumes (`langflow_data`, `postgres_data`) and bind mounts. Never add `-v`.

**Step 3 — Rebuild with a forced pull of the base image:**

```bash
docker compose build --pull
```

**Step 4 — Start services:**

```bash
docker compose up -d
```

**Step 5 — Verify database connection succeeded:**

```bash
docker compose logs --tail=80 langflow
```

Look for `✓ Connecting Database...` — if you see `✗` followed by `ModuleNotFoundError`, a required driver is missing.

**Step 6 — Verify spaCy and the Dutch model:**

```bash
docker compose exec langflow python -c "import spacy; nlp = spacy.load('nl_core_news_sm'); print('spaCy OK:', spacy.__version__, '| model:', nlp.meta['version'])"
```

**Step 7 — Verify version and reachability:**

```bash
curl -skL https://$(grep MYFQDN .env | cut -d= -f2)/api/v1/version; echo
```

**Step 8 — Sanity-check the UI:** log in through the browser, confirm flows load, and run a flow that exercises the NER component, the WILLMA LLM call, and the Research Drive Loader — not just component imports at the Python level.

## Full Command Sequence

```bash
cd ~/LANGFLOW
docker compose exec db pg_dump -U langflow langflow > langflow_backup_$(date +%Y%m%d_%H%M).sql
ls -la langflow_backup_*.sql
docker compose down
docker compose build --pull
docker compose up -d
docker compose logs --tail=80 langflow
docker compose exec langflow python -c "import spacy; nlp = spacy.load('nl_core_news_sm'); print('OK:', nlp.meta['version'])"
curl -skL https://$(grep MYFQDN .env | cut -d= -f2)/api/v1/version; echo
```

## Notes

- **Data safety:** `postgres_data`, `langflow_data`, `chroma_data`, and `langflow_cache` are all preserved across rebuilds as long as `docker compose down -v` is never used.
- **Version pinning:** `langflow==1.11.4` is explicitly pinned in the Dockerfile.
- **Rollback:** restore the database with:
  ```bash
  cat langflow_backup_YYYYMMDD_HHMM.sql | docker compose exec -T db psql -U langflow -d langflow
  ```

---

## Why We Stopped Using `langflowai/langflow:latest`

As of Langflow 1.10 (June 2026), the official Docker image moved to **Python 3.14** as its runtime. spaCy's latest release (3.8.15) only ships wheels for Python 3.10–3.13 (`cp310`–`cp313`) — there is no `cp314` wheel on PyPI. This is a hard blocker, not a configuration mistake. The only practical fix is to stop using the official image as a base and install Langflow via `pip`/`uv` on top of an older, spaCy-compatible Python version instead (`python:3.12-slim`).

### Hidden dependencies discovered so far when installing Langflow via pip

| Package | Why it's needed | Symptom if missing |
|---|---|---|
| `psycopg2-binary` | Sync Postgres driver, used by Langflow's startup version-check | `ModuleNotFoundError: No module named 'psycopg2'` |
| `psycopg[binary]` | Async Postgres driver, used by the async SQLAlchemy engine | `ModuleNotFoundError: No module named 'psycopg'`, container restart loop |
| `requests` | Used by `ResearchDriveLoaderComponent` for WebDAV downloads | `ModuleNotFoundError: No module named 'requests'` when running that component |

> ⚠️ If more `ModuleNotFoundError` failures appear after future rebuilds, the fix follows the same pattern: identify the missing import from the traceback, install it explicitly via `uv pip install --system <package>`, rebuild.

## Troubleshooting: `AttributeError: module 'langflow' has no attribute '__version__'`

Use `importlib.metadata.version('langflow')` or `curl .../api/v1/version` instead of `langflow.__version__`.

## Troubleshooting: No response from `curl http://localhost:7860/...`

The `langflow` service has no `ports:` entry — only Traefik publishes `80`/`443`/`8080` to the host. Always test through the Traefik-routed FQDN, or run curl inside the container.

## Troubleshooting: `307` / `403` on API endpoints — this is normal

Both confirm the API and auth layer are functioning. Use `curl -L` to follow redirects.

## Troubleshooting: `ValueError: Fernet key must be 32 url-safe base64-encoded bytes`

`LANGFLOW_SECRET_KEY` must be a real Fernet key. Generate one with:

```bash
docker compose exec langflow python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

## Troubleshooting: "Bad Gateway" from Traefik

Check `docker compose logs langflow` for the real underlying error (most likely a missing Python dependency after a Dockerfile change).

## Troubleshooting: `AuthenticationError [ComputeAPI] This key does not exist` (WILLMA)

**1. The credential never actually reached the request.** The most common cause: a `SecretStrInput`/`StrInput` field linked to a Global Variable in the UI silently resolves to an empty string at runtime if the component's Python code doesn't declare `load_from_db=True` on that field. See Appendix A.1.

**2. The key itself is stale, revoked, or lacks model access.** Verify directly against SURF's AI-Hub Back Office (`willma.surf.nl`). A working key tested standalone via the `openai` Python client against `https://api.willma.surf.nl/v0` is the fastest way to rule the key itself out.

## Troubleshooting: `KeyError: 'workbook_path'` / mismatched component outputs

If chaining custom components (e.g. `ResearchDriveLoader` → `LoadWorkbookComponent`), confirm the receiving component reads the sending component's actual output keys via `.get(...)`, not direct dict indexing (`[...]`). Also confirm the connection in the canvas points to the correct input port — e.g. a file-producing component's output must go to a dedicated `DataInput` (such as `downloaded_file`), not to `env_settings`, which is reserved for `.env`/Global-Variable settings. Also check that any manual file-upload field (`FileInput`) on the receiving component is empty — a stale previously uploaded file takes priority over a newly connected upstream output if it appears earlier in an `or` fallback chain.

---

# Appendix A: Loading Credentials Without Storing Them in the Flow

This deployment's `docker-compose.yaml` mounts a host `.env` file read-only into the container at `/app/langflow/.env`. Credentials can be read either directly from that mounted file by a component (via `dotenv_values()`), or via Langflow's own **Global Variables** feature (encrypted with `LANGFLOW_SECRET_KEY`).

## A.1 Critical requirement if using Global Variables: `load_from_db=True` on every bound field

Linking a component field to a Global Variable in the UI is not sufficient by itself. The field's Python declaration **must** also include `load_from_db=True`, or Langflow will not resolve the linked value at runtime — the field silently behaves as if it were empty.

This applies to **every** input meant to be sourced from a Global Variable, in **every** component that declares it. Fixing it in only one of two chained components is not sufficient if both declare overlapping fields.

Example — before (broken silently):

```python
SecretStrInput(name="willma_api_key", display_name="WILLMA API Key", value="", advanced=True)
```

After (correct):

```python
SecretStrInput(
    name="willma_api_key",
    display_name="WILLMA API Key",
    value="",
    advanced=True,
    load_from_db=True,
)
```

After adding `load_from_db=True` and saving the component code, **re-link** the Global Variable to the field in the UI — Langflow may reset the field's linkage state when the component's code changes.

## A.2 Verified component code: `LoadEnvConfiguration`

Reads a fixed whitelist of settings from the mounted `.env` file via `dotenv_values()`. Reproduced verbatim below, exactly as deployed and confirmed working:

```python
from pathlib import Path

from dotenv import dotenv_values
from langflow.custom import Component
from langflow.io import Output, StrInput
from langflow.schema import Data


class LoadEnvComponent(Component):
    display_name = "Load .env Configuration"
    description = "Reads provider settings from a user-selected .env file without storing them in the flow."
    icon = "KeyRound"
    name = "LoadEnvConfiguration"

    inputs = [
        StrInput(
            name="env_path",
            display_name=".env File Path",
            value="",
            required=True,
            info="Absolute path to the .env file on the Langflow host.",
        )
    ]
    outputs = [Output(name="settings", display_name="Environment Settings", method="load_settings")]

    def load_settings(self) -> Data:
        env_file = Path(self.env_path).expanduser().resolve()
        if not env_file.is_file():
            raise FileNotFoundError(f".env file not found: {env_file}")
        allowed_names = {
            "DATASET_PATH",
            "EXCEL_OPEN_ANSWERS_DB_PATH",
            "AZURE_OPENAI_ENDPOINT",
            "AZURE_OPENAI_API_KEY",
            "AZURE_OPENAI_API_VERSION",
            "AZURE_OPENAI_DEPLOYMENT",
            "AZURE_OPENAI_MODEL",
            "WILLMA_BASE_URL",
            "WILLMA_API_KEY",
            "WILLMA_MODEL",
            "SHARE_LINK",
            "SHARE_PASSWORD",
            "SHARE_FILENAME",
        }
        settings = {
            name: str(value).strip()
            for name, value in dotenv_values(env_file).items()
            if name in allowed_names and value is not None and str(value).strip()
        }
        self.status = f"Loaded {len(settings)} settings from {env_file.name}"
        return Data(data=settings)
```

**Deployment note:** `env_path` must be set to `/app/langflow/.env` — the in-container path corresponding to the `./.env:/app/langflow/.env:ro` mount in `docker-compose.yaml` — not a host path such as `~/LANGFLOW/.env`. `SHARE_LINK`, `SHARE_PASSWORD`, and `SHARE_FILENAME` were added to `allowed_names` to support the Research Drive Loader component (A.3); without these three entries in the whitelist, `ResearchDriveLoaderComponent` fails with `ValueError: Missing required settings: SHARE_LINK, SHARE_FILENAME` even when the `.env` file itself contains correct values, because `LoadEnvConfiguration` silently filters out any name not in `allowed_names`.

## A.3 Verified component code: `ResearchDriveLoader`

Downloads a file from a password-protected SURF/Nextcloud public share (Research Drive) via WebDAV, using `SHARE_LINK`, `SHARE_PASSWORD`, and `SHARE_FILENAME` supplied through the `env_settings` input (fed by `LoadEnvConfiguration` above). Confirmed working end-to-end in production — reproduced verbatim below:

```python
"""
research_drive_loader.py

Custom Langflow component: Research Drive Loader

Downloads a single file from a password-protected Nextcloud/SURF public
share link (e.g. https://hr.data.surf.nl/s/<token>) via the public WebDAV
endpoint, without requiring rclone.

Follows the same env_settings pattern as ConfigureAzureLLMComponent and
LoadWorkbookComponent: reads SHARE_LINK, SHARE_PASSWORD, and SHARE_FILENAME
from a Data object (env_settings) produced upstream by LoadEnvConfiguration
-- which in turn must expose these three keys, either because they are in
its allowed_names whitelist (if reading a .env file) or because they are
set as Global Variables with load_from_db=True on the corresponding fields.

Nextcloud public-share WebDAV pattern:
    - The share token (the segment after /s/ in the share URL) is used as
      the WebDAV username.
    - The share password (if the share is password-protected) is used as
      the WebDAV password.
    - The download endpoint is always:
          <nextcloud-base-url>/public.php/webdav/<filename>
"""

from pathlib import Path
from urllib.parse import quote, urlparse

import requests

from langflow.custom import Component
from langflow.io import DataInput, Output, StrInput
from langflow.schema import Data


class ResearchDriveLoaderComponent(Component):
    display_name = "Research Drive Loader"
    description = (
        "Downloads a file from a password-protected SURF/Nextcloud public "
        "share (Research Drive) via WebDAV, using SHARE_LINK, SHARE_PASSWORD, "
        "and SHARE_FILENAME from the connected .env Settings."
    )
    icon = "Download"
    name = "ResearchDriveLoader"

    ALLOWED_EXTENSIONS = (".xlsx", ".xls")

    inputs = [
        DataInput(name="env_settings", display_name=".env Settings", required=True),
        StrInput(
            name="download_dir",
            display_name="Download Directory",
            value="/app/langflow/downloads",
            advanced=True,
        ),
        StrInput(
            name="force_redownload",
            display_name="Force Re-download",
            value="false",
            advanced=True,
        ),
    ]

    outputs = [Output(name="file_info", display_name="Downloaded File Info", method="load_research_drive_file")]

    @staticmethod
    def _extract_token_and_base(share_link: str) -> tuple[str, str]:
        parsed = urlparse(share_link)
        if not parsed.scheme or not parsed.netloc:
            raise ValueError(f"SHARE_LINK does not look like a valid URL: {share_link}")
        base = f"{parsed.scheme}://{parsed.netloc}"
        parts = [p for p in parsed.path.split("/") if p]
        if "s" not in parts:
            raise ValueError(f"Could not find a share token ('/s/<token>') in SHARE_LINK: {share_link}")
        token_index = parts.index("s") + 1
        if token_index >= len(parts):
            raise ValueError(f"Could not find a share token ('/s/<token>') in SHARE_LINK: {share_link}")
        return parts[token_index], base

    def load_research_drive_file(self) -> Data:
        settings = self.env_settings.data if self.env_settings else {}

        share_link = str(settings.get("SHARE_LINK", "") or "").strip()
        password = str(settings.get("SHARE_PASSWORD", "") or "").strip()
        filename = str(settings.get("SHARE_FILENAME", "") or "").strip()

        missing = [
            name
            for name, value in (("SHARE_LINK", share_link), ("SHARE_FILENAME", filename))
            if not value
        ]
        if missing:
            raise ValueError(
                f"Missing required settings in env_settings: {', '.join(missing)}. "
                "Confirm the upstream component exposes SHARE_LINK / SHARE_FILENAME "
                "(and optionally SHARE_PASSWORD) as Global Variables or .env entries."
            )

        if not filename.lower().endswith(self.ALLOWED_EXTENSIONS):
            raise ValueError(
                f"SHARE_FILENAME '{filename}' does not have an allowed extension "
                f"{self.ALLOWED_EXTENSIONS}. Refusing to download a non-Excel file."
            )

        force_redownload = str(self.force_redownload or "false").strip().lower() == "true"

        token, base_url = self._extract_token_and_base(share_link)
        webdav_url = f"{base_url}/public.php/webdav/{quote(filename)}"

        download_dir = Path(self.download_dir or "/app/langflow/downloads").expanduser().resolve()
        download_dir.mkdir(parents=True, exist_ok=True)
        dest_path = download_dir / filename

        if dest_path.exists() and not force_redownload:
            size_kb = dest_path.stat().st_size / 1024
            self.status = f"{filename} already present ({size_kb:.1f} KB) — skipped download"
            return Data(data={
                "workbook_path": str(dest_path),
                "file_path": str(dest_path),
                "filename": filename,
                "size_bytes": dest_path.stat().st_size,
                "downloaded": False,
            })

        try:
            response = requests.get(
                webdav_url,
                auth=(token, password),
                headers={"X-Requested-With": "XMLHttpRequest"},
                stream=True,
                timeout=60,
            )
        except requests.exceptions.RequestException as exc:
            raise ConnectionError(f"Could not reach {base_url}: {exc}") from exc

        if response.status_code == 401:
            raise PermissionError(
                "401 Unauthorized — check SHARE_PASSWORD is correct, "
                "or confirm the share still requires a password."
            )
        if response.status_code == 404:
            raise FileNotFoundError(
                f"404 Not Found — check SHARE_FILENAME matches exactly "
                f"(including spaces, capitalization, and extension): '{filename}'"
            )
        response.raise_for_status()

        tmp_path = dest_path.with_suffix(dest_path.suffix + ".part")
        try:
            with open(tmp_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            tmp_path.replace(dest_path)
        finally:
            if tmp_path.exists():
                tmp_path.unlink(missing_ok=True)

        size_kb = dest_path.stat().st_size / 1024
        self.status = f"Downloaded {filename} ({size_kb:.1f} KB) to {dest_path}"
        return Data(data={
            "workbook_path": str(dest_path),
            "file_path": str(dest_path),
            "filename": filename,
            "size_bytes": dest_path.stat().st_size,
            "downloaded": True,
        })
```

**Wiring notes, confirmed working in production:**

- `LoadEnvConfiguration` → `env_settings` input of `ResearchDriveLoader` (requires `SHARE_LINK`/`SHARE_PASSWORD`/`SHARE_FILENAME` in `allowed_names`, per A.2).
- `ResearchDriveLoader` → `file_info` output → `downloaded_file` input of `LoadWorkbookComponent` (a dedicated `DataInput`, added specifically for this purpose — see A.4). Do **not** connect it to `LoadWorkbookComponent`'s `env_settings` input; that is reserved for `DATASET_PATH`/`EXCEL_OPEN_ANSWERS_DB_PATH`.
- The output includes both `workbook_path` and `file_path` (identical values) so it is compatible with either key name expected downstream.
- `LoadWorkbookComponent`'s `Excel Workbook` manual upload field must be left empty — a previously uploaded file there takes priority over the connected `downloaded_file` input in the fallback chain, causing the wrong (stale) file to be loaded.

## A.4 Verified component code: `LoadWorkbookComponent`

Updated to accept the `ResearchDriveLoader` output via a dedicated `downloaded_file` input, avoiding the `KeyError: 'workbook_path'` that occurs if the loader's output is wired into `env_settings` instead. Reproduced verbatim below:

```python
from pathlib import Path

from langflow.custom import Component
from langflow.io import DataInput, FileInput, Output, StrInput
from langflow.schema import Data


class LoadWorkbookComponent(Component):
    display_name = "Load Workbook"
    description = "Selects and validates the Excel workbook and worksheet."
    icon = "FileSpreadsheet"
    name = "LoadWorkbook"

    inputs = [
        DataInput(name="env_settings", display_name=".env Settings", required=False),
        DataInput(
            name="downloaded_file",
            display_name="Downloaded File Info",
            required=False,
            info="Data output from ResearchDriveLoader (or similar). "
            "Its 'file_path' key is used if no manual path/upload is given.",
        ),
        FileInput(
            name="workbook_file",
            display_name="Excel Workbook",
            fileTypes=["xlsx", "xls"],
            required=False,
        ),
        StrInput(
            name="workbook_path",
            display_name="Workbook Path Override",
            value="",
            required=False,
            advanced=True,
        ),
        StrInput(name="sheet_name", display_name="Worksheet", value="", advanced=True),
        StrInput(name="database_path", display_name="SQLite Path", value="", advanced=True),
    ]
    outputs = [Output(name="workbook", display_name="Workbook", method="load_workbook")]

    def load_workbook(self) -> Data:
        import pandas as pd

        settings = self.env_settings.data if self.env_settings else {}

        downloaded_path = ""
        if self.downloaded_file:
            downloaded_data = self.downloaded_file.data if hasattr(self.downloaded_file, "data") else {}
            downloaded_path = str(downloaded_data.get("file_path", "") or "")

        workbook_value = str(
            self.workbook_file
            or self.workbook_path
            or downloaded_path
            or settings.get("DATASET_PATH", "")
        ).strip()

        if not workbook_value:
            raise ValueError(
                "No workbook found. Upload an Excel workbook, set the Workbook Path Override, "
                "connect a Downloaded File Info input, or set DATASET_PATH in the selected .env file."
            )

        workbook = Path(workbook_value).expanduser().resolve()
        if not workbook.exists():
            raise FileNotFoundError(f"Workbook not found: {workbook}")

        sheets = pd.ExcelFile(workbook).sheet_names
        selected_sheet = self.sheet_name.strip() or sheets[0]
        if selected_sheet not in sheets:
            raise ValueError(f"Worksheet '{selected_sheet}' not found. Available: {sheets}")

        self.status = f"{workbook.name} / {selected_sheet}"
        return Data(data={
            "workbook_path": str(workbook),
            "sheet_name": selected_sheet,
            "database_path": self.database_path or settings.get("EXCEL_OPEN_ANSWERS_DB_PATH", ""),
            "available_sheets": sheets,
        })
```

## A.5 Standalone verification notebook

A standalone Jupyter notebook (`research_drive_loader.ipynb`) mirrors the WebDAV download logic of `ResearchDriveLoaderComponent` exactly, independent of Langflow. It reads the same three `.env` values, builds the same WebDAV URL, downloads atomically via a `.part` temp file, and previews the resulting workbook with `pandas`. Confirmed working. Use it to isolate whether a failure is in the download logic itself (test here first) versus in Langflow's component wiring (test in the flow second) — this separation is what confirmed, in this deployment's case, that the WebDAV/credentials layer was correct and the remaining issues were entirely in how `ResearchDriveLoader`'s output was connected to `LoadWorkbookComponent`.

---

# Appendix B: What Needs to Be Installed (Standalone Flow)

Standalone installation checklist for `standaloneAzAIHubExcelOpenAnsInterro-LangV1.11.4V4.json` outside the main `~/LANGFLOW` deployment.

## B.1 Common Requirements

- Langflow 1.11.4, Python 3.12 (not 3.14 — see spaCy compatibility note above)
- `pandas==2.3.3`, `openpyxl==3.1.5`, `SQLAlchemy==2.0.52`
- `spacy==3.8.15` with Dutch model `nl_core_news_sm==3.8.0`
- `openai==2.54.0`, `python-dotenv==1.2.3`, `requests`
- `psycopg2-binary` and `psycopg[binary]` if using PostgreSQL as the Langflow backend database
- An Excel workbook containing the survey data (or credentials for the Research Drive share providing it — see Appendix A)
- A writable directory for the SQLite database, cache metadata, and lock files
- Credentials for Azure OpenAI or WILLMA SURF AI-Hub, via `.env` or Global Variables (see Appendix A — and if using Global Variables, confirm `load_from_db=True` is set on every linked field per A.1)

## B.2 Native Windows 11 Installation

```powershell
py -3.12 -m venv venv
venv\Scripts\Activate
pip install --upgrade pip setuptools wheel
pip install langflow==1.11.4
pip install pandas==2.3.3 openpyxl==3.1.5 SQLAlchemy==2.0.52
pip install spacy==3.8.15
python -m spacy download nl_core_news_sm
pip install openai==2.54.0 python-dotenv==1.2.3 requests
```

Create working directories and `.env` as needed, then launch:

```powershell
langflow run
```

## B.3 Docker on Ubuntu 24.04 VM

Use the same verified Dockerfile documented above (Python 3.12 base, includes Rclone). Install Docker Engine per standard instructions, then:

```bash
docker build --pull -t langflow-standalone:1.11.4 .
docker run -d \
  --name langflow-standalone \
  -p 7860:7860 \
  --env-file .env \
  -v $(pwd)/data:/app/langflow \
  langflow-standalone:1.11.4
```

Note: this `docker run` form does **not** set `--user root`, so the Dockerfile's `USER 1000` instruction takes effect here — unlike the production `docker-compose.yaml`, which sets `user: root` and overrides it.

## B.4 Verification Checklist

- [ ] Python 3.12 active (not 3.14)
- [ ] Langflow 1.11.4 installed (verify via `importlib.metadata.version('langflow')` or `/api/v1/version`)
- [ ] `psycopg2-binary` and `psycopg[binary]` installed if using Postgres
- [ ] `spacy==3.8.15` installed with `nl_core_news_sm==3.8.0` model downloaded and loadable
- [ ] `pandas==2.3.3`, `openpyxl==3.1.5`, `SQLAlchemy==2.0.52`, `openai==2.54.0`, `python-dotenv==1.2.3`, `requests` installed
- [ ] `rclone` installed and `rclone version` succeeds, if backups/sync are needed
- [ ] `LANGFLOW_SECRET_KEY` is a valid, generated Fernet key
- [ ] Excel workbook accessible, either directly or via the Research Drive Loader (Appendix A); writable directory available for SQLite/cache
- [ ] Credentials available via `.env` or Global Variables, including `SHARE_LINK`/`SHARE_PASSWORD`/`SHARE_FILENAME` if using Research Drive Loader
- [ ] If using the mounted `.env` file (production default): the loader's env-file path is `/app/langflow/.env`, not a host path, and `allowed_names` in `LoadEnvConfiguration` includes every key actually needed downstream
- [ ] If using Global Variables for credentials instead: every linked `SecretStrInput`/`StrInput` field declares `load_from_db=True`, and the Global Variable was re-linked in the UI after any component code change
- [ ] `ResearchDriveLoader`'s `file_info` output is wired to `LoadWorkbookComponent`'s `downloaded_file` input (not `env_settings`), and `LoadWorkbookComponent`'s manual `Excel Workbook` upload field is empty
- [ ] Flow JSON imported with no missing-component errors
- [ ] Login, flow loading, and flow execution (including the NER step) all confirmed working in the browser UI
- [ ] A test question that triggers the LLM summary step returns a successful response, not `AuthenticationError [ComputeAPI] This key does not exist`
- [ ] `ResearchDriveLoader` downloads successfully and `LoadWorkbookComponent` opens the resulting file without `KeyError` or `FileNotFoundError`
