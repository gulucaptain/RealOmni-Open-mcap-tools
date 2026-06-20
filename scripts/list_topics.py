from mcap.reader import make_reader
import sys

mcap_path = sys.argv[1]

seen = set()

with open(mcap_path, "rb") as f:
    reader = make_reader(f)

    for schema, channel, message in reader.iter_messages():
        key = channel.id
        if key in seen:
            continue
        seen.add(key)

        schema_name = schema.name if schema else "None"
        schema_encoding = schema.encoding if schema else "None"

        print("topic:", channel.topic)
        print("  message_encoding:", channel.message_encoding)
        print("  schema:", schema_name)
        print("  schema_encoding:", schema_encoding)
        print()