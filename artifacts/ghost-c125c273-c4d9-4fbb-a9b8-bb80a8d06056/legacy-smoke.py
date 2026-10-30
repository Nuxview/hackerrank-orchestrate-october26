"""Fresh synthetic intent + explicit image proof; never processes dataset labels."""

import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from transport import CONFIG, MODEL, ROOT, RUN_ID, RuntimeFailure, invoke, validate_intents

REQUESTS = [
    {"case_id": "negative", "request_text": "Remove promotional emails only. Keep my account and invoices."},
    {"case_id": "negated", "request_text": "Do not delete my account; send me an export instead."},
    {"case_id": "affirmative", "request_text": "Delete my account, not just promotional emails."},
    {"case_id": "mixed", "request_text": "No borres mi cuenta. Solo quiero una copia de mis datos."},
    {"case_id": "multilingual", "request_text": "Veuillez supprimer mon compte et toutes mes données personnelles."},
]
EXPECTED = dict(negative=False, negated=False, affirmative=True, mixed=False, multilingual=True)


def main():
    artifacts = ROOT / "artifacts" / RUN_ID
    artifacts.mkdir(parents=True, exist_ok=True)
    image = artifacts / "synthetic-attachment.png"
    executable = shutil.which("magick") or shutil.which("convert")
    if executable is None:
        raise RuntimeFailure("ImageMagick is required for this synthetic image smoke only")
    source = ("Support attachment\nResource: fixture_attachment\n"
              "Subject: fixture_user\nOwner email: fixture@example.test\n"
              "Belongs only to this subject\nCaptured: 2026-04-10T10:00:00Z")
    if not image.exists():
        subprocess.run([executable, "-background", "white", "-fill", "black",
                        "-font", "DejaVu-Sans", "-pointsize", "24", "label:" + source,
                        "-strip", str(image)], check=True, timeout=30, capture_output=True)
    ocr = subprocess.check_output(["tesseract", str(image), "stdout"],
                                  text=True, stderr=subprocess.DEVNULL, timeout=30)
    prompt = (Path(__file__).with_name("intent.md").read_text(encoding="utf-8")
              + "\nFor this synthetic smoke, return an object instead of the top-level array: "
              + '{"intents": [intent objects], "image": {"resource_id": string, '
              + '"subject_id": string, "owner_email": string, "supporting_quote": string}}. '
              + "Read the attached image. Its quote must be a literal image substring. "
              + "No tools or other context may be used.\n<untrusted-source-json>\n"
              + json.dumps(REQUESTS, ensure_ascii=False) + "\n</untrusted-source-json>")
    record_path = artifacts / "isolated-image-intent-smoke-2.json"
    if record_path.exists():
        record = json.loads(record_path.read_text(encoding="utf-8"))
        if (record.get("run_id") != RUN_ID or record.get("model") != MODEL
                or record.get("error")
                or record.get("prompt_sha256") != hashlib.sha256(prompt.encode()).hexdigest()
                or record.get("config_sha256") != hashlib.sha256(CONFIG.read_bytes()).hexdigest()
                or record.get("attachment_sha256") != hashlib.sha256(image.read_bytes()).hexdigest()):
            raise RuntimeFailure("Recorded smoke does not match this run's inputs/config/model")
        print("Revalidating this run's recorded smoke; no new provider call")
    else:
        record = invoke(prompt, "isolated-image-intent-smoke-2", artifacts, attachment=image)
    response = record["response"]
    if not isinstance(response, dict) or set(response) != {"intents", "image"}:
        raise RuntimeFailure("Invalid smoke response schema")
    result = validate_intents(response["intents"], REQUESTS)
    visual = response["image"]
    if (result != EXPECTED or not isinstance(visual, dict)
            or set(visual) != {"resource_id", "subject_id", "owner_email", "supporting_quote"}
            or visual["resource_id"] != "fixture_attachment"
            or visual["subject_id"] != "fixture_user"
            or visual["owner_email"] != "fixture@example.test"
            or not isinstance(visual["supporting_quote"], str)
            or not visual["supporting_quote"].strip()
            or visual["supporting_quote"] not in source
            or " ".join(visual["supporting_quote"].split()) not in " ".join(ocr.split())):
        raise RuntimeFailure("Synthetic image or intent failed independent expected results/OCR")
    print("PASS: five intent decisions, exact synthetic image identifiers and grounded quote")
    print("session", record["session_id"], "tokens", record["tokens"])


if __name__ == "__main__":
    main()
