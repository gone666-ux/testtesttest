import os
from pathlib import Path

DEFAULT_OUTPUT_DIR = "/output"
JOKE = "I asked my AI coding agent to fix a typo; it rewrote 40 files, including the ticket, which now says 'rewrite 40 files.'"


def write_entry(output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    entry_path = output_dir / "entry.txt"
    entry_path.write_bytes(JOKE.encode("utf-8"))
    return entry_path


def main() -> None:
    output_dir = Path(os.environ.get("MAKEFUN_OUTPUT_DIR", DEFAULT_OUTPUT_DIR))
    write_entry(output_dir)


if __name__ == "__main__":
    main()
