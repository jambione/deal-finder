import json
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(__file__))

import flights as flights_module
import oil as oil_module
import sentiment as sentiment_module
from analyzer import analyze

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "output")


def write_json(filename, data):
    path = os.path.join(OUTPUT_DIR, filename)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=str)
    print(f"[output] wrote {path}")


def main():
    now = datetime.now(timezone.utc).isoformat()
    print(f"[main] starting flight tracker run at {now}")

    flights_today = flights_module.fetch()
    oil = oil_module.fetch()
    sentiment = sentiment_module.fetch()

    analysis, history = analyze(flights_today, oil, sentiment)

    write_json("flights.json", {"generated_at": now, "flights": flights_today})
    write_json("oil.json", oil)
    write_json("sentiment.json", sentiment)
    write_json("analysis.json", analysis)
    write_json("history.json", history)

    print(f"[main] done — {len(flights_today)} prices, recommendation={analysis['recommendation']}")


if __name__ == "__main__":
    main()
