import os
import zipfile
import hashlib
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
OUTPUT_ZIP = ROOT_DIR / "FIVERR_DELIVERY_PACKAGE.zip"

EXCLUDE_DIRS = {
    ".venv",
    "venv",
    "node_modules",
    "dist",
    "__pycache__",
    ".pytest_cache",
    ".git",
    "htmlcov",
    ".idea",
    ".vscode",
}

EXCLUDE_EXTENSIONS = {
    ".pyc",
    ".pyo",
    ".pyd",
    ".db",
    ".sqlite",
    ".sqlite3",
    ".coverage",
}

EXCLUDE_FILES = {
    "FIVERR_DELIVERY_PACKAGE.zip",
    ".coverage",
}


def should_include(path: Path) -> bool:
    rel = path.relative_to(ROOT_DIR)
    parts = set(rel.parts)
    if parts & EXCLUDE_DIRS:
        return False
    if path.is_file():
        if path.suffix.lower() in EXCLUDE_EXTENSIONS:
            return False
        if path.name in EXCLUDE_FILES:
            return False
    return True


def create_delivery_zip():
    print(f"Creating delivery zip at: {OUTPUT_ZIP}")
    files_added = 0
    total_bytes = 0

    with zipfile.ZipFile(OUTPUT_ZIP, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for root, dirs, files in os.walk(ROOT_DIR):
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
            for file in files:
                file_path = Path(root) / file
                if should_include(file_path):
                    rel_path = file_path.relative_to(ROOT_DIR)
                    zip_path = Path("company-intelligence-crm") / rel_path
                    zip_file.write(file_path, arcname=str(zip_path).replace("\\", "/"))
                    files_added += 1
                    total_bytes += file_path.stat().st_size

    zip_size = OUTPUT_ZIP.stat().st_size
    sha256 = hashlib.sha256(OUTPUT_ZIP.read_bytes()).hexdigest()

    print(f"Delivery archive created successfully!")
    print(f"Files bundled: {files_added}")
    print(f"Uncompressed size: {total_bytes / (1024 * 1024):.2f} MB")
    print(f"Compressed size: {zip_size / (1024 * 1024):.2f} MB")
    print(f"SHA-256 Checksum: {sha256}")


if __name__ == "__main__":
    create_delivery_zip()
