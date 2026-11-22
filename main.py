"""Entry for the-picture-that-tastes-of-one-20261122-2047.

The repository ships the finished picture as entry.png: one ripe
strawberry, macro and glossy, drawn procedurally by build_image.py
(1024x1024, under 300 KB). This program copies that image to the
output directory, byte for byte, with no network use.

Outside the grader, MAKEFUN_OUTPUT_DIR stands in for /output:
    mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
"""

import os
import shutil
from pathlib import Path


def main() -> None:
    # Revision 2: the narrower berry with small golden achenes,
    # a softer gloss and fewer, subtler droplets.
    out_dir = Path(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output"))
    out_dir.mkdir(parents=True, exist_ok=True)
    source = Path(__file__).resolve().parent / "entry.png"
    shutil.copyfile(source, out_dir / "entry.png")


if __name__ == "__main__":
    main()
