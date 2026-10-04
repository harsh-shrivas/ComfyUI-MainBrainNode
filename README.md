# ComfyUI-MainBrainNode

An autonomous AI orchestration and terminal bridge node for ComfyUI.

Designed for automated VFX review, video QA, and generative pipelines, this node bridges ComfyUI directly with external AI CLI agents (such as **Claude Code** and the **After Effects MCP server**). It dispatches structured analysis instructions and ingested media paths directly into active terminal windows via low-level Win32 thread-attached IPC.

---

## Features

- **Win32 Thread-Attached IPC:** Bypasses Windows OS foreground-lock restrictions using direct Win32 API calls (`AttachThreadInput`, `SetForegroundWindow`, `ShowWindow`) via embedded PowerShell to reliably focus active agent terminals.
- **Base64 Clipboard Dispatch:** Encodes complex multi-line prompts and system instructions in Base64 before injection, preventing shell escaping bugs, quotes mismatch, and character corruption.
- **Targeted Process Sniffing:** Automatically identifies terminal windows hosting `Claude`, `after-effects-mcp`, Windows Terminal (`wt`), or standard consoles (`cmd`).
- **Autonomous Video QA Blueprint:** Pre-loaded with an end-to-end After Effects ExtendScript QA protocol (frame extraction, OCR review, subtitle audit, automated error marker placement, and report generation).
- **Universal Input Resolution:** Intelligently resolves raw file paths from string inputs, dictionaries, image/video tuples, or upstream pipeline loader nodes.
- **Zero External Dependencies:** Built entirely with Python standard libraries (`os`, `json`, `subprocess`, `time`, `base64`) and native Windows PowerShell.

---

## Installation

1. Navigate to your ComfyUI custom nodes directory:
    cd ComfyUI/custom_nodes

2. Clone this repository:
    git clone https://github.com/harsh-shrivas/ComfyUI-MainBrainNode.git

3. Restart ComfyUI. (Zero external pip packages required).

---

## Usage

- **Category:** `Automation/AI Brain`
- **Node Name:** `Main Brain Node (AE Video QA)`
- **Workflow:**
  1. Open a terminal session running Claude Code or your agent CLI (e.g., in Windows Terminal or CMD).
  2. Connect the output of a video loader, asset reader, or path string into `video_path` or `IMAGE_OR_VIDEO`.
  3. Customize the `prompt_instructions` field or use the built-in After Effects QA audit prompt.
  4. Connect upstream trigger signals (optional) to chain execution order.
  5. Click **Queue Prompt**. The node will resolve the file path, bring the terminal session to the foreground, inject the prompt via keystroke simulation, and output execution logs.

---

## Inputs & Outputs

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| **prompt_instructions** | `STRING` (Input) | *Multi-line* | Detailed system instructions and task protocol sent to the agent |
| **video_path** | `STRING` (Optional) | `""` | Direct path string to the media file under review |
| **IMAGE_OR_VIDEO** | `ANY` (Optional) | `None` | Flexible input pin accepting image tensors, video batches, or paths |
| **trigger_signal_1** | `STRING` (Optional) | — | Upstream dependency trigger to delay execution until ready |
| **trigger_signal_2** | `STRING` (Optional) | — | Secondary upstream dependency trigger |
| **execution_log** | `STRING` (Output) | — | Status log detailing process capture and dispatch success |
| **trigger_signal** | `STRING` (Output) | — | Downstream timestamped trigger to initiate follow-on nodes |

---

## License

MIT License. Free to use, modify, and integrate into internal VFX studios and automated creative pipelines.
