import os
import shutil
import subprocess

def organize_folder(folder_path: str = "~/Downloads") -> dict:
    target_dir = os.path.expanduser(folder_path.strip())
    if not os.path.exists(target_dir):
        return {"status": "error", "message": f"Directory {folder_path} does not exist."}

    categories = {
        "Images": [".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".heic"],
        "Documents": [".pdf", ".docx", ".doc", ".xlsx", ".pptx", ".txt", ".csv", ".md"],
        "Installers": [".dmg", ".pkg", ".iso", ".app"],
        "Archives": [".zip", ".tar", ".gz", ".rar", ".7z"],
        "Code": [".py", ".js", ".html", ".css", ".json", ".dart", ".cpp", ".c", ".rs"]
    }

    moved_counts = {}
    for filename in os.listdir(target_dir):
        full_p = os.path.join(target_dir, filename)
        if os.path.isdir(full_p) or filename.startswith("."):
            continue

        ext = os.path.splitext(filename)[1].lower()
        destination_cat = "Other"
        for cat, ext_list in categories.items():
            if ext in ext_list:
                destination_cat = cat
                break

        dest_dir = os.path.join(target_dir, destination_cat)
        os.makedirs(dest_dir, exist_ok=True)
        try:
            shutil.move(full_p, os.path.join(dest_dir, filename))
            moved_counts[destination_cat] = moved_counts.get(destination_cat, 0) + 1
        except Exception:
            pass

    total_moved = sum(moved_counts.values())
    summary = ", ".join([f"{count} {cat}" for cat, count in moved_counts.items()])
    return {
        "status": "success",
        "total_organized": total_moved,
        "detail": f"Folder {folder_path} organized successfully, Sir. Sorted {total_moved} files ({summary})."
    }

def find_files_by_keyword(query: str, max_results: int = 5) -> dict:
    try:
        res = subprocess.run(["mdfind", "-name", query.strip()], capture_output=True, text=True)
        lines = [l for l in res.stdout.strip().split("\n") if l][:max_results]
        if not lines:
            return {"status": "success", "results": [], "detail": f"No files found matching {query}, Sir."}
        formatted = "\n".join([f"- {os.path.basename(p)} ({p})" for p in lines])
        return {
            "status": "success",
            "results": lines,
            "detail": f"Found {len(lines)} files matching {query}, Sir:\n{formatted}"
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
