import json
import re
import sys
import os

PATH = "tmp_resp.json"

if not os.path.exists(PATH):
    print(f"ERROR: {PATH} not found")
    sys.exit(1)

with open(PATH, "r", encoding="utf8") as f:
    try:
        data = json.load(f)
    except Exception as e:
        print("ERROR: failed to read JSON from", PATH)
        print(str(e))
        sys.exit(1)

output = data.get("output", "")


def extract_json(s: str):
    # direct parse
    try:
        return json.loads(s)
    except Exception:
        pass

    # fenced ```json blocks
    m = re.search(r"```json\s*(.*?)\s*```", s, re.S | re.I)
    if m:
        try:
            return json.loads(m.group(1).strip())
        except Exception:
            pass

    # find first [ ... ]
    start = s.find("[")
    end = s.rfind("]")
    if start != -1 and end != -1 and end > start:
        candidate = s[start:end+1]
        try:
            return json.loads(candidate)
        except Exception:
            pass

    # find first { ... }
    start = s.find("{")
    end = s.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidate = s[start:end+1]
        try:
            return json.loads(candidate)
        except Exception:
            pass

    return None

parsed = extract_json(output)

if parsed is None:
    print("PARSE FAILED: could not find valid JSON in transform output")
    print("--- OUTPUT PREVIEW ---")
    print(output[:2000])
    sys.exit(2)

print("PARSE SUCCESS")
print("Type:", type(parsed).__name__)
if isinstance(parsed, list):
    print("Count:", len(parsed))
    # show first 3 items
    to_show = parsed[:3]
    print(json.dumps(to_show, ensure_ascii=False, indent=2))
else:
    print(json.dumps(parsed, ensure_ascii=False, indent=2))

sys.exit(0)
