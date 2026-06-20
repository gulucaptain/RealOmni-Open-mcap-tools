from collections import Counter
from mcap.reader import make_reader
import sys

mcap_path = sys.argv[1]

counter = Counter()

with open(mcap_path, "rb") as f:
    reader = make_reader(f)

    for schema, channel, message in reader.iter_messages():
        counter[channel.topic] += 1

for topic, count in counter.items():
    print(repr(topic), count)