import os
import json
import subprocess
import time

class MainBrainNode:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "prompt_instructions": ("STRING", {
                    "default": (
                        "You are performing a visual OCR and transcript QA audit on the video layer in After Effects.\n\n"
                        "WORKFLOW STEPS:\n"
                        "1. Inspect composition duration and frame rate via ExtendScript.\n"
                        "2. Sample video frames using $.grabCurrentFrameSnapshot(frameNumber).\n"
                        "3. Compare on-screen burned-in text against spoken audio.\n"
                        "4. FOR EVERY ERROR FOUND:\n"
                        "   - Call $.addQAMarker(frameNumber, \"Current: <wrong>\\nCorrect: <right>\") on layer 'QA_Error_Markers'.\n"
                        "   - Snap playhead with $.jumpToFrame(errorFrame).\n"
                        "5. Run $.exportQAMarkersToText() once completed.\n\n"
                        "STRICT MARKER FORMAT (NO EXPLANATIONS OR ISSUE LABELS):\n"
                        "Current: <exact wrong text>\n"
                        "Correct: <corrected text>"
                    ),
                    "multiline": True
                }),
            },
            "optional": {
                "video_path": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "forceInput": True
                }),
                "IMAGE_OR_VIDEO": ("IMAGE_OR_VIDEO,VIDEO,IMAGE,STRING", {}),
                "trigger_signal_1": ("STRING", {"forceInput": True}),
                "trigger_signal_2": ("STRING", {"forceInput": True}),
            }
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("execution_log", "trigger_signal")
    FUNCTION = "send_to_claude_window"
    OUTPUT_NODE = True
    CATEGORY = "Automation/AI Brain"

    @classmethod
    def IS_CHANGED(s, prompt_instructions, video_path="", IMAGE_OR_VIDEO=None, trigger_signal_1=None, trigger_signal_2=None):
        return float(time.time())

    def parse_path(self, raw):
        if not raw:
            return ""
        if isinstance(raw, str):
            return raw
        if isinstance(raw, (list, tuple)) and len(raw) > 0:
            return self.parse_path(raw[0])
        if isinstance(raw, dict):
            for k in ["path", "filename", "video_path", "text"]:
                if k in raw:
                    return self.parse_path(raw[k])
        return str(raw)

    def send_to_claude_window(self, prompt_instructions, video_path="", IMAGE_OR_VIDEO=None, trigger_signal_1=None, trigger_signal_2=None):
        import base64
        
        target_path = self.parse_path(video_path)
        if not target_path or not os.path.exists(target_path):
            target_path = self.parse_path(IMAGE_OR_VIDEO)

        clean_path = target_path.strip().strip('"').strip("'")
        print(f"[Main Brain Node] Ingested File: '{clean_path}'")

        if not clean_path or not os.path.exists(clean_path):
            err_msg = f"ERROR: Target file path invalid or not found -> '{clean_path}'"
            print(f"[Main Brain Node] {err_msg}")
            return (err_msg, f"FAILED_{time.time()}")

        try:
            full_prompt = (
                f"Import the video at file path \"{clean_path}\" into After Effects using the AE MCP tool if not already loaded, "
                f"then perform the following QA check:\n\n{prompt_instructions}"
            )

            encoded_prompt = base64.b64encode(full_prompt.encode('utf-8')).decode('utf-8')

            # Bulletproof PowerShell Script with Direct Win32 Thread-Attaching
            ps_script = f'''
            $code = @"
            using System;
            using System.Runtime.InteropServices;
            using System.Text;
            using System.Windows.Forms;

            public class WindowActivator {{
                [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr hWnd);
                [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);
                [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
                [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint lpdwProcessId);
                [DllImport("user32.dll")] public static extern bool AttachThreadInput(uint idAttach, uint idAttachTo, bool fAttach);
                [DllImport("user32.dll")] public static extern IntPtr SetFocus(IntPtr hWnd);

                public static void ForceFocus(IntPtr hWnd) {{
                    ShowWindow(hWnd, 9); // SW_RESTORE
                    IntPtr foreHWnd = GetForegroundWindow();
                    uint foreThread = GetWindowThreadProcessId(foreHWnd, out _);
                    uint appThread = GetWindowThreadProcessId(hWnd, out _);

                    if (foreThread != appThread) {{
                        AttachThreadInput(foreThread, appThread, true);
                        SetForegroundWindow(hWnd);
                        SetFocus(hWnd);
                        AttachThreadInput(foreThread, appThread, false);
                    }} else {{
                        SetForegroundWindow(hWnd);
                        SetFocus(hWnd);
                    }}
                }}
            }}
"@
            Add-Type -TypeDefinition $code -ReferencedAssemblies "System.Windows.Forms"

            # Locate Claude Code process specifically by process window title or process name
            $proc = Get-Process | Where-Object {{
                $_.MainWindowHandle -ne 0 -and (
                    $_.MainWindowTitle -like "*Claude*" -or
                    $_.MainWindowTitle -like "*after-effects-mcp*"
                )
            }} | Select-Object -First 1

            # Fallback to general terminal process if title isn't explicitly hooked
            if (-not $proc) {{
                $proc = Get-Process | Where-Object {{
                    $_.MainWindowHandle -ne 0 -and ($_.ProcessName -eq "wt" -or $_.ProcessName -eq "cmd")
                }} | Select-Object -First 1
            }}

            if ($proc) {{
                [WindowActivator]::ForceFocus($proc.MainWindowHandle)
                Start-Sleep -Milliseconds 600

                # Decode prompt string
                $base64 = "{encoded_prompt}"
                $bytes = [System.Convert]::FromBase64String($base64)
                $decodedText = [System.Text.Encoding]::UTF8.GetString($bytes)

                # Set Clipboard and simulate Ctrl+V and Enter
                [System.Windows.Forms.Clipboard]::SetText($decodedText)
                [System.Windows.Forms.SendKeys]::SendWait("^v")
                Start-Sleep -Milliseconds 400
                [System.Windows.Forms.SendKeys]::SendWait("~")
                Write-Output "SUCCESS"
            }} else {{
                Write-Output "WINDOW_NOT_FOUND"
            }}
            '''

            result = subprocess.run(["powershell", "-ExecutionPolicy", "Bypass", "-Command", ps_script], capture_output=True, text=True)
            output = result.stdout.strip()

            if "SUCCESS" in output:
                log = f"Successfully dispatched QA instructions to Claude Code for file: {clean_path}"
                print(f"[Main Brain Node] {log}")
                return (log, f"TRIGGER_OUT_{time.time()}")
            else:
                err = f"Could not locate open terminal window hosting Claude Code. Output: {output}"
                print(f"[Main Brain Node] {err}")
                return (err, f"FAILED_{time.time()}")

        except Exception as ex:
            err = f"EXCEPTION in Main Brain Node: {str(ex)}"
            print(f"[Main Brain Node] {err}")
            return (err, f"ERROR_{time.time()}")


NODE_CLASS_MAPPINGS = {"MainBrainNode": MainBrainNode}
NODE_DISPLAY_NAME_MAPPINGS = {"MainBrainNode": "Main Brain Node (AE Video QA)"}
