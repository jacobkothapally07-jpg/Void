import os
from pathlib import Path

_MAX_SIZE_BYTES = 1_048_576

def read_workspace_file(path: str, max_lines: int = 200) -> dict:
    """
    Safely reads file contents from the user workspace or system.
    Returns lines or text preview.
    """
    clean_p = os.path.expanduser(path.strip())
    p = Path(clean_p).resolve()
    
    if not p.exists():
        return {"status": "error", "message": f"File '{path}' does not exist."}
    if not p.is_file():
        return {"status": "error", "message": f"Path '{path}' is not a regular file."}
    
    try:
        size = p.stat().st_size
        if size > _MAX_SIZE_BYTES:
            return {"status": "error", "message": f"File is too large ({size} bytes, limit is 1MB)."}
        
        with open(p, "r", encoding="utf-8", errors="replace") as f:
            lines = [f.readline() for _ in range(max_lines)]
            content = "".join(lines)
            
        return {
            "status": "success",
            "path": str(p),
            "lines_read": len(lines),
            "content": content,
            "detail": f"File '{p.name}' read successfully ({len(lines)} lines)."
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
