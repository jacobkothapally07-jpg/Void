import subprocess
import os

BLOCKED_COMMANDS = ["rm -rf /", "mkfs", "dd if="]

def run_terminal_command(command: str) -> dict:
    clean_cmd = command.strip()
    for b in BLOCKED_COMMANDS:
        if b in clean_cmd:
            return {"status": "error", "message": "Command blocked for safety reasons."}
            
    try:
        res = subprocess.run(
            clean_cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=15,
            cwd=os.path.expanduser("~")
        )
        out = res.stdout.strip()
        err = res.stderr.strip()
        combined = f"{out}\n{err}".strip() if err else out
        if len(combined) > 1000:
            combined = combined[:1000] + "... [truncated]"
            
        return {
            "status": "success" if res.returncode == 0 else "warning",
            "returncode": res.returncode,
            "output": combined or "Command executed successfully.",
            "detail": f"Executed '{clean_cmd}' successfully, Sir."
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
