# Whisper v3 Two-Speaker Diarized Transcription with SURF AI-HUB + Langflow

> **Platform:** [SURF AI-HUB (WiLLMa)](https://hr-ai-hub.github.io/) · [SURF Research Cloud](https://www.surf.nl/en/surf-research-cloud-collaborative-research-environment) · [Langflow 1.9.3](https://langflow.org/) · Docker · Ubuntu 22.04  
> **Repository:** [HR-DataLab-Healthcare / RESEARCH\_SUPPORT — SRAM\_DOCKER\_LANGFLOW](https://github.com/HR-DataLab-Healthcare/RESEARCH_SUPPORT/tree/main/PROJECTS/SRAM_DOCKER_LANGFLOW)  
> **Notebook:** `LANGFLOW_WILLMA_WHISPER_TRANSCRIBER_V07.ipynb` (current) · `LANGFLOW_WILLMA_WHISPER_TRANSCRIBER_V06.ipynb` (V06 baseline)  
> **Ready-to-import flow:** `URL PREPRO TRANSCR  + TIME + DIARIZATION.json`

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
11. [Supported audio formats](#supported-audio-formats)
12. [Troubleshooting](#troubleshooting)
13. [Security notes](#security-notes)
14. [License](#license)
15. [Changelog](#changelog)

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

## What this tool does

This Langflow flow accepts a **public audio or video file URL** (pasted into the Langflow Chat Playground), downloads the file into memory, optionally extracts audio from video containers via `ffmpeg`, cleans it with a **pure-Python DSP chain**, and sends it to the **SURF WILLMA Whisper API** for transcription and **two-speaker diarization**.

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
     │  (audio URL as text)
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
| Audio files accessible by URL | Public HTTP/HTTPS links, or GitHub raw file URLs |

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

1. Copy `URL PREPRO TRANSCR  + TIME + DIARIZATION.json` to a location accessible from your browser.
2. In Langflow, click **My Flows → Import** (the upload icon, top-right of the flows list).
3. Select the JSON file and confirm.
4. Open the imported flow. You will see all 5 components already connected.
5. Click the **3. WILLMA Whisper Diarized Transcriber** component, navigate to the **WILLMA API Key** field (padlock icon), and enter your API key.
6. Click **Playground** (top-right) and paste an audio URL to test.

---

## Step 5 — Build the flow from scratch (component by component)

This section documents the **V06 baseline** component code. For the **V07 update** (video support + authenticated share links), replace each component's code with the corresponding cell from `LANGFLOW_WILLMA_WHISPER_TRANSCRIBER_V07.ipynb`:

| Component | V06 notebook cell | V07 notebook cell |
|-----------|-------------------|-------------------|
| 1. WILLMA Audio Downloader | cell 4 | **cell 6** |
| 2. Audio Preprocessor | cell 7 | **cell 8** |
| 3. WILLMA Whisper Diarized Transcriber | cell 9 | **cell 10** |

### 5a. Create a new flow

In Langflow, click **New Flow → Blank Flow**. Name it `WILLMA Whisper V06`.

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
import requests
import os
from langflow.custom import Component
from langflow.inputs import MessageInput
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
        )
    ]

    outputs = [
        Output(name="audio_packet", display_name="Audio Packet Data", method="download_to_memory")
    ]

    def download_to_memory(self) -> Data:
        message_obj = self.chat_message
        url_target = ""

        if message_obj and hasattr(message_obj, "text") and message_obj.text:
            url_target = str(message_obj.text).strip()

        if not url_target or not url_target.startswith(("http://", "https://")):
            return Data(text="INVALID_URL", data={"bytes": None, "filename": "audio.mp3"})

        # Rewrite GitHub web URLs to raw.githubusercontent.com
        if "github.com" in url_target and "/blob/" in url_target:
            url_target = url_target.replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/")
        elif "github.com" in url_target and "/raw/" in url_target:
            url_target = url_target.replace("github.com", "raw.githubusercontent.com").replace("/raw/", "/")

        try:
            response = requests.get(url_target, timeout=120)
            response.raise_for_status()
            audio_bytes = response.content

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
        except Exception:
            return Data(text="DOWNLOAD_FAILED", data={"bytes": None, "filename": "audio.mp3"})
```

3. **Wire:** connect Chat Input `message` → Downloader `chat_message`.

**Output wire:** `audio_packet` (Audio Packet Data)

> **V07 update:** The V07 Audio Downloader adds a **Share Link Password** (`SecretStr`) field and cookie-based session authentication for password-protected SURF Research Drive share links. Use **cell 6** from `LANGFLOW_WILLMA_WHISPER_TRANSCRIBER_V07.ipynb` for the full V07 code.

---

### Component 3 — Audio Preprocessor (Pure Python / Stdlib-only)

1. Create another **Custom Component**.
2. Paste the full `AudioPreprocessorComponent` code from notebook cell 7 (lines 227–370).  
   Key class signature:

```python
class AudioPreprocessorComponent(Component):
    display_name = "2. Audio Preprocessor"
    description = "Cleans WAV audio: stereo→mono, resampling, high-pass filter, DRC, peak normalization."
    # ... (see notebook cell 7 for full code)
```

   Key parameters (all have sensible defaults):

   | Input | Default | Effect |
   |-------|---------|--------|
   | `target_sample_rate` | 16 000 Hz | Resamples to Whisper's native rate |
   | `highpass_cutoff_hz` | 90 Hz | Removes DC offset and low-frequency rumble |
   | `enable_drc` | `True` | Power-law soft compression (`\|s\|^0.88`) |
   | `peak_normalize` | 0.98 | Peak amplitude target (avoids clipping) |

3. **Wire:** Downloader `audio_packet` → Preprocessor `incoming_packet`.

**Output wire:** `processed_packet` (Processed Audio Data)

> **Why stdlib-only?** The Langflow Docker container may not have scipy or numpy available without modifying the image. The preprocessor uses only `wave`, `struct`, and `math` — zero extra dependencies.

> **V07 update:** The V07 Preprocessor adds video audio extraction via `ffmpeg` subprocess, writing a `/tmp` temp file for full random-access seeking (required for moov-at-end MP4s). Use **cell 8** from `LANGFLOW_WILLMA_WHISPER_TRANSCRIBER_V07.ipynb` for the full V07 code. Requires `ffmpeg` in the Docker image (see [Step 2f](#2f-install-ffmpeg-for-video-support-v07)).

---

### Component 4 — WILLMA Whisper Diarized Transcriber

1. Create another **Custom Component**.
2. Paste the `WillmaWhisperTranscriber` code from notebook cell 9 (lines 404–723).  
   Class signature:

```python
class WillmaWhisperTranscriber(Component):
    display_name = "3. WILLMA Whisper Diarized Transcriber"
    description = "Transcribes and diarizes audio into a timestamped two-speaker dialogue script."
```

   **Required configuration:**

   | Input | Type | Action required |
   |-------|------|----------------|
   | `api_key` | SecretStr | **Paste your WILLMA API key here** |
   | `base_url` | Str | Default: `https://willma.surf.nl/api/v0` |
   | `language` | Str | Default: `nl` (Dutch). Change to `en`, `de`, etc. as needed |

   **Tunable parameters:**

   | Parameter | Default | Notes |
   |-----------|---------|-------|
   | `chunk_seconds` | 30 s | STT + diarization window size per API call |
   | `min_overlap_seconds` | 0.15 s | Minimum speaker-segment overlap to assign a speaker label |
   | `pause_threshold` | 1.2 s | Pause gap used by the STT-turn fallback diarizer |

3. **Wire:** Preprocessor `processed_packet` → Transcriber `incoming_packet`.

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

| Format | Preprocessor action | Passed to Whisper |
|--------|-------------------|-------------------|
| **MP4, MKV, MOV, AVI, WEBM, M4V, MPG, MPEG** *(V07+)* | **ffmpeg audio extraction** → 16 kHz mono WAV → full DSP chain | ✅ |
| 16-bit PCM WAV | Full DSP pipeline (resample, filter, DRC, normalize) | ✅ |
| WAV with other bit-depth | ⏩ Passthrough (no DSP) | ✅ |
| MP3, M4A, FLAC, OGG | ⏩ Passthrough (no DSP) | ✅ (Whisper handles natively) |

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
