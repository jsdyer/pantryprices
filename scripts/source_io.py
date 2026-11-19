"""Retrieve official releases and write a single validated browser edition."""
from datetime import datetime, timezone
import json
from pathlib import Path
from tempfile import NamedTemporaryFile

ROOT = Path(__file__).resolve().parents[1]

def archives():
    return json.loads((ROOT / "sources" / "releases.json").read_text())

def publish(data):
    if not data["count"] or not data["start"] or not data["end"]:
        raise ValueError("An empty edition cannot be published")
    data["retrieved"] = datetime.now(timezone.utc).date().isoformat()
    folder = ROOT / "web" / "data"
    folder.mkdir(exist_ok=True)
    with NamedTemporaryFile(mode="w", dir=folder, delete=False, encoding="utf-8") as temp:
        json.dump(data,temp,ensure_ascii=False,separators=(",",":"))
        temp.write("\n")
    Path(temp.name).replace(folder / "edition.json")
    print(data["count"],data["coverage"],"retrieved",data["retrieved"])
