# RCLONE V01 — SURF Research Drive shared-link access

Connect a SURF Research Drive public shared folder to the Docker-hosted code-server notebook workspace. Download selected recordings locally, then process them using `WILLMA_WHISPER_TRANSCRIBER_V05d.ipynb`.

Version: V01 — 22 November 2026.

## Scope and validation status

This guide targets your existing configuration:

- Browser editor: `https://visualstudio.cyber-secure-te.src.surf-hosted.nl`
- Browser-terminal user: `abc`
- Persistent container home: `/config`
- Workspace: `/config/workspace`
- Conda environment: `/config/miniforge3/envs/transcription-env`
- Research Drive share: `https://hr.data.surf.nl/s/wZnZMSicNGAcTjq`

Run commands in the browser editor terminal, not the host VM's SSH session. No `sudo`, FUSE mount, privileged container, or Docker Compose change is needed for this download-based workflow.

The target share could not be retrieved during preparation. Its current availability, password, expiry, permissions, contents, and successful WebDAV access are not verified. The connection mapping below follows SURF's documented programmatic public-link access; verify it with a listing before downloading data.

This is an independent implementation guide, not a verified reproduction of scripts in the referenced GitHub RCLONE directory.

## Contents

1. [Architecture](#1-architecture)
2. [Install dependencies](#2-install-dependencies)
3. [Configure the existing .env](#3-configure-the-existing-env)
4. [Create the Research Drive helper](#4-create-the-research-drive-helper)
5. [List and download from the notebook](#5-list-and-download-from-the-notebook)
6. [Connect the WILLMA transcriber](#6-connect-the-willma-transcriber)
7. [Troubleshooting](#7-troubleshooting)
8. [Security and operational limits](#8-security-and-operational-limits)

## 1. Architecture

```text
SURF Research Drive shared folder
    |
    | HTTPS / WebDAV; rclone copy downloads files
    v
/config/workspace/rd_input/<selected-folder>/
    |
    | local paths supplied to the notebook
    v
WILLMA Whisper Transcriber notebook
    |
    | uploads media to WILLMA using a separate API key
    v
/config/workspace/transcription_outputs/
```

This is a download/staging workflow, not a mounted remote filesystem or a live synchronization service. New files in Research Drive require another explicit download operation.

### Shared-link credential mapping

| Setting | Value |
|---|---|
| Backend | `webdav` |
| URL | `https://hr.data.surf.nl/public.php/webdav/` |
| Vendor | `other` |
| Username | The token after `/s/` in `RD_URL` |
| Password | The password belonging to the share |

For your URL, the username token is `wZnZMSicNGAcTjq`; it is not your institutional username. Do not use the browser `/s/TOKEN` page as the WebDAV endpoint. An account's `/remote.php/...` endpoint is also not the public-link endpoint documented here.

SURF specifically recommends vendor `other` for this public-link URL pattern. Do not change vendors at random to solve an authentication failure.

## 2. Install dependencies

In the browser editor terminal:

```bash
source /config/miniforge3/etc/profile.d/conda.sh
conda activate transcription-env
conda install --override-channels -c conda-forge rclone python-dotenv -y
rclone version
python -c "from dotenv import dotenv_values; print('python-dotenv import OK')"
```

Add these entries to the existing `dependencies:` list in `/config/workspace/environment.yml`:

```yaml
  - rclone
  - python-dotenv
```

Do not replace your existing environment file or remove the transcription dependencies. These two additions provide the rclone executable and a proper dotenv parser.

After installation, restart the notebook kernel and select **Python (transcription-env)**. Check the interpreter from a notebook cell:

```python
import sys
print(sys.executable)
assert sys.executable == "/config/miniforge3/envs/transcription-env/bin/python"
```

## 3. Configure the existing .env

Open `/config/workspace/.env` in the editor. Preserve all existing unrelated values and add or update these two lines:

```dotenv
RD_URL=https://hr.data.surf.nl/s/wZnZMSicNGAcTjq
RD_PASSWORD=
```

If the share requires a password, enter it as a dotenv value, using quotes where needed:

```dotenv
RD_PASSWORD='replace-with-the-actual-share-password'
```

The empty value is valid only when the share does not require a password. Never paste the real password into notebook code, chat, screenshots, or shell commands.

The helper uses `dotenv_values(..., interpolate=False)`, so `$` sequences in passwords are not expanded as dotenv variable references. Follow python-dotenv quoting rules for unusual passwords containing quotes or backslashes.

Protect the file in the terminal:

```bash
chmod 600 /config/workspace/.env
```

Add the following entries to your project's `.gitignore`, preserving existing entries:

```gitignore
.env
.env.*
!.env.example
rd_input/
transcription_outputs/
.ipynb_checkpoints/
```

A `.gitignore` entry does not remove secrets that were already committed. Revoke/rotate exposed secrets and remove them from repository history as appropriate.

The Research Drive share password is separate from the WILLMA API key and from the code-server browser login password.

## 4. Create the Research Drive helper

Create `/config/workspace/research_drive.py` in the editor. Paste only the following Python code and save it. Do not paste Markdown fences into the actual file.

```python
"""Read-only Research Drive listing and download helpers for notebooks."""
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote, urlparse

from dotenv import dotenv_values

class ResearchDrive:
    def __init__(self, env_file="/config/workspace/.env"):
        self.env_file = Path(env_file)
        cfg = dotenv_values(self.env_file, interpolate=False)
        parsed = urlparse((cfg.get("RD_URL") or "").strip())
        parts = parsed.path.strip("/").split("/")
        if (parsed.scheme != "https" or parsed.netloc != "hr.data.surf.nl"
                or len(parts) != 2 or parts[0] != "s"
                or not re.fullmatch(r"[A-Za-z0-9_-]+", parts[1])):
            raise ValueError("RD_URL must be an https://hr.data.surf.nl/s/TOKEN link")
        token = parts[1]
        self.binary = Path(sys.executable).parent / "rclone"
        if not self.binary.is_file():
            found = shutil.which("rclone")
            if not found:
                raise RuntimeError("Install rclone in the active notebook environment")
            self.binary = Path(found)

        # Isolate this remote from inherited rclone settings and stored config.
        self.env = {k: v for k, v in os.environ.items()
                    if not k.upper().startswith("RCLONE_")}
        self.env.update({
            "RCLONE_CONFIG_RDSHARE_TYPE": "webdav",
            "RCLONE_CONFIG_RDSHARE_URL": "https://hr.data.surf.nl/public.php/webdav/",
            "RCLONE_CONFIG_RDSHARE_VENDOR": "other",
            "RCLONE_CONFIG_RDSHARE_USER": token,
            "RCLONE_CONFIG_RDSHARE_PASS": "",
        })
        password = cfg.get("RD_PASSWORD") or ""
        if password:
            obscured = subprocess.run(
                [str(self.binary), "obscure", "-"],
                input=password, capture_output=True, text=True,
                check=True, timeout=30, env=self.env,
            ).stdout.strip()
            self.env["RCLONE_CONFIG_RDSHARE_PASS"] = obscured

    @staticmethod
    def _remote(folder=""):
        if not folder:
            return "RDSHARE:"
        if (folder.startswith("/") or "\\" in folder
                or any(part in (".", "..") for part in folder.split("/"))):
            raise ValueError("Use a relative folder path without . or .. segments")
        return "RDSHARE:" + folder.rstrip("/")

    def _run(self, args):
        command = [str(self.binary), "--config", os.devnull,
                   "--contimeout", "20s", "--timeout", "5m",
                   "--retries", "2", *args]
        result = subprocess.run(
            command, env=self.env, capture_output=True,
            text=True, timeout=3600,
        )
        if result.returncode:
            raise RuntimeError(
                f"rclone failed with exit code {result.returncode}. "
                "Inspect details privately; paths may contain personal data.\n"
                + result.stderr[-4000:]
            )
        return result.stdout + result.stderr

    def list(self, folder="", max_depth=1):
        return self._run([
            "lsf", self._remote(folder), "--max-depth", str(max_depth)
        ])

    def download(self, destination, folder="", dry_run=True):
        destination = Path(destination).expanduser().resolve()
        destination.mkdir(parents=True, exist_ok=True)
        args = ["copy", self._remote(folder), str(destination),
                "--transfers", "2", "--checkers", "4", "--stats", "30s"]
        if dry_run:
            args += ["--dry-run", "-v"]
        return self._run(args)
```

### What the helper does

- Reads the specific `.env` path; it does not depend on your notebook's current directory.
- Validates that the share belongs to `https://hr.data.surf.nl` before sending credentials.
- Derives the share token from `RD_URL` rather than hard-coding the username.
- Uses an environment-defined remote called `RDSHARE`.
- Uses an empty config source to avoid loading unrelated stored remotes.
- Sends the password to `rclone obscure` through standard input, not a command-line argument.
- Keeps the remote configuration in the child-process environment; it does not create `rclone.conf`.
- Offers listing and remote-to-local copying only. No upload, deletion, mount, or sync helper is provided.

Rclone requires its WebDAV `pass` setting to use the obscured representation. Obscuring is reversible and is not strong encryption; protect the process environment and `.env` accordingly.

Do not print `rd.env`: it contains remote credentials. Avoid displaying raw exception output in a notebook you plan to publish, because remote filenames and paths can be sensitive.

## 5. List and download from the notebook

Use separate cells for listing, planning, and downloading. This prevents accidentally starting a large transfer while merely checking connectivity.

### 5.1 Import and connect

Add this near the beginning of `WILLMA_WHISPER_TRANSCRIBER_V05d.ipynb`:

```python
import sys
from pathlib import Path

WORKSPACE = Path("/config/workspace")
if str(WORKSPACE) not in sys.path:
    sys.path.insert(0, str(WORKSPACE))

from research_drive import ResearchDrive

rd = ResearchDrive(WORKSPACE / ".env")
print("Research Drive helper initialized; connectivity not yet tested.")
```

Initialization only prepares configuration. It does not prove access.

### 5.2 List the share root

```python
print(rd.list())
```

The default lists the top-level contents. To inspect a selected subfolder:

```python
print(rd.list(folder="relative/subfolder", max_depth=1))
```

Replace `relative/subfolder` with an actual folder shown by the listing. A successful listing confirms directory-list permission, but not necessarily download permission for every item.

The helper is designed for a folder share. If the link points to a single file or an upload-only/file-drop share, do not assume this folder-listing workflow applies. Ask the owner for a downloadable folder share if necessary.

### 5.3 Select the source and local target

```python
# Empty string selects the root of the shared folder.
# Prefer a small, explicitly selected subfolder for the first test.
REMOTE_FOLDER = ""
LOCAL_INPUT = Path("/config/workspace/rd_input/selected")
```

Do not include the share token in `REMOTE_FOLDER`. It is a path relative to the shared folder, such as `interviews/session01`.

### 5.4 Preview the download

```python
print(rd.download(LOCAL_INPUT, folder=REMOTE_FOLDER, dry_run=True))
```

This creates the local target directory and previews the transfer; it does not transfer file contents. Review the planned files and check available space before downloading:

```python
import shutil
free_gib = shutil.disk_usage("/config/workspace").free / (1024 ** 3)
print(f"Free local disk space: {free_gib:.1f} GiB")
```

Allow additional space for extracted WAV files and transcript outputs. WAV extraction can be larger than the original compressed media.

### 5.5 Download explicitly

```python
print(rd.download(LOCAL_INPUT, folder=REMOTE_FOLDER, dry_run=False))
```

This is `rclone copy`, not `sync`:

- It downloads remote contents and preserves relative subdirectories.
- It does not delete extra local files.
- It can replace a local file that rclone determines needs updating; it is not an immutable archive or versioned backup.
- It does not write to or modify the source share.

Use a distinct local target per dataset to avoid mixing unrelated shares. Do not put transcript output inside the remote-derived input tree.

The helper captures output until the command ends; the cell may appear quiet during large downloads. It limits a call to one hour and raises an exception on nonzero exit status. A failed transfer can leave already-downloaded files in place. Review the error privately and rerun only after resolving the cause; do not assume that the entire dataset is ready after failure.

## 6. Connect the WILLMA transcriber

The notebook uses local `Path` objects. Rclone stages the files locally; no changes to its HTTP transcription functions are required just to supply those files.

### 6.1 Replace the original Windows path block

Before the notebook's `CONFIG` dictionary is constructed, use:

```python
from pathlib import Path

NOTEBOOK_PATH = Path(
    "/config/workspace/WILLMA_WHISPER_TRANSCRIBER_V05d.ipynb"
)
DEFAULT_INPUT_FOLDER = Path("/config/workspace/rd_input/selected")
DEFAULT_OUTPUT_FOLDER = Path("/config/workspace/transcription_outputs/selected")
DEFAULT_CLEANED_FOLDER = DEFAULT_OUTPUT_FOLDER / "cleaned_audio"
DEFAULT_LOG_FOLDER = DEFAULT_OUTPUT_FOLDER / "logs"
DEFAULT_PROGRESS_FILE = DEFAULT_LOG_FOLDER / "batch_progress.json"
DEFAULT_REFERENCE_FOLDER = DEFAULT_OUTPUT_FOLDER / "references"

for folder in (
    DEFAULT_OUTPUT_FOLDER, DEFAULT_CLEANED_FOLDER,
    DEFAULT_LOG_FOLDER, DEFAULT_REFERENCE_FOLDER,
):
    folder.mkdir(parents=True, exist_ok=True)
```

Remove original Windows path assignments that would overwrite these values. Update the path each time you choose a different local download target.

If `CONFIG` already exists in your running kernel, rerun the adapted setup cell so it is rebuilt with the new paths. This also restores any hard-coded configuration in that cell; set your rotated WILLMA key securely afterwards, before API calls.

### 6.2 Important: nested folders

The notebook's main discovery helper searches one directory level using `folder.glob("*")`. Rclone copies recursively and preserves subdirectories.

Consequently, files under `selected/interviews/...` will not be found by a scan of `selected/`. Either:

1. Download a chosen remote folder whose media are directly inside it; or
2. Point `DEFAULT_INPUT_FOLDER` at the exact downloaded leaf folder.

Do not flatten multiple directories blindly. Different folders can contain identical filenames, and the notebook uses source stems for naming outputs. Even distinct files with the same stem but different extensions can collide in a shared output directory. Use separate batch/output folders where needed.

### 6.3 Verify the kernel's tools

Run before transcription:

```python
import os
import shutil
import sys
from pathlib import Path

os.environ["PATH"] = (
    str(Path(sys.executable).parent)
    + os.pathsep + os.environ.get("PATH", "")
)
assert shutil.which("ffmpeg"), "FFmpeg is not on the kernel PATH"
assert DEFAULT_INPUT_FOLDER.is_dir(), "Input folder does not exist"

media = [p for p in DEFAULT_INPUT_FOLDER.iterdir() if p.is_file()]
print("Files directly inside input folder:", len(media))
```

Then run the notebook's main functions, discovery diagnostics, and batch workflow. Use a short non-sensitive recording first. A successful rclone download does not demonstrate that WILLMA credentials, model selection, or transcription are working.

The later standalone notebook examples use independent paths/settings and redefine functions. Do not run all cells blindly after the batch workflow.

### 6.4 Existing CONFIG and an optional secure key prompt

After running the main setup cell, obtain the separate WILLMA key without embedding it in the notebook:

```python
from getpass import getpass
CONFIG["willma_api_key"] = getpass("WILLMA API key: ").strip()
```

Do not use `RD_PASSWORD` as a WILLMA API key. Remove/rotate API-key values embedded in shared notebook source.

## 7. Troubleshooting

### `rclone` or `dotenv` is missing

Confirm the kernel interpreter:

```python
import sys
print(sys.executable)
```

Expected:

```text
/config/miniforge3/envs/transcription-env/bin/python
```

Install packages into that environment, restart the kernel, and rerun initialization.

### 401 Unauthorized

Check privately:

- Whether the share requires a password.
- Whether `.env` contains the current password with correct quoting.
- Whether the share has expired or been revoked.
- Whether `RD_URL` points to the intended share.

After changing `.env`, create a new helper instance:

```python
rd = ResearchDrive("/config/workspace/.env")
```

The object caches its settings; changing the file does not update an existing instance automatically. Do not print credential dictionaries.

### 403 Forbidden or listing works but downloads fail

The share may not permit the requested operation, may be upload-only, or may have downloads restricted. Confirm permissions with the owner. Do not attempt to bypass download restrictions.

### 404 Not Found or unexpected HTML response

Confirm that the URL/token are correct and that you are using the public-link WebDAV endpoint, not the browser share page. The baseline in this guide is SURF's documented `/public.php/webdav/` endpoint.

Server versions can expose different public-DAV paths. A 404 alone does not establish which alternative path or authentication scheme is correct. Verify the tenant's supported endpoint with its current documentation or administrator before changing the helper. Do not enable cross-domain credential forwarding or disable TLS verification as a shortcut.

### The remote is empty

Verify whether it is a folder share with listing permission, whether you chose the correct relative folder, and whether the files are nested deeper. An upload-only share is not a readable media source.

### Read timeout or transfer failure

Check network connectivity, available disk space, and share validity. The helper uses limited retries and a one-hour process timeout. It is reasonable to adjust timeout values deliberately for authorized large datasets, but do not run repeated unbounded retries against a failing service.

### No files found by the transcription notebook

Check `CONFIG["input_folder"]`, the download destination, the one-level discovery behavior, supported extensions, and whether old Windows assignments remain. Do not reinstall Conda to fix a path mismatch.

### Sharing diagnostic output

Do not share `.env`, `rd.env`, authorization headers, or verbose HTTP dumps. Filenames, output cells, and errors can reveal participant identities or project details. Redact paths and clear sensitive notebook outputs before publishing.

## 8. Security and operational limits

- Treat the share token as a credential. Without a password, possession of the link may be sufficient for access.
- This guide repeats the user-provided token for configuration clarity. Use a placeholder in public documentation and rotate/revoke the link if its exposure is inappropriate.
- Passwords remain in `.env` and in the helper's process memory. Environment-based configuration avoids a new config file but is not a secret vault.
- Do not disable HTTPS certificate verification.
- Rclone's obscured password is reversible, not a strong encryption boundary.
- Only download data you are authorized to stage on the SRC VM.
- Confirm consent and data-processing arrangements cover both local staging and upload to WILLMA.
- Keep access-controlled backups outside the VM and apply the project's retention/deletion policy to staged recordings.
- Uploading transcript outputs back to Research Drive is intentionally outside this read-only workflow. Confirm write permissions and review target paths before designing a separate upload step.
- SURF warns that writes through read-only public links can fail silently; verify uploaded files independently if uploads are added later.

## References

- [SURF: Programmatic access to Research Drive](https://servicedesk.surf.nl/wiki/spaces/WIKI/pages/102827595/Programmatic+access+to+Research+Drive)
- [SURF: Public-link sharing](https://servicedesk.surf.nl/wiki/spaces/WIKI/pages/126222580/RD+How+to+share+via+a+public+link)
- [SURF: Rclone and Research Drive](https://servicedesk.surf.nl/wiki/spaces/WIKI/pages/117179081/RD+How+to+use+Rclone+with+Research+Drive)
- [Rclone WebDAV backend](https://rclone.org/webdav/)
- [Rclone environment-defined remotes](https://rclone.org/docs/#config-config-file)
- [Rclone copy](https://rclone.org/commands/rclone_copy/)
- [Rclone obscure](https://rclone.org/commands/rclone_obscure/)
- [python-dotenv documentation](https://bbc2.github.io/python-dotenv/)
- [User-provided GitHub reference directory](https://github.com/HR-DataLab-Healthcare/RESEARCH_SUPPORT/tree/main/PROJECTS/RCLONE)

## Completion checklist

- [ ] Correct notebook kernel selected.
- [ ] rclone and python-dotenv installed and added to environment.yml.
- [ ] Existing .env preserved and Research Drive credentials set privately.
- [ ] Share confirmed to allow listing and downloads.
- [ ] research_drive.py saved and importable.
- [ ] Root/subfolder listing succeeds.
- [ ] Selected download reviewed with dry_run=True.
- [ ] Disk space checked.
- [ ] Download completes successfully.
- [ ] Notebook input points to the intended local leaf folder.
- [ ] Output directory is separate from downloaded input.
- [ ] FFmpeg available in the notebook kernel.
- [ ] WILLMA credentials configured independently.
- [ ] Small authorized transcription test succeeds and outputs are reviewed.
