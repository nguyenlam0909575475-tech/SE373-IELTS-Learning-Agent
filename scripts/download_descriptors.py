"""Download the pinned official source locally; never publish the PDF in Git."""
import argparse
import hashlib
import json
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

try:
    from .descriptor_data import ROOT, SOURCE_URL
except ImportError:
    from descriptor_data import ROOT, SOURCE_URL

EXPECTED_SHA256 = 'e3c88943ef92d98988ce4db454fd7fa8d8435f0b25e9ec667e3720a5c1168d1b'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'ielts-writing-band-descriptors.pdf')
    args = parser.parse_args()
    try:
        with urllib.request.urlopen(SOURCE_URL, timeout=60) as response:
            content = response.read()
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        parser.exit(1, f'Cannot download source: {exc}. Open {SOURCE_URL} in a browser and save the PDF as {args.output}; then run extract_descriptors.py.\n')
    digest = hashlib.sha256(content).hexdigest()
    if not content.startswith(b'%PDF') or digest != EXPECTED_SHA256:
        parser.exit(1, f'Source differs from verified PDF (SHA256={digest}); review before updating the pinned source.\n')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(content)
    provenance = ROOT / 'data/raw/descriptors/download_info.json'
    provenance.parent.mkdir(parents=True, exist_ok=True)
    provenance.write_text(json.dumps({'url': SOURCE_URL, 'downloaded_at': datetime.now(timezone.utc).isoformat(), 'document_version': 'May 2023', 'source_sha256': digest, 'copyright_status': 'Redistribution unverified; local use only pending review.'}, indent=2) + '\n', encoding='utf-8')
    print(f'Downloaded verified source: {args.output}')


if __name__ == '__main__':
    main()
