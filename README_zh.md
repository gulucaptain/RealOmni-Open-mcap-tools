# 10Kh RealOmni-Open MCAP 工具集

[![Python 3.8+](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

[English](./README.md) | 中文

用于从 [10Kh RealOmni-Open 数据集](https://www.genrobot.ai/data/open-dataset) MCAP 文件中提取和处理视频数据的工具集。

![示例](./examples/sample_output/concat/000001.jpg)

## 概述

RealOmni-Open 数据集以 [MCAP](https://mcap.dev/) 格式存储多模态机器人传感器数据。每个 `.mcap` 文件包含来自多个机器人摄像头的 H.264 编码视频流（以 `foxglove.CompressedImage` protobuf 消息形式存储）。

本工具集提供以下功能：
- **提取** MCAP 文件中的 H.264 视频流
- **转换** 为 MP4 视频和/或 JPEG 帧序列（通过 ffmpeg）
- **拼接** 双目摄像头图像对为左右并排图像

## 环境要求

- Python >= 3.8
- [ffmpeg](https://ffmpeg.org/)（系统安装）

```bash
# 安装 ffmpeg
brew install ffmpeg        # macOS
sudo apt install ffmpeg    # Ubuntu/Debian

# 安装 Python 依赖
pip install -r requirements.txt
```

## 快速开始

```bash
# 处理 MCAP 文件（自动检测所有摄像头 topic，输出 MP4 + JPEG 帧）
python scripts/run_pipeline.py --mcap path/to/00001.mcap

# 同时生成双目拼接图像
python scripts/run_pipeline.py --mcap path/to/00001.mcap --concat

# 仅提取 JPEG 帧
python scripts/run_pipeline.py --mcap path/to/00001.mcap --mode jpg

# 自定义输出目录和帧率
python scripts/run_pipeline.py --mcap path/to/00001.mcap --out-dir ./output --fps 30
```

## 输出目录结构

```
output/
├── robot0_camera0/
│   ├── frames/
│   │   ├── 000001.jpg
│   │   ├── 000002.jpg
│   │   └── ...
│   └── output.mp4
├── robot1_camera0/
│   ��── frames/
│   │   └── ...
│   └── output.mp4
└── concat_robot0_camera0_robot1_camera0/   # 使用 --concat 时生成
    ├── 000001.jpg
    └── ...
```

## 脚本说明

| 脚本 | 功能描述 |
|------|----------|
| `scripts/run_pipeline.py` | 统一入口 — 自动发现 topic 并运行完整流水线 |
| `scripts/extract_h264.py` | 核心提取 — 从 MCAP 中导出 H.264，通过 ffmpeg 转换为 MP4/JPEG |
| `scripts/concat_frames.py` | 后处理 — 将双目帧图像对左右拼接 |
| `scripts/list_topics.py` | 工具 — 列出 MCAP 文件中的所有 topic |
| `scripts/count_messages.py` | 工具 — 统计每个 topic 的消息数量 |
| `scripts/inspect_messages.py` | 调试 — 检查原始图像消息字节 |

## 详细用法

### 统一流水线

```bash
python scripts/run_pipeline.py --mcap <file> [OPTIONS]
```

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--mcap` | （必填） | 输入 `.mcap` 文件路径 |
| `--fps` | `30` | 输出帧率 |
| `--mode` | `both` | 输出模式：`mp4`、`jpg`、`both`、`h264` |
| `--concat` | 关闭 | 拼接双目图像对为左右并排 |
| `--out-dir` | MCAP 文件所在目录 | 基础输出目录 |
| `--topics` | 自动检测 | 指定要提取的 topic |

### 单 Topic 提取

```bash
python scripts/extract_h264.py \
  --mcap 00001.mcap \
  --topic /robot0/sensor/camera0/compressed \
  --out robot0_camera0 \
  --mode both \
  --fps 30
```

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--mcap` | （必填） | 输入 `.mcap` 文件路径 |
| `--topic` | （必填） | H.264 CompressedImage topic 名称 |
| `--out` | （必填） | 输出目录 |
| `--fps` | `30` | 输出帧率 |
| `--mode` | `both` | `mp4`、`jpg`、`both` 或 `h264` |
| `--keep_h264` | 关闭 | 保留中间 `.h264` 流文件 |
| `--max_packets` | 全部 | 仅提取前 N 个数据包（用于调试） |

### 帧拼接

```bash
python scripts/concat_frames.py \
  --left robot0_camera0/frames \
  --right robot1_camera0/frames \
  --out concat_output
```

### 检查工具

```bash
# 列出 MCAP 文件中的所有 topic
python scripts/list_topics.py 00001.mcap

# 统计每个 topic 的消息数量
python scripts/count_messages.py 00001.mcap

# 检查原始消息数据（前 5 条消息）
python scripts/inspect_messages.py --mcap 00001.mcap --topic /robot0/sensor/camera0/compressed --num 5
```

## 处理流水线

```
input.mcap
│
├─ [自动发现摄像头 topic]
│   例如 /robot0/sensor/camera0/compressed
│        /robot1/sensor/camera0/compressed
│
├─ 提取 H.264 流 ──► robot0_camera0/stream.h264（临时文件）
│   ├─ ffmpeg ──► robot0_camera0/output.mp4
│   └─ ffmpeg ──► robot0_camera0/frames/%06d.jpg
│
├─ 提取 H.264 流 ──► robot1_camera0/stream.h264（临时文件）
│   ├─ ffmpeg ──► robot1_camera0/output.mp4
│   └─ ffmpeg ──► robot1_camera0/frames/%06d.jpg
│
└─ [可选] 拼接双目图像对
    └─ concat_robot0_camera0_robot1_camera0/%06d.jpg
```

## 数据格式说明

- **MCAP**：时序传感器数据的二进制容器格式（[规范](https://mcap.dev/spec)）
- **消息模式**：`foxglove.CompressedImage`（protobuf 编码）
- **视频编码**：H.264，Annex-B 格式（NAL 单元以 `0x00000001` 起始码分隔）
- **Topic 命名规则**：`/robot{N}/sensor/camera{M}/compressed`

## 许可证

[MIT](LICENSE)
