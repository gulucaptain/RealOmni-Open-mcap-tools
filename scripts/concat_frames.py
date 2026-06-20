"""
Concatenate corresponding frames from two directories side-by-side.

Usage:
    python scripts/concat_frames.py --left dir_a/frames --right dir_b/frames --out concat_output
"""

import argparse
from pathlib import Path

from PIL import Image
from tqdm import tqdm


def main():
    parser = argparse.ArgumentParser(
        description="Concatenate stereo frame pairs side-by-side"
    )
    parser.add_argument("--left", required=True, help="Left frames directory")
    parser.add_argument("--right", required=True, help="Right frames directory")
    parser.add_argument("--out", required=True, help="Output directory")
    parser.add_argument(
        "--quality", type=int, default=95, help="JPEG quality (default: 95)"
    )
    args = parser.parse_args()

    dir_left = Path(args.left)
    dir_right = Path(args.right)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    files_left = sorted(f for f in dir_left.iterdir() if f.suffix == ".jpg")
    files_right = {f.name for f in dir_right.iterdir() if f.suffix == ".jpg"}

    count = 0
    for fpath in tqdm(files_left, desc="Concatenating"):
        if fpath.name not in files_right:
            continue

        img_l = Image.open(fpath)
        img_r = Image.open(dir_right / fpath.name)

        w_l, h_l = img_l.size
        w_r, h_r = img_r.size
        h = max(h_l, h_r)

        combined = Image.new("RGB", (w_l + w_r, h))
        combined.paste(img_l, (0, 0))
        combined.paste(img_r, (w_l, 0))
        combined.save(out_dir / fpath.name, quality=args.quality)
        count += 1

    print(f"Done. {count} frames concatenated -> {out_dir}")


if __name__ == "__main__":
    main()
