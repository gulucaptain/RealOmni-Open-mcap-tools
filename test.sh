#!/usr/bin/env bash
# Quick test: extract both camera streams from a sample MCAP file.

set -e

MCAP_FILE="./00001.mcap"

# Option 1: Use unified pipeline (recommended)
python scripts/run_pipeline.py --mcap "$MCAP_FILE" --concat

# Option 2: Manual per-topic extraction
# python scripts/extract_h264.py \
#   --mcap "$MCAP_FILE" \
#   --topic /robot0/sensor/camera0/compressed \
#   --out robot0_camera0 \
#   --mode both \
#   --fps 30

# python scripts/extract_h264.py \
#   --mcap "$MCAP_FILE" \
#   --topic /robot1/sensor/camera0/compressed \
#   --out robot1_camera0 \
#   --mode both \
#   --fps 30

# python scripts/concat_frames.py \
#   --left robot0_camera0/frames \
#   --right robot1_camera0/frames \
#   --out concat_output
