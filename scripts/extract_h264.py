import argparse
import shutil
import subprocess
from pathlib import Path

from tqdm import tqdm
from mcap.reader import make_reader
from mcap_protobuf.decoder import DecoderFactory as ProtobufDecoderFactory


def dump_h264_from_mcap(mcap_path, topic, h264_path, max_packets=None):
    h264_path = Path(h264_path)
    h264_path.parent.mkdir(parents=True, exist_ok=True)

    packet_count = 0
    total_bytes = 0
    skipped_count = 0
    seen_formats = set()

    with open(mcap_path, "rb") as f, open(h264_path, "wb") as fout:
        reader = make_reader(
            f,
            decoder_factories=[ProtobufDecoderFactory()],
        )

        for schema, channel, message, msg in tqdm(reader.iter_decoded_messages()):
            if channel.topic != topic:
                continue

            fmt = getattr(msg, "format", "").lower()
            seen_formats.add(fmt)

            if fmt != "h264":
                skipped_count += 1
                continue

            data = bytes(msg.data)

            # 你的数据已经是 Annex-B 格式，开头是 00 00 00 01
            # 所以这里直接拼接写入即可
            fout.write(data)

            packet_count += 1
            total_bytes += len(data)

            if max_packets is not None and packet_count >= max_packets:
                break

    print("========== MCAP Dump Summary ==========")
    print(f"Input MCAP:       {mcap_path}")
    print(f"Topic:            {topic}")
    print(f"Seen formats:     {seen_formats}")
    print(f"H264 packets:     {packet_count}")
    print(f"Skipped packets:  {skipped_count}")
    print(f"Total bytes:      {total_bytes}")
    print(f"Saved h264:       {h264_path}")
    print("=======================================")

    if packet_count == 0:
        raise RuntimeError(
            "No h264 packets extracted. Please check topic name or message format."
        )

    return h264_path


def run_cmd(cmd):
    print("\nRunning command:")
    print(" ".join(str(x) for x in cmd))
    subprocess.run(cmd, check=True)


def convert_h264_to_mp4(h264_path, mp4_path, fps):
    if shutil.which("ffmpeg") is None:
        raise RuntimeError("ffmpeg not found. Please install ffmpeg first.")

    mp4_path = Path(mp4_path)
    mp4_path.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        "ffmpeg",
        "-y",
        "-f",
        "h264",
        "-framerate",
        str(fps),
        "-i",
        str(h264_path),
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        str(mp4_path),
    ]

    run_cmd(cmd)
    print(f"\nMP4 saved to: {mp4_path}")


def convert_h264_to_jpg(h264_path, frames_dir, fps):
    if shutil.which("ffmpeg") is None:
        raise RuntimeError("ffmpeg not found. Please install ffmpeg first.")

    frames_dir = Path(frames_dir)
    frames_dir.mkdir(parents=True, exist_ok=True)

    output_pattern = frames_dir / "%06d.jpg"

    cmd = [
        "ffmpeg",
        "-y",
        "-f",
        "h264",
        "-framerate",
        str(fps),
        "-i",
        str(h264_path),
        str(output_pattern),
    ]

    run_cmd(cmd)
    print(f"\nJPG frames saved to: {frames_dir}")


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("--mcap", required=True, help="Input .mcap file")
    parser.add_argument("--topic", required=True, help="H264 CompressedImage topic")
    parser.add_argument("--out", required=True, help="Output directory")
    parser.add_argument("--fps", type=float, default=30.0, help="Output FPS")

    parser.add_argument(
        "--mode",
        choices=["mp4", "jpg", "both", "h264"],
        default="both",
        help="Output mode",
    )

    parser.add_argument(
        "--keep_h264",
        action="store_true",
        help="Keep intermediate .h264 file",
    )

    parser.add_argument(
        "--max_packets",
        type=int,
        default=None,
        help="Only extract first N h264 packets for debugging",
    )

    args = parser.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    h264_path = out_dir / "stream.h264"
    mp4_path = out_dir / "output.mp4"
    frames_dir = out_dir / "frames"

    dump_h264_from_mcap(
        mcap_path=args.mcap,
        topic=args.topic,
        h264_path=h264_path,
        max_packets=args.max_packets,
    )

    if args.mode == "h264":
        print(f"Only dumped h264 stream: {h264_path}")
        return

    if args.mode in ["mp4", "both"]:
        convert_h264_to_mp4(
            h264_path=h264_path,
            mp4_path=mp4_path,
            fps=args.fps,
        )

    if args.mode in ["jpg", "both"]:
        convert_h264_to_jpg(
            h264_path=h264_path,
            frames_dir=frames_dir,
            fps=args.fps,
        )

    if not args.keep_h264:
        try:
            h264_path.unlink()
            print(f"\nRemoved intermediate h264 file: {h264_path}")
        except Exception as e:
            print(f"\nFailed to remove intermediate h264 file: {e}")


if __name__ == "__main__":
    main()