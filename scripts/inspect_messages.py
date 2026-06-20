import argparse
from mcap.reader import make_reader
from mcap_protobuf.decoder import DecoderFactory as ProtobufDecoderFactory


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mcap", required=True)
    parser.add_argument("--topic", required=True)
    parser.add_argument("--num", type=int, default=5)
    args = parser.parse_args()

    count = 0

    with open(args.mcap, "rb") as f:
        reader = make_reader(f, decoder_factories=[ProtobufDecoderFactory()])

        for schema, channel, message, msg in reader.iter_decoded_messages():
            if channel.topic != args.topic:
                continue

            print("=" * 80)
            print("topic:", channel.topic)
            print("schema:", schema.name)
            print("msg type:", type(msg))
            print("format:", repr(getattr(msg, "format", None)))
            print("frame_id:", repr(getattr(msg, "frame_id", None)))
            print("data type:", type(msg.data))
            print("data length:", len(msg.data))
            print("first 32 bytes hex:", bytes(msg.data[:32]).hex())
            print("first 32 bytes raw:", bytes(msg.data[:32]))

            count += 1
            if count >= args.num:
                break

    print("inspected:", count)


if __name__ == "__main__":
    main()