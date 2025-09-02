import csv
import json

INPUT_FILE = "data/cwe-top25.csv"
OUTPUT_FILE = "data/aspm_dataset.jsonl"

examples = []

with open(INPUT_FILE, newline='', encoding="utf-8") as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        cwe_id = row.get("CWE-ID", "").strip()
        name = row.get("Name", "").strip()
        desc = row.get("Description", "").strip()

        if not (cwe_id and name and desc):
            continue

        prompt = f"{cwe_id}: {name} detected in application scan"
        completion = (
            f"{desc} This alert indicates a potential weakness. "
            f"Developers should follow OWASP guidance to mitigate."
        )

        examples.append({"prompt": prompt, "completion": completion})

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    for e in examples:
        f.write(json.dumps(e) + "\n")

print(f"✅ Dataset saved as {OUTPUT_FILE} with {len(examples)} examples")
