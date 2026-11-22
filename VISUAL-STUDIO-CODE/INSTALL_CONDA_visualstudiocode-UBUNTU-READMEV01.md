# Conda environment for WILLMA Whisper Transcriber V05d

Install Miniforge and create the `transcription-env` Conda environment for running `WILLMA_WHISPER_TRANSCRIBER_V05d.ipynb` in browser-based VS Code (code-server).

Updated: 22 November 2026.

## Scope

This guide assumes your SRC Ubuntu VM and Docker-based code-server deployment already work. It does not reinstall Docker or change your HTTPS configuration.

Run all installation commands in **Terminal → New Terminal inside the browser editor**, as container user `abc`. Do not run them in the host VM's SSH session, and do not use `sudo`.

The notebook's original documentation calls its example environment `transcriber-env`. This guide deliberately uses `transcription-env`, as requested. The kernel you select must match the name used here.

### What has been verified in this deployment

Your terminal output confirmed:

- Miniforge installed in `/config/miniforge3`.
- Conda reported version `26.9.4`.
- `transcription-env` exists in `/config/miniforge3/envs/transcription-env`.
- Its Python executable reported `Python 3.11.18`.
- Python and Jupyter editor extensions were installed.

These observations confirm installation and interpreter availability, not successful execution of every notebook cell or a complete transcription run.

If these components already exist, use the checks below and skip the corresponding installation steps.

## Contents

1. [Storage and prerequisites](#1-storage-and-prerequisites)
2. [Install Miniforge](#2-install-miniforge)
3. [Create environment.yml](#3-create-environmentyml)
4. [Create or update the environment](#4-create-or-update-the-environment)
5. [Verify dependencies](#5-verify-dependencies)
6. [Configure the editor and kernel](#6-configure-the-editor-and-kernel)
7. [Adapt the notebook for Linux](#7-adapt-the-notebook-for-linux)
8. [Run a first test](#8-run-a-first-test)
9. [Daily use and reproducibility](#9-daily-use-and-reproducibility)
10. [Troubleshooting](#10-troubleshooting)

## 1. Storage and prerequisites

This guide uses:

```text
/config/
├── miniforge3/
│   └── envs/
│       └── transcription-env/
└── workspace/
    ├── WILLMA_WHISPER_TRANSCRIBER_V05d.ipynb
    ├── install_conda.sh
    ├── environment.yml
    ├── .env                         # optional; not loaded automatically
    └── audio/
        └── transcriber_v05d_outputs/
```

In the Docker Compose deployment used here, `~/VSCode/config` on the host is mounted at `/config` in the container. Consequently, Conda, environments, notebooks, and data under `/config` survive container recreation, provided this bind mount is preserved.

Verify the terminal context:

```bash
whoami
echo "$HOME"
uname -m
ls -ld /config
```

Expected for this deployment:

```text
abc
/config
x86_64
```

You need write access to `/config`, sufficient disk space, and outbound access to GitHub and conda-forge. Notebook transcription also requires authorized access to WILLMA.

Prepare the workspace:

```bash
mkdir -p /config/workspace
cd /config/workspace
```

### Terminal commands versus file contents

- Run `bash`, `conda`, and `code-server` commands in the terminal.
- Paste YAML only into `environment.yml`.
- Run commands such as `Developer: Reload Window` in the editor's Command Palette, not Bash.
- Shell heredoc markers such as `EOF` and `SCRIPT` are not part of YAML or Python files.

## 2. Install Miniforge

Miniforge supplies Conda and defaults to conda-forge packages. Install it under `/config` so it is persisted by your existing Docker mount.

### 2.1 Check for an existing installation

```bash
/config/miniforge3/bin/conda --version
```

If this works, skip to section 2.4. Do not reinstall over a working installation.

### 2.2 Create the installer script

In VS Code, create `/config/workspace/install_conda.sh`. Paste **only the following script contents** into the file and save it with `Ctrl+S`:

```bash
#!/usr/bin/env bash
set -euo pipefail

CONDA_DIR="/config/miniforge3"

if [ -x "$CONDA_DIR/bin/conda" ]; then
    echo "Existing Conda installation found."
elif [ -e "$CONDA_DIR" ]; then
    echo "ERROR: $CONDA_DIR exists but has no conda executable."
    echo "Inspect this directory before retrying; do not delete it blindly."
    exit 1
else
    case "$(uname -s)-$(uname -m)" in
        Linux-x86_64|Linux-aarch64) ;;
        *) echo "Unsupported platform for this guide."; exit 1 ;;
    esac

    INSTALLER="$(mktemp /config/miniforge-installer.XXXXXX.sh)"
    trap 'rm -f "$INSTALLER"' EXIT

    curl -fL \
      "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-$(uname -s)-$(uname -m).sh" \
      -o "$INSTALLER"

    bash "$INSTALLER" -b -p "$CONDA_DIR"
fi

"$CONDA_DIR/bin/conda" --version
"$CONDA_DIR/bin/conda" init bash

echo "Installation check complete. Initialize your current terminal next."
```

This uses the latest installer for convenience. For controlled deployments, choose a fixed release and verify its published SHA-256 checksum before execution.

### 2.3 Run the script

In the browser terminal:

```bash
cd /config/workspace
bash -n install_conda.sh && bash install_conda.sh
```

`bash -n` checks syntax without running the installer. Running with `bash` does not require executable permission.

Alternatively, after syntax validation:

```bash
chmod +x /config/workspace/install_conda.sh
/config/workspace/install_conda.sh
```

Choose one execution method. Do not run this Bash script with `sh`.

### 2.4 Initialize the current terminal

Run in the terminal after installation, even if the installer ran `conda init`:

```bash
source /config/miniforge3/etc/profile.d/conda.sh
conda --version
conda config --set auto_activate false
```

The observed Conda version accepts `auto_activate`; its warning about `auto_activate_base` being an alias is informational. If using an older Conda release that does not recognize `auto_activate`, use:

```bash
conda config --set auto_activate_base false
```

`conda init bash` prepares future Bash sessions. Sourcing `conda.sh` enables activation in the current shell; an installer running as a child process cannot initialize its parent terminal.

## 3. Create environment.yml

The uploaded notebook documents Python 3.11 and imports libraries for HTTP requests, audio processing, tables, Excel output, and PDF generation. It also invokes the FFmpeg executable.

Use `environment.yml` as the main dependency specification: unlike a pip-only requirements file, it can include Python itself and FFmpeg.

Create `/config/workspace/environment.yml` in the editor and paste **only this YAML**:

```yaml
name: transcription-env

channels:
  - conda-forge
  - nodefaults

dependencies:
  # Runtime
  - python=3.11
  - pip

  # Notebook support
  - ipykernel
  - ipython

  # Data and HTTP requests
  - numpy
  - pandas
  - requests
  - urllib3

  # Audio processing
  - pysoundfile
  - libsndfile
  - scipy
  - noisereduce
  - ffmpeg

  # Excel and PDF output
  - openpyxl
  - reportlab
```

Save with `Ctrl+S`. Do not include terminal commands, Markdown fences, or a final `EOF` line in the actual file.

### Dependency notes

| Dependency | Purpose |
|---|---|
| Python 3.11 | Notebook's documented tested runtime |
| pandas / numpy | Tables and numerical operations |
| requests / urllib3 | WILLMA HTTP requests and retries |
| pysoundfile / libsndfile | Provides `import soundfile` and its native audio library |
| scipy | Filtering and resampling |
| noisereduce | Optional notebook preprocessing, included here |
| ffmpeg | Audio extraction and validation for media containers |
| openpyxl | Excel transcript/diarization export |
| reportlab | PDF transcript export |
| ipykernel / ipython | Notebook kernel and display support |

This specification leaves most versions unpinned. It is a maintainable starting specification, not an exact lockfile. Package solving and successful notebook execution must be verified on the target system.

The inspected notebook calls WILLMA's remote transcription and diarization endpoints. Local Whisper model weights, PyTorch, and a local GPU are not required merely to execute these API calls.

## 4. Create or update the environment

### 4.1 Check existing environments

```bash
source /config/miniforge3/etc/profile.d/conda.sh
conda env list
```

### 4.2 Create if it does not exist

```bash
cd /config/workspace
conda env create -f environment.yml
```

Wait for a successful finish. Do not continue after a package-solving or download failure.

### 4.3 Update if it already exists

Instead of recreating or deleting it:

```bash
conda env update \
  --name transcription-env \
  --file /config/workspace/environment.yml
```

No `--prune` is used: this avoids intentionally removing other packages you may have installed.

### 4.4 Activate and check

```bash
conda activate transcription-env
python --version
which python
```

Expected executable:

```text
/config/miniforge3/envs/transcription-env/bin/python
```

Your reported installation returned Python `3.11.18`; another compatible solve may return a different Python 3.11 patch release.

## 5. Verify dependencies

With `transcription-env` activated, paste this entire block into the terminal:

```bash
python - <<'PY'
import importlib
import shutil
import subprocess
import sys

print("Python:", sys.version)
print("Interpreter:", sys.executable)

modules = [
    "numpy", "pandas", "requests", "urllib3", "soundfile",
    "scipy", "noisereduce", "openpyxl", "reportlab",
    "ipykernel", "IPython",
]
failures = []

for module in modules:
    try:
        importlib.import_module(module)
        print(f"OK: {module}")
    except Exception as exc:
        failures.append(module)
        print(f"FAILED: {module}: {exc}")

ffmpeg = shutil.which("ffmpeg")
if ffmpeg:
    result = subprocess.run(
        [ffmpeg, "-version"], capture_output=True, text=True, check=False
    )
    if result.returncode == 0:
        print("OK:", result.stdout.splitlines()[0])
    else:
        failures.append("ffmpeg")
        print("FAILED: ffmpeg:", result.stderr)
else:
    failures.append("ffmpeg")
    print("FAILED: ffmpeg not found on PATH")

if failures:
    raise SystemExit("Checks failed: " + ", ".join(failures))

print("All dependency checks passed.")
PY
```

This verifies imports and FFmpeg execution. It does not upload audio, verify API credentials, validate all input formats, or prove end-to-end transcription success.

## 6. Configure the editor and kernel

Conda packages and VS Code editor extensions are separate installations.

### 6.1 Install or check editor extensions

In the browser terminal, as `abc`:

```bash
code-server --install-extension ms-python.python
code-server --install-extension ms-toolsai.jupyter
```

An `already installed` message is informational. Do not use `--force` just because an interpreter has not been discovered.

If the GUI displays a publisher-trust prompt, inspect the exact extension identifier and source before approving. An unverified-publisher warning is not a security guarantee and should not be dismissed solely because a namespace looks familiar.

### 6.2 Reload the editor through its interface

Save files. Press `F1` or open **☰ → View → Command Palette**, then select:

```text
Developer: Reload Window
```

Do not type this into Bash. A terminal error such as `bash: Developer:: command not found` means an editor command was entered in the wrong place.

### 6.3 Register the kernel with the exact interpreter

In the terminal:

```bash
/config/miniforge3/envs/transcription-env/bin/python \
  -m ipykernel install \
  --user \
  --name transcription-env \
  --display-name "Python (transcription-env)"
```

Expected registration destination is beneath `/config/.local/share/jupyter/kernels/`, because this deployment uses `/config` as the container user's home.

### 6.4 Select the interpreter manually if discovery fails

Open the Command Palette in the GUI, select **Python: Select Interpreter**, then:

1. Click **Enter interpreter path…**.
2. Enter `/config/miniforge3/envs/transcription-env/bin/python`.
3. Press Enter.

A `Python is not installed` entry in the discovery menu does not establish that an explicitly verified Conda Python is absent. The terminal check using its full path is the relevant check.

Do not enter the host path `~/VSCode/config/...` into the container's interpreter picker.

### 6.5 Select the notebook kernel

Open `WILLMA_WHISPER_TRANSCRIBER_V05d.ipynb`, then:

1. Click **Select Kernel** in the upper-right corner.
2. Choose **Select Another Kernel** if needed.
3. Look under **Jupyter Kernels** or **Python Environments**.
4. Select **Python (transcription-env)**.

Interpreter selection for Python files and kernel selection for notebooks are distinct. Terminal activation alone does not prove which kernel a notebook uses.

### 6.6 Verify inside a notebook cell

```python
import os
import shutil
import subprocess
import sys
from pathlib import Path

expected = Path("/config/miniforge3/envs/transcription-env/bin/python")
print("Interpreter:", sys.executable)
print("Python:", sys.version)
assert Path(sys.executable) == expected, "Select the transcription-env kernel"

# Ensure external tools from this environment can be found by subprocesses.
env_bin = str(expected.parent)
os.environ["PATH"] = env_bin + os.pathsep + os.environ.get("PATH", "")

ffmpeg = shutil.which("ffmpeg")
assert ffmpeg, "FFmpeg was not found"
result = subprocess.run(
    [ffmpeg, "-version"], capture_output=True, text=True, check=True
)
print("FFmpeg:", ffmpeg)
print(result.stdout.splitlines()[0])
```

The explicit PATH setup matters if the notebook kernel was launched by executable path without full Conda shell activation. Keep this cell before the notebook invokes FFmpeg.

## 7. Adapt the notebook for Linux

Installing dependencies is not sufficient to run the original notebook unchanged.

### 7.1 Replace Windows paths

The supplied notebook contains Windows `D:`/`E:` paths in its setup and standalone examples. Replace them with container paths before those cells run.

Create the input directory in the terminal:

```bash
mkdir -p /config/workspace/audio
```

Upload your audio there. Replace the initial path configuration block with:

```python
from pathlib import Path

NOTEBOOK_PATH = Path(
    "/config/workspace/WILLMA_WHISPER_TRANSCRIBER_V05d.ipynb"
)
DEFAULT_INPUT_FOLDER = Path("/config/workspace/audio")
DEFAULT_OUTPUT_FOLDER = DEFAULT_INPUT_FOLDER / "transcriber_v05d_outputs"
DEFAULT_CLEANED_FOLDER = DEFAULT_OUTPUT_FOLDER / "cleaned_audio"
DEFAULT_LOG_FOLDER = DEFAULT_OUTPUT_FOLDER / "logs"
DEFAULT_PROGRESS_FILE = DEFAULT_LOG_FOLDER / "batch_progress.json"
DEFAULT_REFERENCE_FOLDER = DEFAULT_OUTPUT_FOLDER / "references"

for folder in (
    DEFAULT_OUTPUT_FOLDER,
    DEFAULT_CLEANED_FOLDER,
    DEFAULT_LOG_FOLDER,
    DEFAULT_REFERENCE_FOLDER,
):
    folder.mkdir(parents=True, exist_ok=True)
```

Do this before the existing `CONFIG` dictionary is constructed, and remove later Windows assignments that would overwrite your changes. Update standalone example file paths separately if you use those cells.

This documentation does not modify the supplied notebook automatically.

### 7.2 Replace hard-coded API credentials

The uploaded notebook includes API-key values in multiple cells. Treat shared embedded credentials as exposed and revoke/rotate them. Do not commit replacement keys, raw interview data, or transcript outputs to a public repository.

The presence of a `.env` file does not automatically make its values available to Python. For the first test, use a masked prompt in the notebook before API calls:

```python
from getpass import getpass

CONFIG["willma_api_key"] = getpass("WILLMA API key: ").strip()
if not CONFIG["willma_api_key"]:
    raise ValueError("A valid WILLMA API key is required")
```

Run this after the main `CONFIG` definition but before model discovery or transcription. Remove hard-coded credentials in every standalone cell you intend to use; those cells can have independent variables or fallback configuration.

If using environment variables or a dotenv loader later, configure that explicitly. Do not overwrite your existing `.env` blindly; it may contain unrelated settings.

### 7.3 Respect data handling requirements

The workflow uploads media to WILLMA. Confirm institutional authorization and applicable consent/data-processing requirements before sending research recordings. This is not an entirely offline transcription pipeline.

### 7.4 Use the main workflow first

The main code sections are:

1. `CELL01: SETUP — PATHS, IMPORTS AND CONFIGURATION`.
2. `CELL03: ALL FUNCTIONS`.
3. The diagnostic cell listing discovered audio files.
4. `CELL05: BATCH RUN / DEMO`.

The later `CELL06` self-contained and `CELL07` minimal examples redefine functions or use independent settings. Do not use **Run All** blindly: start with the main workflow and run the alternative examples separately when needed.

The batch demo sets `overwrite_outputs` to `True` in its copied settings. Review that line before rerunning a batch if you intend to preserve existing outputs.

## 8. Run a first test

1. Select the `Python (transcription-env)` kernel.
2. Run the interpreter/FFmpeg verification cell from section 6.6.
3. Use a short, non-sensitive test recording in `/config/workspace/audio`.
4. Apply the Linux path configuration.
5. Run the main setup cell.
6. Set a valid API key without embedding it in source.
7. Run the main functions and diagnostic cells.
8. Confirm that the diagnostic list includes the intended recording.
9. Run the batch workflow and inspect its status and output-integrity results.

The main export code writes:

```text
<stem>.txt
<stem>.segments.json
<stem>.speaker.csv
<stem>.speaker.xlsx
<stem>.speaker.srt
<stem>.transcript.pdf
```

A passing import check is not proof of correct transcription or speaker attribution. The code includes fallback speaker-label behavior; inspect the actual result and API responses rather than treating every speaker label as verified diarization.

## 9. Daily use and reproducibility

### New terminal

```bash
source /config/miniforge3/etc/profile.d/conda.sh
conda activate transcription-env
cd /config/workspace
```

The environment need not be recreated each time you open the editor.

### Update dependencies

Edit `environment.yml`, then:

```bash
conda env update \
  --name transcription-env \
  --file /config/workspace/environment.yml
```

Restart the notebook kernel after changing its packages.

### Record a tested environment

After the notebook works:

```bash
conda env export -n transcription-env \
  | sed '/^prefix: /d' \
  > /config/workspace/environment-resolved.yml

conda list -n transcription-env --explicit \
  > /config/workspace/conda-linux-64-explicit.txt
```

Keep the hand-maintained `environment.yml` as the main specification. The resolved export records package versions; the explicit specification is platform-specific. Review exports for private channel URLs or tokens before sharing.

### Backup

Back up notebooks, environment specifications, authorized data, and outputs securely outside the VM. The existing Docker deployment's backup of the entire `config` directory also includes Miniforge and environments, increasing its size. Do not rely solely on a backup stored on the same VM.

## 10. Troubleshooting

### `conda: command not found`

```bash
source /config/miniforge3/etc/profile.d/conda.sh
conda --version
```

If this fails:

```bash
ls -l /config/miniforge3/bin/conda
```

Do not reinstall before checking whether the installation exists.

### `Permission denied` when running install_conda.sh

Run explicitly with Bash:

```bash
bash /config/workspace/install_conda.sh
```

Or add executable permission with `chmod +x` before running it directly. No `sudo` is needed.

### YAML parsing error

Ensure `environment.yml` contains only YAML, uses spaces for indentation, and has no `EOF`, `cat > ...`, or Markdown backticks. Those belong to terminal creation instructions or documentation, not the file itself.

### Environment already exists

Use `conda env update`, not deletion and recreation. Confirm the path with:

```bash
/config/miniforge3/bin/conda env list
```

### GUI says Python is not installed

Test the actual interpreter:

```bash
/config/miniforge3/envs/transcription-env/bin/python --version
```

If it works, manually enter that path in **Python: Select Interpreter → Enter interpreter path…**.

### Kernel is missing

Repeat registration with the environment's full Python path. If `ipykernel` is missing:

```bash
/config/miniforge3/bin/conda install \
  -n transcription-env -c conda-forge ipykernel -y
```

Reload the editor through its Command Palette, reopen the notebook, and select the kernel again.

If selection still fails, inspect **View → Output → Jupyter** and **Python** for activation or discovery errors. Installed extensions are not proof that they activated successfully.

### FFmpeg works in terminal but not notebook

Run section 6.6 inside the notebook. A kernel using the correct Python can still inherit a PATH that omits the Conda environment's `bin` directory.

### Import fails despite successful installation

Print `sys.executable` in the notebook. Check that it points to `transcription-env`, not `base` or a system Python. Select the intended kernel and restart it after package changes.

### No audio files found

Inspect `CONFIG["input_folder"]`, verify uploaded files exist inside the container, and check that no old Windows path assignment remains. The main discovery code searches the selected folder, not recursively through every subdirectory.

### HTTP 401 or API/model errors

These are separate from environment installation. Check the current API key, authorization, endpoint response, and model catalog. Do not print keys in logs or issue reports. A model-catalog error cannot be repaired by reinstalling Python packages without investigating its response.

## References

- [Miniforge installation documentation](https://github.com/conda-forge/miniforge)
- [Conda environment management](https://docs.conda.io/projects/conda/en/stable/user-guide/tasks/manage-environments.html)
- [Conda configuration](https://docs.conda.io/projects/conda/en/stable/configuration.html)
- [VS Code Python support](https://code.visualstudio.com/docs/languages/python)
- [VS Code Jupyter notebooks](https://code.visualstudio.com/docs/datascience/jupyter-notebooks)
- [IPython kernel installation](https://ipython.readthedocs.io/en/stable/install/kernel_install.html)
- [code-server extension documentation](https://coder.com/docs/code-server/FAQ/)

The notebook-specific dependency, configuration, and workflow descriptions in this guide were derived from the supplied `WILLMA_WHISPER_TRANSCRIBER_V05d.ipynb`. The environment and editor setup still require verification on the target deployment.

## Completion checklist

- [ ] Commands run inside the code-server container as `abc`.
- [ ] Miniforge installed under `/config/miniforge3`.
- [ ] `environment.yml` contains valid YAML only.
- [ ] `transcription-env` exists and Python 3.11 runs.
- [ ] Dependency checks pass.
- [ ] Python and Jupyter editor extensions are enabled.
- [ ] Kernel registered and selected.
- [ ] Notebook `sys.executable` points to `transcription-env`.
- [ ] FFmpeg executes from the notebook kernel.
- [ ] Windows paths replaced with container paths.
- [ ] Shared embedded API credentials rotated and removed.
- [ ] Authorized test recording transcribed and outputs reviewed.
- [ ] Tested environment exported and backups stored securely.
