"""
Unified pipeline for processing RealOmni-Open Dataset MCAP files.

Automatically detects camera topics, extracts H.264 video streams,
converts to MP4/JPEG frames, and optionally concatenates stereo pairs.
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path

from mcap.reader import make_reader


def discover_camera_topics(mcap_path):
    """Auto-detect camera topics matching /robot*/sensor/camera*/compressed."""
    pattern = re.compile(r"^/robot\d+/sensor/camera\d+/compressed$")
    topics = set()

    with open(mcap_path, "rb") as f:
        reader = make_reader(f)
        for schema, channel, message in reader.iter_messages():
            if pattern.match(channel.topic):
                topics.add(channel.topic)

    return sorted(topics)


def topic_to_dirname(topic):
    """Convert topic like /robot0/sensor/camera0/compressed to robot0_camera0."""
    match = re.match(r"^/(robot\d+)/sensor/(camera\d+)/compressed$", topic)
    if match:
        return f"{match.group(1)}_{match.group(2)}"
    return topic.strip("/").replace("/", "_")


def run_extraction(mcap_path, topic, out_dir, fps, mode):
    """Run extract_h264.py for a single topic."""
    script = Path(__file__).resolve().parent / "extract_h264.py"
    cmd = [
        sys.executable,
        str(script),
        "--mcap", str(mcap_path),
        "--topic", topic,
        "--out", str(out_dir),
        "--fps", str(fps),
        "--mode", mode,
    ]
    print(f"\n{'='*60}")
    print(f"Extracting: {topic} -> {out_dir}")
    print(f"{'='*60}")
    subprocess.run(cmd, check=True)


def run_concat(base_dir, dir_pairs):
    """Concatenate stereo frame pairs side-by-side."""
    from PIL import Image

    for dir_left, dir_right in dir_pairs:
        frames_left = base_dir / dir_left / "frames"
        frames_right = base_dir / dir_right / "frames"

        if not frames_left.exists() or not frames_right.exists():
            print(f"Skipping concat: {frames_left} or {frames_right} not found")
            continue

        out_dir = base_dir / f"concat_{dir_left}_{dir_right}"
        out_dir.mkdir(exist_ok=True)

        files_left = sorted(f for f in frames_left.iterdir() if f.suffix == ".jpg")
        files_right = {f.name for f in frames_right.iterdir() if f.suffix == ".jpg"}

        count = 0
        for fpath in files_left:
            if fpath.name not in files_right:
                continue
            img_l = Image.open(fpath)
            img_r = Image.open(frames_right / fpath.name)

            w_l, h_l = img_l.size
            w_r, h_r = img_r.size
            h = max(h_l, h_r)

            combined = Image.new("RGB", (w_l + w_r, h))
            combined.paste(img_l, (0, 0))
            combined.paste(img_r, (w_l, 0))
            combined.save(out_dir / fpath.name, quality=95)
            count += 1

        print(f"\nConcat: {count} frames -> {out_dir}")


def main():
    parser = argparse.ArgumentParser(
        description="Process RealOmni-Open Dataset MCAP files"
    )
    parser.add_argument("--mcap", required=True, help="Input .mcap file path")
    parser.add_argument("--fps", type=float, default=30.0, help="Output FPS (default: 30)")
    parser.add_argument(
        "--mode",
        choices=["mp4", "jpg", "both", "h264"],
        default="both",
        help="Output mode (default: both)",
    )
    parser.add_argument(
        "--concat",
        action="store_true",
        help="Concatenate stereo pairs (robot0+robot1) side-by-side",
    )
    parser.add_argument(
        "--out-dir",
        type=str,
        default=None,
        help="Base output directory (default: same directory as MCAP file)",
    )
    parser.add_argument(
        "--topics",
        nargs="*",
        default=None,
        help="Specific topics to extract (default: auto-detect all camera topics)",
    )

    args = parser.parse_args()

    mcap_path = Path(args.mcap).resolve()
    if not mcap_path.exists():
        print(f"Error: MCAP file not found: {mcap_path}", file=sys.stderr)
        sys.exit(1)

    base_dir = Path(args.out_dir) if args.out_dir else mcap_path.parent
    base_dir.mkdir(parents=True, exist_ok=True)

    # Discover or use provided topics
    if args.topics:
        topics = args.topics
    else:
        print("Discovering camera topics...")
        topics = discover_camera_topics(mcap_path)

    if not topics:
        print("Error: No camera topics found in MCAP file.", file=sys.stderr)
        sys.exit(1)

    print(f"\nFound {len(topics)} camera topic(s):")
    for t in topics:
        print(f"  {t}")

    # Extract each topic
    dirnames = []
    for topic in topics:
        dirname = topic_to_dirname(topic)
        dirnames.append(dirname)
        out_path = base_dir / dirname
        run_extraction(mcap_path, topic, out_path, args.fps, args.mode)

    # Concatenate stereo pairs if requested
    if args.concat and args.mode in ["jpg", "both"]:
        # Find pairs: robot0_camera0 + robot1_camera0, etc.
        pairs = []
        camera_groups = {}
        for d in dirnames:
            match = re.match(r"robot(\d+)_(camera\d+)", d)
            if match:
                camera_id = match.group(2)
                camera_groups.setdefault(camera_id, []).append(d)

        for cam_id, dirs in sorted(camera_groups.items()):
            if len(dirs) >= 2:
                dirs_sorted = sorted(dirs)
                pairs.append((dirs_sorted[0], dirs_sorted[1]))

        if pairs:
            print(f"\n{'='*60}")
            print("Concatenating stereo pairs...")
            print(f"{'='*60}")
            run_concat(base_dir, pairs)
        else:
            print("\nNo stereo pairs found to concatenate.")

    print(f"\n{'='*60}")
    print("Pipeline complete!")
    print(f"Output directory: {base_dir}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
