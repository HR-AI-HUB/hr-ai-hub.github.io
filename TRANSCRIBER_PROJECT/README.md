# Whisper v3 Two-Speaker Diarized Transcription with SURF AI-HUB + Langflow

> **Platform:** [SURF AI-HUB (WiLLMa)](https://hr-ai-hub.github.io/) · [SURF Research Cloud](https://www.surf.nl/en/surf-research-cloud-collaborative-research-environment) · [Langflow 1.9.3](https://langflow.org/) · Docker · Ubuntu 22.04  
> **Repository:** [HR-DataLab-Healthcare / RESEARCH\_SUPPORT — SRAM\_DOCKER\_LANGFLOW](https://github.com/HR-DataLab-Healthcare/RESEARCH_SUPPORT/tree/main/PROJECTS/SRAM_DOCKER_LANGFLOW)
> 
> **Notebook:** `LANGFLOW_WILLMA_WHISPER_TRANSCRIBER_V07.ipynb` [current](https://github.com/HR-AI-HUB/hr-ai-hub.github.io/blob/main/TRANSCRIBER_PROJECT/Jupyter_Notebooks/LANGFLOW_WILLMA_WHISPER_TRANSCRIBER_V07.ipynb)
> 
> **Ready-to-import flow:** Download the Langflow JSON from [HR-AI-HUB GitHub](https://github.com/HR-AI-HUB/hr-ai-hub.github.io/blob/main/TRANSCRIBER_PROJECT/LANGFLOW_WHISPER_JSON/URL%20NextCLOUD-AUDVIs-PREPRO%2BTRANSCR%2BTIME%2BDIAR-BETA.json)

---

## Table of Contents

1. [What this tool does](#what-this-tool-does)
2. [Architecture overview](#architecture-overview)
3. [Prerequisites](#prerequisites)
4. [Step 1 — Provision a SURF Research Cloud VM](#step-1--provision-a-surf-research-cloud-vm)
5. [Step 2 — Deploy Langflow on SRC with Docker](#step-2--deploy-langflow-on-src-with-docker)
6. [Step 3 — Obtain a WILLMA API Key](#step-3--obtain-a-willma-api-key)
7. [Step 4 — Import the ready-made flow](#step-4--import-the-ready-made-flow)
8. [Step 5 — Build the flow from scratch (component by component)](#step-5--build-the-flow-from-scratch-component-by-component)
9. [Configuration reference](#configuration-reference)
10. [How two-speaker diarization works](#how-two-speaker-diarization-works)
11. [Supported media formats and URL types](#supported-audio-formats)
12. [Troubleshooting](#troubleshooting)
13. [Security notes](#security-notes)
14. [License](#license)
15. [Changelog](#changelog)

---

## What this tool does

The here described Langflow flow accepts a **private (SURF Research Drive)  or public audio or video file via encrypted https URL** (pasted into the Langflow Chat Playground).

It downloads the audio file into memory, or alternativly, it extracts audio from video containers via `ffmpeg`, <br> cleans it with a **pure-Python DSP chain**, and sends it to the **SURF WILLMA Whisper API** for transcription and **two-speaker diarization**.

The output is a readable timestamped **dialogue script** rendered directly in the Chat Playground:

```
[0m:00s] Speaker 001:
"Goedemiddag, ik ben hier voor mijn afspraak."

[0m:08s] Speaker 002:
"Welkom, kunt u uw naam even noemen?"

[0m:12s] Speaker 001:
"Ja, mijn naam is ..."
```

The underlying models running on SURF infrastructure are:

| Model | Purpose |
|-------|---------|
| `openai/whisper-large-v3` | Speech-to-text transcription |
| `pyannote/speaker-diarization-3.1` | Speaker turn detection |

All compute stays within **SURF's own data centres** — NEN-ISO/IEC 27001 compliant, no data leaves the Dutch sovereign cloud.

---

## Architecture overview

```
[Chat Input]
     │  (audio or video encrypted https URL as text)
     ▼
[1. WILLMA Audio Downloader]
     │  (raw audio bytes in RAM)
     ▼
[2. Audio Preprocessor  — pure Python/stdlib]
     │  (16 kHz mono PCM WAV bytes)
     ▼
[3. WILLMA Whisper Diarized Transcriber]
     │  ├─► transcript_message  (formatted dialogue script → Chat Output)
     │  └─► segments_json       (structured segments list for downstream use)
     ▼
[Chat Output]
     (dialogue script displayed in Playground)
```

### Component summary

| # | Component | Technology | Key role |
|---|-----------|-----------|----------|
| — | **Chat Input** | Langflow built-in | Entry point — captures the URL typed by the user |
| 1 | **WILLMA Audio Downloader** | `requests` (stdlib) | HTTP GET → in-memory `bytes`; handles GitHub raw rewrites, Nextcloud/ownCloud share links, and password-protected SURF Research Drive links via cookie-based session auth *(V07+)* |
| 2 | **Audio Preprocessor** | `wave`, `struct`, `math` (stdlib) + `ffmpeg` subprocess *(V07+)* | Video audio extraction (MP4/MKV/MOV/AVI/WEBM) via ffmpeg; WAV DSP: stereo→mono, resample to 16 kHz, high-pass filter, DRC, peak-normalize |
| 3 | **WILLMA Whisper Diarized Transcriber** | `requests`, `wave`, `io` | 30 s chunked STT + pyannote diarization → overlap-matrix alignment → dialogue script |
| — | **Chat Output** | Langflow built-in | Renders the transcript as an AI reply in the Playground |

---

## Prerequisites

| Requirement | Notes |
|-------------|-------|
| SURF Research Cloud (SRC) account | Via [SRAM](https://sram.surf.nl) — contact your institution's SURF coordinator |
| SRC Collaborative Organisation (CO) | Your research group or DataLab must be a member of a CO with SRC access |
| Ubuntu 22.04 VM on SRC | Public IP, DNS A-record, ports 80 / 443 / 8080 open |
| WILLMA API key | Request via [SURF Servicedesk](https://servicedesk.surf.nl) (login via SURF/SRAM required) |
| Docker + Docker Compose | Installed on the VM (scripts below handle this) |
| Audio / video files accessible by encrypted https URL | Public links, like e.g. GitHub raw file URLs as well as Private, password protected, Share links from SURF RESEARCH DRIVE |

<img align="left" width="150" height="250" src="https://github.com/HR-AI-HUB/hr-ai-hub.github.io/blob/main/TRANSCRIBER_PROJECT/FIGs/SURF_RESREARCH_DRIVE_EXTERNALSHARE_LINK.png">

> **NEN-ISO/IEC 27001 compliance:** Participation in the SURF AI-HUB pilot is only permitted when the applicable information-security framework satisfies [NEN-ISO/IEC 27001](https://www.forumstandaardisatie.nl/open-standaarden/nen-isoiec-27001). SURF holds ISO 27001 certification for all its services.

---

## Step 1 — Provision a SURF Research Cloud VM

1. **Log in to SURF Research Cloud** at [portal.live.surfresearchcloud.nl](https://portal.live.surfresearchcloud.nl) using your institutional credentials via SRAM.

2. **Create a new Workspace** — choose the _Ubuntu 22.04_ catalog item. Recommended minimum specs for Langflow + Whisper workloads:

   | Resource | Minimum | Recommended |
   |----------|---------|-------------|
   | vCPU | 4 | 8 |
   | RAM | 16 GB | 64 GB |
   | Storage | 50 GB | 100 GB |

3. **Assign a public IP** and request a **DNS A-record** for your VM (e.g. `langflow.src.surf-hosted.nl`). This is required for Let's Encrypt HTTPS certificates.

4. **Open firewall ports** in the SRC portal: `80` (HTTP), `443` (HTTPS), `8080` (Traefik dashboard).

5. **SSH into the VM** as a non-root user:

   ```bash
   ssh <your-username>@<vm-ip-or-fqdn>
   ```

---

## Step 2 — Deploy Langflow on SRC with Docker

This project uses the automated scripts from the [SRAM\_DOCKER\_LANGFLOW](https://github.com/HR-DataLab-Healthcare/RESEARCH_SUPPORT/tree/main/PROJECTS/SRAM_DOCKER_LANGFLOW) repository. The stack consists of:

- **Traefik** — reverse proxy + automatic Let's Encrypt TLS
- **Langflow** — visual AI flow builder (custom Docker image with Docling extras)
- **PostgreSQL 16** — persistent flow and session storage

### 2a. Download the deployment files

Open a terminal on the SRC VM and run:

```bash
# Create a working directory
mkdir -p LANGFLOW && cd LANGFLOW

# Bootstrap: open the script URL in your browser, copy the raw content,
# then paste it into nano:
nano get-files.sh
# Paste the content from:
# https://github.com/HR-DataLab-Healthcare/RESEARCH_SUPPORT/blob/main/PROJECTS/SRAM_DOCKER_LANGFLOW/get-files.sh
# Save: Ctrl+X → Y → Enter

# Run the bootstrap script (it uses git sparse-checkout to fetch only
# the SRAM_DOCKER_LANGFLOW folder, then cleans up .git)
bash get-files.sh
```

After this completes, `ls -la` should show: `Dockerfile`, `docker-compose.yaml`, `create-langflow.sh`, `get-files.sh`.

### 2b. Start the Langflow stack

```bash
# Make the deployment script executable
chmod +x create-langflow.sh

# Run as sudo — this script will:
#   1. Stop and disable any running Nginx (conflicts with Traefik on port 80)
#   2. Create acme.json (Let's Encrypt cert storage, chmod 600)
#   3. Auto-detect your FQDN and write it to .env
#   4. Add your user to the docker group
#   5. Run: docker compose up -d --build
sudo bash create-langflow.sh
```

> **What happens:** Traefik listens on ports 80 and 443. HTTP is automatically redirected to HTTPS. Let's Encrypt issues a certificate using the HTTP-01 challenge. Langflow starts on internal port 7860 and is proxied via your FQDN.

### 2c. Verify the stack is running

```bash
docker ps
```

Expected output:

```
CONTAINER ID   IMAGE                    STATUS        PORTS
xxxxxxxxxxxx   langflow_docker-langflow Up 2 minutes
xxxxxxxxxxxx   postgres:16              Up 2 minutes
xxxxxxxxxxxx   traefik:v2.11            Up 2 minutes  0.0.0.0:80->80/tcp, 0.0.0.0:443->443/tcp
```

Open `https://<your-fqdn>` in a browser. You should see the Langflow login page.

### 2d. Create your first admin account

On first visit, register an admin account via the Langflow signup page. Then use the bulk-user script from the repository if you need to provision multiple researcher accounts.

### 2e. (Optional) Fix resource-limit errors

If you see `SystemError: (11, 'Resource temporarily unavailable')` in Langflow logs, add file-descriptor limits to the `langflow` service in `docker-compose.yaml`:

```yaml
langflow:
  ulimits:
    nofile:
      soft: 65535
      hard: 65535
```

Then restart: `docker compose down && docker compose up -d --build`.

### 2f. Install ffmpeg for video support (V07+)

V07 requires `ffmpeg` inside the Langflow container. Add the following line to the `Dockerfile` **before** the `USER 1000` line and rebuild:

```dockerfile
# V07+ — Install ffmpeg for video audio extraction
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*
```

Rebuild the image:

```bash
docker compose up -d --build
```

Verify inside the running container:

```bash
docker exec langflow ffmpeg -version
```

> If `ffmpeg` is absent, video files (MP4, MKV, MOV, etc.) are forwarded unchanged to WILLMA Whisper — which handles them natively — but the DSP preprocessing step is skipped.

---

## Step 3 — Obtain a WILLMA API Key

1. Log in to the [SURF Servicedesk](https://servicedesk.surf.nl) via your SURF/SRAM account.
2. Navigate to the **AI-Hub (WiLLMa) Pilot** page.
3. Request API access for your research group / DataLab.
4. Once approved, you will receive:
   - **Base URL:** `https://willma.surf.nl/api/v0`
   - **API Key:** a hex string in the format `77696c6c6d61-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`

> Store the API key securely — do **not** commit it to version control. In Langflow, use the **SecretStr** input type (padlock icon) which stores the value encrypted in the Langflow database.

---

## Step 4 — Import the ready-made flow

If you want to skip manual component assembly, import the pre-wired flow JSON directly:

1. **Download the flow JSON** from GitHub:
   [URL NextCLOUD-AUDVIs-PREPRO+TRANSCR+TIME+DIAR-BETA.json](https://github.com/HR-AI-HUB/hr-ai-hub.github.io/blob/main/TRANSCRIBER_PROJECT/LANGFLOW_WHISPER_JSON/URL%20NextCLOUD-AUDVIs-PREPRO%2BTRANSCR%2BTIME%2BDIAR-BETA.json)
   Click **Raw** (or the download icon) on that page to download the `.json` file to your computer.
2. In Langflow, click **My Flows → Import** (the upload icon, top-right of the flows list).
3. Select the downloaded JSON file and confirm.
4. Open the imported flow. You will see all 5 components already connected.
5. Click the **3. WILLMA Whisper Diarized Transcriber** component, navigate to the **WILLMA API Key** field (padlock icon), and enter your API key.
6. If you use password-protected SURF Research Drive share links, enter the password in the **Share Link Password** field of the **1. WILLMA Audio Downloader** component.
7. Click **Playground** (top-right) and paste an audio or video URL to test.

---

## Step 5 — Build the flow from scratch (component by component)

This section provides the complete **V07** component code from `LANGFLOW_WILLMA_WHISPER_TRANSCRIBER_V07.ipynb`.

### 5a. Create a new flow

In Langflow, click **New Flow → Blank Flow**. Name it `WILLMA Whisper V07`.

---

### Component 1 — Chat Input (built-in)

1. In the component sidebar, search for **Chat Input** under the _Inputs_ category.
2. Drag it onto the canvas.
3. No configuration needed — it will capture the URL typed in the Playground.

**Output wire:** `message` (Chat Message)

---

### Component 2 — WILLMA Audio Downloader

1. Click **+** → **Custom Component** to open the code editor.
2. Paste the following code and click **Check & Save**:

```python
import re
import requests
import os
from urllib.parse import urlparse, parse_qs
from langflow.custom import Component
from langflow.inputs import MessageInput, SecretStrInput
from langflow.io import Output
from langflow.schema import Data

class WillmaAudioDownloader(Component):
    display_name = "1. WILLMA Audio Downloader"
    description = "Downloads an audio URL directly from Chat Input into an in-memory Data packet stream."
    
    inputs = [
        MessageInput(
            name="chat_message",
            display_name="Chat Input Message",
            required=True
        ),
        SecretStrInput(
            name="share_password",
            display_name="Share Link Password (optional)",
            value="",
            info="Password for password-protected Nextcloud / SURF Research Drive share links. Leave empty for public (no-password) shares."
        )
    ]
    
    outputs = [
        Output(name="audio_packet", display_name="Audio Packet Data", method="download_to_memory")
    ]

    def _authenticated_session_download(self, url_target, nc_share_token, pwd, parsed_url):
        """Download a file from a password-protected Nextcloud/ownCloud public share.

        Mirrors exactly what a browser does:
          1. GET /s/{token}  →  extract CSRF requesttoken from HTML
          2. POST /s/{token}/authenticate/downloadshare  →  server sets session cookie
          3. GET the original download URL  →  session cookie is sent automatically

        This works for all Nextcloud/ownCloud versions, including SURF Research Drive
        (ownCloud-based).  HTTP Basic Auth on /s/{token}/download is NOT honoured by
        ownCloud/Nextcloud for password-protected public shares — cookie auth is required.
        """
        session = requests.Session()
        base = f"{parsed_url.scheme}://{parsed_url.netloc}"

        # Step 1 — load the share landing page to get the CSRF requesttoken
        request_token = ""
        try:
            page_resp = session.get(
                f"{base}/s/{nc_share_token}", timeout=30, allow_redirects=True
            )
            m = re.search(r'data-requesttoken="([^"]+)"', page_resp.text)
            if m:
                request_token = m.group(1)
        except Exception:
            pass

        # Step 2 — POST the password to the authenticate endpoint.
        # Try the Nextcloud path first, then the ownCloud / generic fallbacks.
        post_data = {"password": pwd}
        if request_token:
            post_data["requesttoken"] = request_token
        auth_headers = {"X-Requested-With": "XMLHttpRequest"}

        for auth_url in [
            f"{base}/s/{nc_share_token}/authenticate/downloadshare",   # Nextcloud
            f"{base}/index.php/s/{nc_share_token}/authenticate",        # ownCloud
            f"{base}/s/{nc_share_token}/authenticate",                  # generic
        ]:
            try:
                session.post(
                    auth_url, data=post_data, headers=auth_headers,
                    timeout=30, allow_redirects=True
                )
                break   # first POST that doesn't throw sets the session cookie
            except Exception:
                continue

        # Step 3 — GET the download URL; the session cookie is sent automatically
        return session.get(url_target, timeout=120, allow_redirects=True)

    def download_to_memory(self) -> Data:
        message_obj = self.chat_message
        url_target = ""
        nc_share_token = None

        if message_obj and hasattr(message_obj, "text") and message_obj.text:
            url_target = str(message_obj.text).strip()
            
        if not url_target or not url_target.startswith(("http://", "https://")):
            return Data(text="INVALID_URL", data={"bytes": None, "filename": "audio.mp3"})

        # --- URL rewriting ---

        # GitHub: rewrite web URLs to raw content
        if "github.com" in url_target and "/blob/" in url_target:
            url_target = url_target.replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/")
        elif "github.com" in url_target and "/raw/" in url_target:
            url_target = url_target.replace("github.com", "raw.githubusercontent.com").replace("/raw/", "/")

        # Nextcloud / SURF Research Drive — file viewer URL
        # /apps/files/files/{id}?dir=... → /index.php/f/{id}?download
        nc_viewer = re.search(r'/apps/files/files/(\d+)', url_target)
        if nc_viewer:
            base = url_target[:url_target.index('/apps/files/files/')]
            url_target = f"{base}/index.php/f/{nc_viewer.group(1)}?download"

        # Nextcloud / ownCloud — public share link.
        # Capture share token; append /download if not already present.
        # ?path= query params are preserved when /download is already in the path.
        else:
            nc_share_match = re.search(r'/s/([A-Za-z0-9_-]+)', url_target.split('?')[0])
            if nc_share_match:
                nc_share_token = nc_share_match.group(1)
                share_base = url_target.split('?')[0].rstrip('/')
                if not share_base.endswith('/download'):
                    url_target = share_base + "/download"

        # Resolve password — handle both plain str and Pydantic SecretStr from Langflow
        pwd = getattr(self, "share_password", "") or ""
        if hasattr(pwd, "get_secret_value"):
            pwd = pwd.get_secret_value()
        pwd = str(pwd).strip() if pwd else ""

        try:
            if nc_share_token and pwd:
                # Cookie-based session auth — the only reliable method for
                # password-protected public shares on Nextcloud / ownCloud / SURF Research Drive.
                parsed = urlparse(url_target)
                response = self._authenticated_session_download(
                    url_target, nc_share_token, pwd, parsed
                )
            else:
                response = requests.get(url_target, timeout=120, allow_redirects=True)

            response.raise_for_status()

            # HTML response → still on the password-entry page (wrong/missing password)
            # or an internal login-required page.
            content_type = response.headers.get("Content-Type", "").lower()
            if "text/html" in content_type:
                return Data(text="AUTH_REQUIRED", data={"bytes": None, "filename": "audio.mp3"})

            audio_bytes = response.content

            # Prefer Content-Disposition filename (reliable for Nextcloud downloads)
            filename = ""
            content_disp = response.headers.get("Content-Disposition", "")
            if content_disp:
                cd_match = re.search(
                    r"filename\*?=(?:UTF-8'')?[\"']?([^\"';\r\n]+)[\"']?",
                    content_disp, re.IGNORECASE
                )
                if cd_match:
                    filename = cd_match.group(1).strip().strip("\"'")

            # Fall back to URL path basename
            if not filename:
                clean_url_path = url_target.split("?")[0]
                filename = os.path.basename(clean_url_path) or "audio.wav"

            return Data(
                text=filename,
                data={
                    "bytes": audio_bytes,
                    "filename": filename,
                    "size_bytes": len(audio_bytes)
                }
            )
        except requests.exceptions.HTTPError as http_err:
            status = http_err.response.status_code if http_err.response is not None else 0
            if status in (401, 403):
                return Data(text="AUTH_REQUIRED", data={"bytes": None, "filename": "audio.mp3"})
            return Data(text="DOWNLOAD_FAILED", data={"bytes": None, "filename": "audio.mp3"})
        except Exception:
            return Data(text="DOWNLOAD_FAILED", data={"bytes": None, "filename": "audio.mp3"})
```

3. **Wire:** connect Chat Input `message` → Downloader `chat_message`.

**Inputs:** `chat_message` (URL) · `share_password` (SecretStr, optional — for password-protected SURF Research Drive shares)

**Output wire:** `audio_packet` (Audio Packet Data)

**Example — SURF Research Drive password-protected share link:**

- Share link (from the UI): `https://hr.data.surf.nl/s/7Gz8JCzZDfCy42D`
- Paste as download URL: `https://hr.data.surf.nl/s/7Gz8JCzZDfCy42D/download?path=/ECO_LARS_INTERVIEW.mp4`

![SURF Research Drive share link example](images/surf_share_link_example.png)

---

### Component 3 — Audio Preprocessor (Pure Python / Stdlib-only)

1. Create another **Custom Component**.
2. Paste the following code and click **Check & Save**:

```python
import io
import os
import tempfile
import wave
import struct
import math
import subprocess
from langflow.custom import Component
from langflow.inputs import DataInput, IntInput, FloatInput, BoolInput
from langflow.io import Output
from langflow.schema import Data

class AudioPreprocessorComponent(Component):
    display_name = "2. Audio Preprocessor"
    description = "Extracts audio from video containers (MP4/MKV/MOV/AVI/WEBM) via ffmpeg, then applies 16kHz resampling, Highpass Filtering, DRC, and Peak Normalization in memory."

    VIDEO_EXTENSIONS = (".mp4", ".mkv", ".avi", ".mov", ".webm", ".m4v", ".mpg", ".mpeg")

    inputs = [
        DataInput(
            name="incoming_packet",
            display_name="Raw Audio/Video Packet Data",
            required=True
        ),
        IntInput(
            name="target_sample_rate",
            display_name="Target Sample Rate (Hz)",
            value=16000
        ),
        FloatInput(
            name="highpass_cutoff_hz",
            display_name="Highpass Cutoff (Hz)",
            value=90.0
        ),
        BoolInput(
            name="enable_drc",
            display_name="Enable Dynamic Range Control",
            value=True
        ),
        FloatInput(
            name="peak_normalize",
            display_name="Peak Normalization Target",
            value=0.98
        )
    ]

    outputs = [
        Output(name="cleaned_packet", display_name="Cleaned Audio Packet", method="preprocess_audio")
    ]

    def _extract_audio_from_video(self, video_bytes: bytes, filename: str = "video.mp4") -> bytes:
        """Extract audio track from a video container via a /tmp temp file.

        Writes video_bytes to a named temp file, runs ffmpeg against it, reads
        the output WAV back into memory, then deletes both temp files.

        Using a real file (instead of stdin pipe) gives ffmpeg full random-access
        seeking — required for MP4 files whose moov atom is at the end (Zoom
        recordings, phone captures, screen recordings).  The cache:pipe approach
        fails for these files inside Docker containers.

        Raises RuntimeError if ffmpeg exits with a non-zero return code.
        """
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "mp4"
        with tempfile.NamedTemporaryFile(suffix=f".{ext}", delete=False, dir="/tmp") as f_in:
            f_in.write(video_bytes)
            tmp_in = f_in.name
        tmp_out = tmp_in + ".wav"
        try:
            cmd = [
                "ffmpeg", "-y",
                "-i", tmp_in,
                "-vn",                                    # drop video stream
                "-ac", "1",                               # force mono
                "-ar", str(self.target_sample_rate),      # resample to target rate
                "-sample_fmt", "s16",                     # 16-bit signed PCM
                "-f", "wav",
                tmp_out
            ]
            result = subprocess.run(cmd, capture_output=True, timeout=300)
            if result.returncode != 0:
                error_msg = result.stderr.decode("utf-8", errors="replace")
                raise RuntimeError(f"ffmpeg audio extraction failed: {error_msg[-500:]}")
            with open(tmp_out, "rb") as f_out:
                return f_out.read()
        finally:
            for p in (tmp_in, tmp_out):
                try:
                    os.unlink(p)
                except OSError:
                    pass

    def _resample_linear(self, data, orig_sr, target_sr):
        if orig_sr == target_sr or len(data) == 0:
            return data
        ratio = float(orig_sr) / float(target_sr)
        target_length = int(len(data) / ratio)
        resampled = [0.0] * target_length
        for i in range(target_length):
            orig_idx = i * ratio
            idx_low = int(math.floor(orig_idx))
            idx_high = min(idx_low + 1, len(data) - 1)
            weight = orig_idx - idx_low
            resampled[i] = (1.0 - weight) * data[idx_low] + weight * data[idx_high]
        return resampled

    def _apply_highpass(self, data, sample_rate, cutoff):
        if len(data) == 0 or cutoff <= 0:
            return data
        rc = 1.0 / (2.0 * math.pi * cutoff)
        dt = 1.0 / sample_rate
        alpha = rc / (rc + dt)
        filtered = [0.0] * len(data)
        filtered[0] = data[0]
        for i in range(1, len(data)):
            filtered[i] = alpha * (filtered[i-1] + data[i] - data[i-1])
        return filtered

    def _apply_drc(self, data):
        boosted = []
        for sample in data:
            sign = 1.0 if sample >= 0 else -1.0
            boosted.append(sign * math.pow(abs(sample), 0.88))
        return boosted

    def preprocess_audio(self) -> Data:
        packet = self.incoming_packet.data if self.incoming_packet else {}
        raw_bytes = packet.get("bytes")
        filename = packet.get("filename", "audio.wav")

        if not raw_bytes or len(raw_bytes) == 0:
            return self.incoming_packet  # passthrough — preserves error codes (AUTH_REQUIRED, DOWNLOAD_FAILED, etc.)

        # Step 0: Extract audio track from video containers (MP4, MKV, MOV, AVI, WEBM, etc.)
        name_lower = filename.lower()
        if any(name_lower.endswith(ext) for ext in self.VIDEO_EXTENSIONS):
            try:
                raw_bytes = self._extract_audio_from_video(raw_bytes, filename)
                # Rename to .wav so the DSP chain picks it up
                filename = filename.rsplit(".", 1)[0] + ".wav"
            except Exception:
                return self.incoming_packet  # ffmpeg unavailable or failed — passthrough to Transcriber

        # Process as WAV if extension matches, otherwise fallback pass-through (e.g. MP3, FLAC)
        if not filename.lower().endswith(".wav"):
            return self.incoming_packet

        try:
            # Decode PCM_16 bytes to Float Mono array
            with wave.open(io.BytesIO(raw_bytes), 'rb') as wav_in:
                orig_sr = wav_in.getframerate()
                channels = wav_in.getnchannels()
                sampwidth = wav_in.getsampwidth()
                n_frames = wav_in.getnframes()
                raw_frames = wav_in.readframes(n_frames)

                if sampwidth != 2:
                    return self.incoming_packet  # Dynamic pass-through if not 16-bit

                fmt = f"<{n_frames * channels}h"
                integer_samples = struct.unpack(fmt, raw_frames)
                float_samples = [s / 32768.0 for s in integer_samples]

            # Downmix Stereo/Surround to Mono channel layout
            if channels > 1:
                mono = []
                for i in range(0, len(float_samples), channels):
                    mono.append(sum(float_samples[i:i+channels]) / channels)
                float_samples = mono

            # Execute DSP chain
            float_samples = self._resample_linear(float_samples, orig_sr, self.target_sample_rate)
            float_samples = self._apply_highpass(float_samples, self.target_sample_rate, self.highpass_cutoff_hz)

            if self.enable_drc:
                float_samples = self._apply_drc(float_samples)

            peak = max(abs(s) for s in float_samples) if float_samples else 0.0
            if peak > 0:
                float_samples = [(s / peak) * self.peak_normalize for s in float_samples]

            # Re-encode clean Float array back into standard PCM_16 WAV bytes
            out_buffer = io.BytesIO()
            with wave.open(out_buffer, 'wb') as wav_out:
                wav_out.setnchannels(1)
                wav_out.setsampwidth(2)
                wav_out.setframerate(self.target_sample_rate)
                int_frames = [int(max(-32768, min(32767, s * 32767))) for s in float_samples]
                wav_out.writeframes(struct.pack(f"<{len(int_frames)}h", *int_frames))

            processed_bytes = out_buffer.getvalue()
            return Data(
                text=filename,
                data={
                    "bytes": processed_bytes,
                    "filename": filename,
                    "size_bytes": len(processed_bytes)
                }
            )
        except Exception:
            return self.incoming_packet  # Resilient fallback in case header tracking breaks
```

3. **Wire:** Downloader `audio_packet` → Preprocessor `incoming_packet`.

**Output wire:** `cleaned_packet` (Cleaned Audio Packet)

> **Why stdlib-only?** The Langflow Docker container may not have scipy or numpy available without modifying the image. The preprocessor uses only `wave`, `struct`, `math`, and `subprocess` — no extra pip dependencies (ffmpeg is a system binary).

> **Docker requirement:** `ffmpeg` must be installed in the Langflow container for video extraction. See [Step 2f](#2f-install-ffmpeg-for-video-support-v07). Without ffmpeg, video files are passed through directly to WILLMA Whisper, which handles them natively.

---

### Component 4 — WILLMA Whisper Diarized Transcriber

1. Create another **Custom Component**.
2. Paste the following code and click **Check & Save**:

```python
import io
import wave
import requests
from langflow.custom import Component
from langflow.inputs import DataInput, StrInput, SecretStrInput, IntInput, FloatInput
from langflow.io import Output
from langflow.schema.message import Message

class WillmaWhisperTranscriber(Component):
    display_name = "3. WILLMA Whisper Diarized Transcriber"
    description = "Transcribes and diarizes audio stream segments into timestamped two-speaker dialogue scripts."

    inputs = [
        DataInput(
            name="incoming_packet",
            display_name="Audio Packet Data",
            required=True
        ),
        StrInput(
            name="base_url",
            display_name="WILLMA Base URL",
            value="https://willma.surf.nl/api/v0"
        ),
        SecretStrInput(
            name="api_key",
            display_name="WILLMA API Key",
            required=True
        ),
        StrInput(
            name="language",
            display_name="Language Code",
            value="nl"
        ),
        IntInput(
            name="chunk_seconds",
            display_name="Processing Window Size (s)",
            value=30
        ),
        FloatInput(
            name="min_overlap_seconds",
            display_name="Minimum Speaker Overlap (s)",
            value=0.15
        ),
        FloatInput(
            name="pause_threshold",
            display_name="Diarization Turn Pause Gap (s)",
            value=1.2
        )
    ]

    outputs = [
        Output(name="transcript_message", display_name="Diarized Transcript", method="get_chat_message"),
        Output(name="segments_json", display_name="Structured Segments List", method="get_segments")
    ]

    _MIME_MAP = {
        "mp4": "video/mp4", "mkv": "video/x-matroska", "avi": "video/x-msvideo",
        "mov": "video/quicktime", "webm": "video/webm", "m4v": "video/mp4",
        "mp3": "audio/mpeg", "m4a": "audio/mp4", "flac": "audio/flac",
        "ogg": "audio/ogg", "aac": "audio/aac", "opus": "audio/opus",
        "wav": "audio/wav",
    }

    def _fetch_model_name(self) -> str:
        headers = {"X-API-KEY": self.api_key, "Content-Type": "application/json"}
        resp = requests.get(f"{self.base_url}/sequences", headers=headers, timeout=45)
        resp.raise_for_status()
        catalog = resp.json()
        preferred = ["whisper-large-v3", "faster-whisper-large-v3", "whisper-large", "whisper-medium"]
        for frag in preferred:
            for item in catalog:
                if frag in str(item.get("name", "")).lower():
                    return item.get("name")
        for item in catalog:
            if "whisper" in str(item.get("name", "")).lower():
                return item.get("name")
        return "whisper-large-v3"

    def _overlap_seconds(self, start_a, end_a, start_b, end_b):
        return max(0.0, min(end_a, end_b) - max(start_a, start_b))

    def _build_turns_from_stt(self, segments, pause_threshold):
        turns = []
        if not segments:
            return turns
        sorted_segs = sorted(segments, key=lambda x: (float(x.get("start", 0)), float(x.get("end", 0))))
        current = {
            "start": float(sorted_segs[0].get("start", 0)),
            "end": float(sorted_segs[0].get("end", 0)),
            "text": (sorted_segs[0].get("text") or "").strip(),
        }
        for seg in sorted_segs[1:]:
            seg_start = float(seg.get("start", 0))
            seg_end = float(seg.get("end", 0))
            seg_text = (seg.get("text") or "").strip()
            gap = seg_start - current["end"]
            if gap >= pause_threshold:
                turns.append(current)
                current = {"start": seg_start, "end": seg_end, "text": seg_text}
            else:
                current["end"] = max(current["end"], seg_end)
                if seg_text:
                    current["text"] = (current["text"] + " " + seg_text).strip()
        turns.append(current)
        return turns

    def _alternative_diarization_from_stt(self, segments, pause_threshold, start_with="001"):
        turns = self._build_turns_from_stt(segments, pause_threshold)
        speaker_cycle = ["002", "001"] if start_with == "002" else ["001", "002"]
        diarization = []
        for index, turn in enumerate(turns):
            diarization.append({
                "start": round(float(turn["start"]), 3),
                "end": round(float(turn["end"]), 3),
                "speaker": speaker_cycle[index % 2]
            })
        return diarization

    def _force_two_speaker_labels(self, segments):
        counts = {}
        for seg in segments:
            raw = seg.get("speaker")
            if raw in (None, "", "UNKNOWN"):
                continue
            counts[str(raw).strip()] = counts.get(str(raw).strip(), 0) + 1
        top_speakers = [item[0] for item in sorted(counts.items(), key=lambda x: x[1], reverse=True)[:2]]

        spk_map = {}
        if len(top_speakers) >= 1: spk_map[top_speakers[0]] = "001"
        if len(top_speakers) >= 2: spk_map[top_speakers[1]] = "002"

        forced = []
        for seg in segments:
            updated = dict(seg)
            raw = updated.get("speaker")
            if raw in (None, "", "UNKNOWN"):
                updated["speaker"] = "UNKNOWN"
            else:
                k = str(raw).strip()
                updated["speaker"] = k if k in ("001", "002") else spk_map.get(k, "UNKNOWN")
            forced.append(updated)
        return forced

    def _assign_unknown_by_neighbors(self, segments):
        if not segments:
            return segments
        count = len(segments)
        for index, seg in enumerate(segments):
            if seg.get("speaker") != "UNKNOWN":
                continue
            prev_spk, next_spk = None, None
            for left in range(index - 1, -1, -1):
                if segments[left].get("speaker") and segments[left].get("speaker") != "UNKNOWN":
                    prev_spk = segments[left].get("speaker")
                    break
            for right in range(index + 1, count):
                if segments[right].get("speaker") and segments[right].get("speaker") != "UNKNOWN":
                    next_spk = segments[right].get("speaker")
                    break
            if prev_spk and prev_spk == next_spk:
                seg["speaker"] = prev_spk
        return segments

    def _merge_speaker_segments(self, segments, max_gap=1.0):
        merged = []
        sorted_segs = sorted(segments, key=lambda x: (float(x.get("start", 0)), float(x.get("end", 0))))
        for seg in sorted_segs:
            text = seg.get("text", "").strip()
            if not text:
                continue
            if not merged:
                merged.append(dict(seg))
                continue
            prev = merged[-1]
            same_speaker = prev.get("speaker") == seg.get("speaker")
            gap = float(seg.get("start", 0)) - float(prev.get("end", 0))
            if same_speaker and gap <= max_gap:
                prev["end"] = max(prev["end"], seg.get("end", prev["end"]))
                prev["text"] = (prev.get("text").strip() + " " + text).strip()
            else:
                merged.append(dict(seg))
        return merged

    def _assign_speakers(self, stt_segments, diar_diarization, diar_source, chunk_offset=0.0):
        """Map each STT segment to a speaker via time-overlap matching, then offset timestamps."""
        result = []
        for seg in stt_segments:
            local_start = float(seg.get("start", 0))
            local_end = float(seg.get("end", 0))
            best_speaker = None
            best_overlap = 0.0
            for diar_seg in diar_diarization:
                d_start = float(diar_seg.get("start", 0))
                d_end = float(diar_seg.get("end", 0))
                overlap = self._overlap_seconds(local_start, local_end, d_start, d_end)
                if overlap > best_overlap:
                    best_overlap = overlap
                    best_speaker = diar_seg.get("speaker") or diar_seg.get("label") or diar_seg.get("id")
            out = dict(seg)
            out["start"] = round(local_start + chunk_offset, 3)
            out["end"] = round(local_end + chunk_offset, 3)
            if diar_source == "stt_turn_fallback":
                out["speaker"] = best_speaker or "UNKNOWN"
            else:
                out["speaker"] = best_speaker if best_overlap >= self.min_overlap_seconds else "UNKNOWN"
            out["speaker_source"] = diar_source
            out["speaker_overlap"] = round(best_overlap, 3)
            result.append(out)
        return result

    def process_audio_pipeline(self):
        if hasattr(self, "_cached_result"):
            return self._cached_result

        packet = self.incoming_packet.data if self.incoming_packet else {}
        audio_bytes = packet.get("bytes")
        filename = packet.get("filename", "audio.wav")

        if not audio_bytes or len(audio_bytes) == 0:
            # Surface specific error codes from the downloader as actionable messages
            packet_status = getattr(self.incoming_packet, "text", "") or ""
            if packet_status == "AUTH_REQUIRED":
                return (
                    "Download blocked — authentication required.\n\n"
                    "The URL you pasted is an internal link (requires a SURF login), a folder share, "
                    "or a password-protected share link.\n\n"
                    "How to fix this:\n\n"
                    "  Option A — Share the file directly (no password):\n"
                    "    1. In SURF Research Drive, right-click the AUDIO FILE (not the folder)\n"
                    "    2. Share → New share link → no password → Copy link\n"
                    "    3. Paste that link here (e.g. https://hr.data.surf.nl/s/AbCdEfGh)\n\n"
                    "  Option B — File within a shared folder (no password):\n"
                    "    Append the filename to the folder download URL:\n"
                    "    https://hr.data.surf.nl/s/<sharetoken>/download?path=/filename.mp4\n\n"
                    "  Option C — Password-protected share link:\n"
                    "    Enter the share password in the 'Share Link Password' field\n"
                    "    of the WILLMA Audio Downloader component.",
                    []
                )
            return "No input audio data detected.", []

        stt_model_name = self._fetch_model_name()
        diar_model_name = "pyannote/speaker-diarization-3.1"
        headers = {"X-API-KEY": self.api_key, "Accept": "application/json"}

        all_aligned_segments = []

        # --- Probe: is this a valid WAV container? ---
        # If ffmpeg is unavailable in the container, the preprocessor passes through raw
        # video bytes (MP4/MKV/etc.). Detect this and route to the direct-send path so
        # WILLMA Whisper handles the container natively — no chunking needed.
        is_wav = False
        try:
            with wave.open(io.BytesIO(audio_bytes), 'rb') as _probe:
                _probe.getnframes()
            is_wav = True
        except Exception:
            is_wav = False

        if is_wav:
            # ── WAV path: chunked processing ──────────────────────────────────────────
            fallback_starts_with = "001"
            try:
                with wave.open(io.BytesIO(audio_bytes), 'rb') as wav_in:
                    params = wav_in.getparams()
                    sr = wav_in.getframerate()
                    total_frames = wav_in.getnframes()

                frames_per_chunk = int(self.chunk_seconds * sr)
                frames_read = 0
                chunk_index = 0

                while frames_read < total_frames:
                    to_read = min(frames_per_chunk, total_frames - frames_read)

                    with wave.open(io.BytesIO(audio_bytes), 'rb') as wav_src:
                        wav_src.setpos(frames_read)
                        chunk_raw_frames = wav_src.readframes(to_read)

                    chunk_buffer = io.BytesIO()
                    with wave.open(chunk_buffer, 'wb') as wav_dst:
                        wav_dst.setparams(params)
                        wav_dst.writeframes(chunk_raw_frames)

                    chunk_payload_bytes = chunk_buffer.getvalue()
                    chunk_offset_seconds = frames_read / sr
                    chunk_filename = f"chunk_{chunk_index:03d}.wav"

                    stt_data = {
                        "model": stt_model_name, "language": self.language,
                        "stream": "false", "response_format": "verbose_json",
                        "timestamp_granularities[]": "segment"
                    }
                    stt_files = {"file": (chunk_filename, chunk_payload_bytes, "audio/wav")}
                    stt_resp = requests.post(f"{self.base_url}/audio/transcriptions", headers=headers, files=stt_files, data=stt_data, timeout=240)
                    stt_resp.raise_for_status()
                    chunk_stt_segments = stt_resp.json().get("segments", []) or []

                    diar_diarization = []
                    diar_source = "api"
                    try:
                        diar_files = {"file": (chunk_filename, chunk_payload_bytes, "audio/wav")}
                        diar_resp = requests.post(f"{self.base_url}/audio/custom-diarization", headers=headers, files=diar_files, data={"model": diar_model_name}, timeout=240)
                        if diar_resp.status_code < 400:
                            diar_diarization = diar_resp.json().get("diarization", []) or []
                        else:
                            diar_source = "fallback"
                    except Exception:
                        diar_source = "fallback"

                    if diar_source == "fallback" or not diar_diarization:
                        diar_diarization = self._alternative_diarization_from_stt(chunk_stt_segments, self.pause_threshold, start_with=fallback_starts_with)
                        diar_source = "stt_turn_fallback"
                        if diar_diarization:
                            fallback_starts_with = "002" if diar_diarization[-1].get("speaker") == "001" else "001"

                    all_aligned_segments.extend(
                        self._assign_speakers(chunk_stt_segments, diar_diarization, diar_source, chunk_offset=chunk_offset_seconds)
                    )
                    frames_read += to_read
                    chunk_index += 1

            except Exception as e:
                return f"Pipeline processing failed: {str(e)}", []

        else:
            # ── Direct path: non-WAV / video passthrough ──────────────────────────────
            # ffmpeg was unavailable in the container — send the original bytes straight
            # to WILLMA Whisper. The API handles MP4/MKV/MOV/AVI/WEBM/MP3/M4A natively.
            try:
                ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "bin"
                mime_type = self._MIME_MAP.get(ext, "application/octet-stream")

                stt_data = {
                    "model": stt_model_name, "language": self.language,
                    "stream": "false", "response_format": "verbose_json",
                    "timestamp_granularities[]": "segment"
                }
                stt_files = {"file": (filename, audio_bytes, mime_type)}
                stt_resp = requests.post(f"{self.base_url}/audio/transcriptions", headers=headers, files=stt_files, data=stt_data, timeout=600)
                stt_resp.raise_for_status()
                stt_segments = stt_resp.json().get("segments", []) or []

                diar_diarization = []
                diar_source = "api"
                try:
                    diar_files = {"file": (filename, audio_bytes, mime_type)}
                    diar_resp = requests.post(f"{self.base_url}/audio/custom-diarization", headers=headers, files=diar_files, data={"model": diar_model_name}, timeout=600)
                    if diar_resp.status_code < 400:
                        diar_diarization = diar_resp.json().get("diarization", []) or []
                    else:
                        diar_source = "fallback"
                except Exception:
                    diar_source = "fallback"

                if diar_source == "fallback" or not diar_diarization:
                    diar_diarization = self._alternative_diarization_from_stt(stt_segments, self.pause_threshold, start_with="001")
                    diar_source = "stt_turn_fallback"

                all_aligned_segments.extend(
                    self._assign_speakers(stt_segments, diar_diarization, diar_source, chunk_offset=0.0)
                )

            except Exception as e:
                return f"Pipeline processing failed: {str(e)}", []

        # ── Post-processing (shared by both paths) ────────────────────────────────────
        finalized = self._force_two_speaker_labels(all_aligned_segments)
        finalized = self._assign_unknown_by_neighbors(finalized)
        merged_conversation = self._merge_speaker_segments(finalized)

        string_script_blocks = []
        for segment in merged_conversation:
            start_min = f"{int(segment['start'] // 60)}m:{int(segment['start'] % 60):02d}s"
            speaker_tag = f"Speaker {segment['speaker']}" if segment['speaker'] != "UNKNOWN" else "Unknown Speaker"
            string_script_blocks.append(f"[{start_min}] {speaker_tag}:\n\"{segment['text'].strip()}\"")

        finalized_transcript_string = "\n\n".join(string_script_blocks)

        self._cached_result = (finalized_transcript_string, merged_conversation)
        return self._cached_result

    def get_chat_message(self) -> Message:
        text_script, _ = self.process_audio_pipeline()
        return Message(text=text_script or "Transcription returned empty.")

    def get_segments(self) -> list:
        _, raw_segments_list = self.process_audio_pipeline()
        return raw_segments_list
```

3. **Wire:** Preprocessor `cleaned_packet` → Transcriber `incoming_packet`.

**Required configuration:**

| Input | Type | Action required |
|-------|------|----------------|
| `api_key` | SecretStr | **Paste your WILLMA API key here** |
| `base_url` | Str | Default: `https://willma.surf.nl/api/v0` |
| `language` | Str | Default: `nl` (Dutch). Change to `en`, `de`, etc. as needed |

**Output wires:**
- `transcript_message` — dialogue script as a `Message`
- `segments_json` — list of structured segment dicts (for downstream analytics)

---

### Component 5 — Chat Output (built-in)

1. Search the sidebar for **Chat Output** and drag it onto the canvas.
2. **Wire:** Transcriber `transcript_message` → Chat Output `input_value`.

---

### 5b. Final wiring check

Your canvas should show this left-to-right chain:

```
Chat Input  →  Audio Downloader  →  Audio Preprocessor  →  Diarized Transcriber  →  Chat Output
```

Click **Build** (top-right) to validate all connections, then open **Playground** to run your first transcription.

---

## Configuration reference

### Audio Preprocessor

| Parameter | Default | Description |
|-----------|---------|-------------|
| `target_sample_rate` | 16 000 | Target Hz after resampling. Whisper is trained on 16 kHz mono. |
| `highpass_cutoff_hz` | 90 | First-order RC high-pass cutoff frequency in Hz. Removes DC offset, HVAC rumble. |
| `enable_drc` | `True` | Apply power-law dynamic range compression before normalization. |
| `peak_normalize` | 0.98 | Scale all samples so the loudest peak reaches this value (0.0–1.0). |

### WILLMA Whisper Diarized Transcriber

| Parameter | Default | Description |
|-----------|---------|-------------|
| `base_url` | `https://willma.surf.nl/api/v0` | WILLMA API base URL. |
| `api_key` | _(required)_ | Your WILLMA API key (stored encrypted in Langflow DB). |
| `language` | `nl` | BCP-47 language code passed to Whisper. |
| `chunk_seconds` | 30 | Size of each processing window in seconds. |
| `min_overlap_seconds` | 0.15 | Minimum time overlap (in seconds) between an STT segment and a diarization segment for speaker assignment. |
| `pause_threshold` | 1.2 | Pause gap (in seconds) used by the STT-turn fallback to detect speaker changes. |

---

## How two-speaker diarization works

The transcriber processes the audio in **30-second windows**. For each chunk it fires two parallel API requests:

```
chunk WAV bytes
    ├─► POST /audio/transcriptions     → word-level STT segments (start, end, text)
    └─► POST /audio/custom-diarization → speaker timeline [{start, end, speaker}, ...]
```

Speaker assignment uses an **overlap matrix**: for every STT segment, the transcriber computes the time overlap with every diarization segment and assigns the speaker with the highest overlap (provided it exceeds `min_overlap_seconds`). Segments with no sufficient overlap are labelled `UNKNOWN`.

If the diarization API is unavailable or returns empty results, a **STT-turn fallback** kicks in: STT segments separated by a pause ≥ `pause_threshold` seconds are treated as speaker changes, and speaker labels `001` / `002` are alternated.

After all chunks are processed, a three-stage **post-processing pipeline** cleans up the merged timeline:

1. **`_force_two_speaker_labels`** — collapses all detected speaker IDs to exactly `001` and `002` (by frequency rank).
2. **`_assign_unknown_by_neighbors`** — fills `UNKNOWN` segments by inheriting the speaker label from surrounding context.
3. **`_merge_speaker_segments`** — merges consecutive same-speaker segments separated by ≤ 1 second into single blocks.

Finally, the dialogue is formatted as:

```
[Xm:YYs] Speaker 001:
"..."

[Xm:YYs] Speaker 002:
"..."
```

The `segments_json` output exposes each segment's `start`, `end`, `text`, `speaker`, `speaker_source` (`api` or `stt_turn_fallback`), and `speaker_overlap` — useful for downstream quality analysis or export to JSON/CSV.

---

## Supported audio formats

### Accepted media types

Paste any of the following into the Langflow Chat Playground:

#### Video files
| Extension | Notes |
|-----------|-------|
| `.mp4` | Zoom recordings, phone captures, screen recordings — `moov`-at-end handled via `/tmp` temp file |
| `.mkv` | Matroska container |
| `.mov` | QuickTime — common on macOS/iOS |
| `.avi` | Legacy Windows video |
| `.webm` | Browser screen recordings, Google Meet exports |
| `.m4v` | iTunes-style MP4 variant |
| `.mpg` / `.mpeg` | MPEG-1/2 video |

> **V07 requirement:** Video extraction uses `ffmpeg`. Install it in the Docker container — see [Step 2f](#2f-install-ffmpeg-for-video-support-v07). Without ffmpeg the video bytes are forwarded unchanged to WILLMA Whisper (which handles common containers natively).

#### Audio files
| Extension | DSP treatment |
|-----------|---------------|
| `.wav` (16-bit PCM) | Full DSP pipeline: resample → 90 Hz highpass → DRC → peak normalize |
| `.wav` (other bit-depths) | ⏩ Passthrough — no DSP |
| `.mp3` | ⏩ Passthrough — Whisper handles natively |
| `.m4a` | ⏩ Passthrough — Whisper handles natively |
| `.flac` | ⏩ Passthrough — Whisper handles natively |
| `.ogg` | ⏩ Passthrough — Whisper handles natively |
| `.aac` | ⏩ Passthrough — Whisper handles natively |
| `.opus` | ⏩ Passthrough — Whisper handles natively |

### Accepted URL types

| URL pattern | How it is handled |
|-------------|-------------------|
| Direct download link (any extension above) | Streamed directly with `requests.get` |
| GitHub web viewer URL (`/blob/`) | Auto-rewritten to `raw.githubusercontent.com` |
| Nextcloud / ownCloud file viewer (`/apps/files/files/{id}`) | Auto-rewritten to `/index.php/f/{id}?download` |
| SURF Research Drive public share (`/s/{token}`) | Appended `/download`; no password needed |
| SURF Research Drive public share with password (`/s/{token}`) | Cookie-based 3-step auth — enter password in **Share Link Password** field |
| SURF Research Drive share + subfolder path (`/s/{token}/download?path=/file.mp4`) | Supported — path query string is preserved |

### Processing pipeline summary

| Format | Preprocessor action | Passed to Whisper |
|--------|-------------------|-------------------|
| **Video** (MP4, MKV, MOV, AVI, WEBM, M4V, MPG, MPEG) *(V07+)* | **ffmpeg audio extraction** → 16 kHz mono WAV → full DSP chain | ✅ |
| 16-bit PCM WAV | Full DSP pipeline (resample, filter, DRC, normalize) | ✅ |
| WAV with other bit-depth | ⏩ Passthrough (no DSP) | ✅ |
| MP3, M4A, FLAC, OGG, AAC, OPUS | ⏩ Passthrough (no DSP) | ✅ (Whisper handles natively) |

The DSP chain processes **16-bit PCM WAV** files (or WAV extracted by ffmpeg from a video container). All other formats are forwarded unchanged — Whisper large-v3 handles them natively server-side.

> **V07 Docker requirement:** Add `RUN apt-get update && apt-get install -y ffmpeg` to the Dockerfile for video support (see [Step 2f](#2f-install-ffmpeg-for-video-support-v07)). Without ffmpeg, video files are forwarded unchanged to WILLMA Whisper, bypassing the DSP step.

---

## Troubleshooting

### "INVALID_URL" in Chat Output
The URL you pasted either does not start with `http://`/`https://` or the field was empty. Paste a direct download link to an audio file.

### "DOWNLOAD_FAILED" in Chat Output
The HTTP GET to the audio URL failed (timeout, 4xx/5xx, DNS error). Verify the URL is publicly accessible. GitHub repository files must use the raw URL (`raw.githubusercontent.com`), not the HTML viewer URL — the downloader rewrites `/blob/` automatically but `/tree/` links are not supported.

### "AUTH_REQUIRED" in Chat Output *(V07+)*
The server returned an HTML page instead of the file. Causes and fixes:

- **Password-protected SURF Research Drive link:** Enter the share password in the **Share Link Password** field (`SecretStr`, padlock icon) of the WILLMA Audio Downloader component.
- **Wrong password:** The share page was returned (wrong password → HTML → `AUTH_REQUIRED`). Re-check the password and re-enter it.
- **Internal / login-gated link:** The URL requires a personal SURF login. Create a new public share link in SURF Research Drive (right-click the **file** → Share → New share link → set or omit password → Copy link).
- **Folder URL instead of file URL:** Append the filename to the share download URL: `https://hr.data.surf.nl/s/<token>/download?path=/filename.mp4`

### Transcription returns empty / very short text
- The audio file may be silent, corrupt, or the wrong format.
- Check that `language` is set to the correct BCP-47 code (e.g. `nl` for Dutch, `en` for English).
- Try with `whisper-large-v3` explicitly set in `base_url` sequence resolution.

### Diarization fallback always active (`speaker_source: stt_turn_fallback`)
The pyannote endpoint (`/audio/custom-diarization`) may be temporarily unavailable or overloaded on the WILLMA platform. The STT-turn fallback still produces a reasonable two-speaker split. Check SURF Servicedesk for any reported outages.

### Langflow `SystemError: (11, 'Resource temporarily unavailable')`
Add `ulimits` to the Langflow service in `docker-compose.yaml` (see Step 2e above) and restart the stack.

### Let's Encrypt certificate not issued
- Ensure ports 80 and 443 are open in the SRC firewall/security group.
- Ensure Nginx is stopped (`sudo systemctl stop nginx && sudo systemctl disable nginx`).
- The `create-langflow.sh` script handles this automatically.

### API rate limits / 429 responses
WILLMA enforces per-key rate limits. For long audio files (> 30 minutes), consider reducing concurrency or adding a short `time.sleep` between chunks in the transcriber code.

### Video file not processed / "No input audio data detected." *(V07+)*
- Verify that `ffmpeg` is installed in the Langflow container: `docker exec langflow ffmpeg -version`.
- If ffmpeg is missing, the Preprocessor forwards raw video bytes to the Transcriber, which probes them as a WAV — the probe fails → bytes treated as empty → "No input audio data detected."
- Fix: add `ffmpeg` to the Dockerfile (see [Step 2f](#2f-install-ffmpeg-for-video-support-v07)) and rebuild: `docker compose up -d --build`.
- Alternatively, pre-convert the video to WAV/MP3 and paste a direct audio URL.

---

## Security notes

- **API key storage:** Always use Langflow's **SecretStr** input (padlock icon). Values are stored encrypted in PostgreSQL and never exposed in the Langflow UI or logs.
- **HTTPS only:** The Docker stack enforces HTTP→HTTPS redirect via Traefik. Never run Langflow over plain HTTP in production.
- **No data leaves SURF:** All model inference runs on SURF infrastructure. Audio files are downloaded to the SRC VM RAM and streamed to WILLMA endpoints — they are never forwarded to third-party cloud providers.
- **SRAM authentication:** The SRC VM itself is protected by SRAM (SURF Research Access Management), which federates institutional identity providers via SAML/OIDC.
- **Change the default secret key:** In `docker-compose.yaml`, replace `LANGFLOW_SECRET_KEY=alongrandomstringhereforsecurity` with a strong random string before going to production.

---

## License

This project is released under the [Creative Commons BY-ND 4.0](https://creativecommons.org/licenses/by-nd/4.0/legalcode.nl) licence, consistent with the HR AI-HUB Pilot programme.

**Developed by:** HR DataLab Healthcare · [SURF AI-Hub Pilot Programme 2025–2026](https://hr-ai-hub.github.io/)  
**Tech lead:** RFvdW · **DataLab coordinator:** Alfons Looman  
**Institution:** [Hogeschool Rotterdam](https://www.hogeschoolrotterdam.nl) · In collaboration with [SURF](https://www.surf.nl) & [Npuls](https://www.surf.nl/themas/artificial-intelligence/projecten-en-samenwerkingen/ai-hub)

---

## Quick reference — WILLMA API endpoints used

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/sequences` | GET | Discover available model names (model resolution) |
| `/audio/transcriptions` | POST | Whisper STT — `verbose_json` + segment timestamps |
| `/audio/custom-diarization` | POST | pyannote/speaker-diarization-3.1 speaker timeline |

All requests use header `X-API-KEY: <your-api-key>` and base URL `https://willma.surf.nl/api/v0`.

---

## Changelog

### V07 — Video Support + Authenticated Share Links *(current)*

Based on `LANGFLOW_WILLMA_WHISPER_TRANSCRIBER_V06.ipynb`. Documented in `LANGFLOW_WILLMA_WHISPER_TRANSCRIBER_V07.ipynb`.

#### What changed

| Area | Change |
|------|--------|
| **Video file support** | Component 2 (Audio Preprocessor) detects video containers (`.mp4` `.mkv` `.mov` `.avi` `.webm` `.m4v` `.mpg` `.mpeg`) by file extension and calls `ffmpeg` to extract the audio track before the DSP chain runs |
| **ffmpeg temp-file strategy** | Video bytes are written to a named `/tmp` temp file; ffmpeg reads from disk (not stdin pipe), which is required for moov-at-end MP4s (Zoom recordings, phone captures, screen recordings) |
| **Resilient ffmpeg fallback** | If `ffmpeg` is not installed or exits non-zero, the original bytes are forwarded unchanged — the flow never breaks |
| **Password-protected share links** | Component 1 (Audio Downloader) accepts a new **Share Link Password** (`SecretStr`) field for password-protected Nextcloud / ownCloud / SURF Research Drive public share links |
| **Cookie-based session auth** | Replaces HTTP Basic Auth (which ownCloud/Nextcloud ignores for public shares); mirrors browser flow: GET share page → extract CSRF `requesttoken` from HTML → POST password to `/authenticate/downloadshare` → session cookie → GET download URL |
| **Nextcloud file viewer URL rewriting** | `/apps/files/files/{id}?dir=...` viewer URLs are rewritten to `/index.php/f/{id}?download` |
| **`AUTH_REQUIRED` error code** | Downloader returns `AUTH_REQUIRED` when the server returns HTML (wrong/missing password or login-gated link); HTTP 401/403 also maps to `AUTH_REQUIRED`; the Preprocessor propagates the code unchanged |
| **Content-Disposition filename** | Downloader prefers the `Content-Disposition: attachment; filename=...` response header over the URL path basename |
| **Actionable transcriber message** | Transcriber surfaces a detailed Option A/B/C guide when it receives `AUTH_REQUIRED` instead of audio bytes |
| **Non-WAV direct path in transcriber** | Transcriber probes received bytes as a WAV container; if not valid WAV, bytes are sent to WILLMA Whisper as-is without chunking (handles ffmpeg-unavailable passthrough and native non-WAV formats) |
| **Docker: `ffmpeg` required for video** | `RUN apt-get update && apt-get install -y ffmpeg` must be added to the Dockerfile and the image rebuilt (see [Step 2f](#2f-install-ffmpeg-for-video-support-v07)) |

#### Component cells in the V07 notebook

| Component | V06 notebook | V07 notebook |
|-----------|-------------|-------------|
| 1. WILLMA Audio Downloader | cell 4 | **cell 6** |
| 2. Audio Preprocessor | cell 7 | **cell 8** |
| 3. WILLMA Whisper Diarized Transcriber | cell 9 | **cell 10** |

#### Migration from V06 → V07

1. Add `ffmpeg` to the Dockerfile (see [Step 2f](#2f-install-ffmpeg-for-video-support-v07)) and rebuild: `docker compose up -d --build`
2. In Langflow, open the flow and update **1. WILLMA Audio Downloader** with **cell 6** from `LANGFLOW_WILLMA_WHISPER_TRANSCRIBER_V07.ipynb`.
3. Update **2. Audio Preprocessor** with **cell 8**.
4. Update **3. WILLMA Whisper Diarized Transcriber** with **cell 10**.
5. If you use password-protected SURF Research Drive share links, enter the share password in the new **Share Link Password** field of the Audio Downloader component.

---

### V06 — Stable Baseline *(prior version)*

Two-speaker diarization, WAV/MP3 audio support, public URL downloads, pure-Python DSP.  
Documented in `LANGFLOW_WILLMA_WHISPER_TRANSCRIBER_V06.ipynb`. Ready-to-import flow: `URL PREPRO TRANSCR  + TIME + DIARIZATION.json`.

---
