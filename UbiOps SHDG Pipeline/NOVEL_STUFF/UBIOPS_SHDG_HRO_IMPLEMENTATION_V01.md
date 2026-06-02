# UBIOPS SHDG HRO Implementation V01

## Overview

This document provides a concise implementation overview of how the original SHDG pipeline on UbiOps, which used **Azure OpenAI `gpt-5.3-chat`** for `FLOW03`, was adapted to a new variant that uses a **local large language model (LLM)** on **Hogeschool Rotterdam NutaNix hardware**.

The goal of this adaptation is to keep synthetic clinical text generation as local as possible within the HRO / UbiOps runtime boundary, while preserving the existing SHDG pipeline structure:

- **FLOW01+02** — PDF ingestion and privacy masking
- **FLOW03** — synthetic dossier generation using an LLM
- **FLOW04** — evaluation and privacy similarity scoring

The architectural change affects **FLOW03 only**.

---

## 1. Original baseline: Azure OpenAI implementation

The original implementation of `flow03-ga-synthesis:v1` used:

- **Client**: `AzureOpenAI`
- **Endpoint**: `https://llmfoundrys.cognitiveservices.azure.com/`
- **Deployment name**: `gpt-5.3-chat`
- **Environment variable**: `AZURE_OPENAI_API_KEY`
- **Execution mode**: remote API call from inside the UbiOps deployment

In that setup:

1. `FLOW01+02` generated `anonymized_output.md`
2. `FLOW03` sent the anonymized markdown to Azure OpenAI
3. Azure OpenAI returned synthetic dossier text
4. `FLOW04` compared the anonymized reference and synthetic output

This version worked and passed smoke tests, but it still depended on an external hosted LLM endpoint.

---

## 2. Target architecture: local LLM on HRO NutaNix

The new implementation replaces the remote Azure OpenAI call in `FLOW03` with a locally hosted Hugging Face model running on the **HRO UbiOps GPU instance**:

- **Organisation**: `hogeschool-rotterdam`
- **Project**: `shdg-hro-project`
- **Deployment**: `flow03-ga-synthesis`
- **Version**: `v2`
- **Model**: `nvidia/Llama-3.1-Nemotron-70B-Instruct-HF`
- **Environment**: `ubuntu22-04-python3-10-cuda12-3-2`
- **Instance group**: `HRO - 1 GPU - 14 vCPU - 30GB RAM - 140GB Disk`
- **Secret**: `HUGGINGFACE_TOKEN`

In the new setup:

1. `FLOW01+02` still generates `anonymized_output.md`
2. `FLOW03:v2` loads the Nemotron model inside the UbiOps deployment container
3. The local model generates `synthetic_dossier.md`
4. `FLOW04` runs unchanged
5. A new pipeline version can be created so `flow03` points to `v2`

---

## 3. Why this adaptation was made

The move from Azure OpenAI to a local HRO-hosted LLM was made for the following reasons:

- **Data locality**: anonymized clinical text no longer leaves the HRO/UbiOps boundary for inference
- **Institutional control**: inference can be aligned with local governance and security requirements
- **Model independence**: the pipeline no longer depends on Azure OpenAI availability or model deployment naming
- **Architectural continuity**: only `FLOW03` changes; all other pipeline stages remain intact

---

## 4. Code changes made in FLOW03

The new local implementation changed `FLOW03` from an API client deployment to a local inference deployment.

### 4.1 Old pattern (Azure OpenAI)

The original code used:

- `from openai import AzureOpenAI`
- `self.client = AzureOpenAI(...)`
- `self.client.chat.completions.create(...)`

This required only the `openai` package and an Azure secret.

### 4.2 New pattern (local Hugging Face model)

The new code uses:

- `torch`
- `transformers`
- `bitsandbytes`
- `accelerate`
- `huggingface_hub`

The local deployment now:

1. loads the tokenizer and model from Hugging Face
2. quantizes the model in **4-bit NF4** using `bitsandbytes`
3. uses `device_map="auto"` so the model is split across GPU and CPU RAM if needed
4. applies a chat template to the anonymized markdown input
5. generates synthetic clinical text directly in the container
6. writes the result to `synthetic_dossier.md`

### 4.3 Model selection

The selected model is:

```text
nvidia/Llama-3.1-Nemotron-70B-Instruct-HF
```

This replaced the earlier placeholder model:

```text
meta-llama/Llama-3.1-70B-Instruct
```

The Nemotron variant was selected as the desired local model baseline for the HRO implementation.

---

## 5. Infrastructure choices

### 5.1 UbiOps environment

The deployment uses the GPU-enabled environment:

```text
ubuntu22-04-python3-10-cuda12-3-2
```

This was chosen because it is available in the HRO UbiOps project and supports GPU workloads.

### 5.2 HRO NutaNix hardware

The deployment targets:

```text
HRO - 1 GPU - 14 vCPU - 30GB RAM - 140GB Disk
```

This provides:

- 1 GPU
- 14 vCPU
- 30 GB RAM
- 140 GB disk

The disk size is important because the model cache and deployment artifacts are large. The RAM and GPU memory budget are tight for 70B-class models, so quantization and automatic CPU/GPU partitioning are required.

### 5.3 Quantization strategy

The deployment uses:

- **4-bit NF4 quantization**
- `bnb_4bit_use_double_quant=True`
- `bnb_4bit_compute_dtype=torch.bfloat16`

Without quantization, a 70B model would not be feasible on this hardware.

---

## 6. UbiOps deployment changes

The following deployment-level changes were introduced.

### 6.1 Existing deployment reused

The same deployment name was reused:

```text
flow03-ga-synthesis
```

This preserved compatibility with the rest of the SHDG pipeline.

### 6.2 New deployment version created

A new version was created:

```text
v2
```

This allows the Azure-based implementation (`v1`) and the local NutaNix implementation (`v2`) to coexist side by side.

### 6.3 New secret

The Azure secret:

```text
AZURE_OPENAI_API_KEY
```

was replaced for the local version by:

```text
HUGGINGFACE_TOKEN
```

This token is required to download the Nemotron model from Hugging Face.

---

## 7. CLI implementation workflow

The migration can be executed entirely from the CLI.

### 7.1 Deploy FLOW03:v2

```powershell
conda activate pubmed-env
ubiops current_project set shdg-hro-project
Set-Location "D:\OneDrive - Hogeschool Rotterdam\1_CURRENT_DOCUMENTS\DATALAB_ALIGNMENT\UbiOps-NutaNix\DEPLOYMENT_CODE\flow03-ga-synthesis"

Compress-Archive -Path ".\deployment.py", ".\requirements.txt" -DestinationPath ".\flow03-ga-synthesis-v2.zip" -Force

ubiops deployments deploy flow03-ga-synthesis \
  -v v2 \
  -dir . \
  -deployment_py deployment.py \
  -e ubuntu22-04-python3-10-cuda12-3-2 \
  -inst_group "HRO - 1 GPU - 14 vCPU - 30GB RAM - 140GB Disk" \
  -min 1 \
  -max 1 \
  -t 1800 \
  -rtm metadata \
  -rtt 604800 \
  -desc "Nemotron-70B on HRO NutaNix GPU" \
  -y --overwrite
```

### 7.2 Add the Hugging Face secret

```powershell
ubiops environment_variables create HUGGINGFACE_TOKEN \
  --value "hf_..." \
  --secret \
  -d flow03-ga-synthesis \
  -v v2 \
  --overwrite
```

### 7.3 Wait for readiness

```powershell
ubiops deployment_versions get v2 -d flow03-ga-synthesis -fmt json
ubiops deployment_versions wait v2 -d flow03-ga-synthesis --stream_logs
```

---

## 8. Pipeline adaptation

The original pipeline version used:

- `flow01-02-ingest-anonymize:v1`
- `flow03-ga-synthesis:v1`
- `flow04-evaluator:v1`

To test the new local LLM end to end, an additional pipeline version should be created:

```text
shdg-pipeline:v2
```

with the following object mapping:

- `flow01 -> v1`
- `flow03 -> v2`
- `flow04 -> v1`

This preserves the working ingestion and evaluation stages while switching only the synthesis stage to the local model.

---

## 9. Testing strategy

### 9.1 Test FLOW03 directly

Before updating the full pipeline, test the new local LLM deployment directly:

1. Generate an anonymized markdown file via `FLOW01+02`
2. Create a request for `flow03-ga-synthesis:v2`
3. Confirm that `synthetic_dossier.md` is produced

### 9.2 Test the full pipeline with one EPD

After creating `shdg-pipeline:v2`, test it using a single EPD such as:

```text
EPDAfdruk_897_59037.pdf
```

This validates:

- file retrieval from SURF Research Drive
- anonymization
- local LLM synthesis on HRO NutaNix
- evaluation output generation

---

## 10. Operational considerations

### 10.1 Cold start time

The first startup may take a long time because the model must be downloaded and loaded into memory. This can take **10–20+ minutes** depending on cache state and hardware.

### 10.2 Warm instances

For this reason, the deployment was configured with:

- `minimum_instances = 1`
- `maximum_instances = 1`

This keeps the model warm between requests.

### 10.3 Token handling

The Hugging Face token must:

- be stored as a UbiOps secret
- never be committed to source control
- be rotated if it is exposed in chat, logs, or notebooks

### 10.4 Model size risk

Although the configuration is designed to make 70B inference possible, actual viability depends on the effective memory split between GPU and CPU. If the model proves too large for stable operation, a smaller instruct model can be substituted using the same deployment pattern.

---

## 11. Summary

The SHDG pipeline was successfully adapted from a remote Azure OpenAI synthesis stage to a local HRO-hosted LLM architecture by:

1. preserving the original three-stage SHDG structure
2. replacing only `FLOW03`
3. deploying a new `v2` of `flow03-ga-synthesis`
4. targeting the HRO NutaNix GPU instance in UbiOps
5. using `nvidia/Llama-3.1-Nemotron-70B-Instruct-HF`
6. planning a new pipeline version so the full SHDG workflow can be tested end to end with local inference

This results in a deployment architecture that is more locally controlled, more institutionally aligned, and better suited for HRO-hosted experimentation with synthetic clinical text generation.
