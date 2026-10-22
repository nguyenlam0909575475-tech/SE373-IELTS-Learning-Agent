"""Extract only the known May 2023 PDF layout; fail on other editions."""
import argparse
import hashlib
import json
from pathlib import Path

import pymupdf

try:
    from .descriptor_data import ROOT, SOURCE_URL, VERSION, CRITERIA, validate_dataset
    from .download_descriptors import EXPECTED_SHA256
except ImportError:
    from descriptor_data import ROOT, SOURCE_URL, VERSION, CRITERIA, validate_dataset
    from download_descriptors import EXPECTED_SHA256


def extract(pdf):
    content = Path(pdf).read_bytes()
    digest = hashlib.sha256(content).hexdigest()
    if digest != EXPECTED_SHA256:
        raise ValueError('Source PDF SHA256 differs from the verified May 2023 source')
    chunks, provenance, policies = [], {}, []
    with pymupdf.open(stream=content, filetype='pdf') as doc:
        if len(doc) != 9 or 'Updated May 2023' not in doc[0].get_text():
            raise ValueError('Expected the nine-page May 2023 source PDF')
        for task, pages in [('task1', (2, 3, 4)), ('task2', (6, 7, 8))]:
            band = 9
            for p in pages:
                page = doc[p]
                drawings = page.get_drawings()
                rows = sorted([x['rect'] for x in drawings if x['type'] == 'f' and 12 < x['rect'].x0 < 14 and x['rect'].y0 > 110], key=lambda r: r.y0)
                headers = sorted([x['rect'] for x in drawings if x['type'] == 'f' and x['rect'].x0 > 49 and 78 < x['rect'].y0 < 80], key=lambda r: r.x0)
                if len(headers) != 4 or len(rows) != (3 if p in (2, 6) else 2 if p in (3, 7) else 5):
                    raise ValueError(f'Unexpected table geometry on page {p + 1}')
                words = page.get_text('words')
                for row in rows:
                    columns = headers if band else [pymupdf.Rect(49, 0, 944, 540)]
                    for index, col in enumerate(columns):
                        selected = [w for w in words if col.x0 <= (w[0]+w[2])/2 < col.x1 and row.y0 <= (w[1]+w[3])/2 < row.y1]
                        # Word coordinates keep neighbouring cells separate even when PDF blocks merge them.
                        text = ' '.join(w[4] for w in sorted(selected, key=lambda w: (round(w[1], 0), w[0])))
                        # Two unmapped punctuation glyphs in this PDF's text layer, checked visually.
                        text = text.replace('accurate \ufffd there', 'accurate – there').replace('candidate\ufffds', 'candidate’s')
                        if not text:
                            raise ValueError('Empty source cell')
                        if not band:
                            policies.append({'test_part': task, 'band': 0, 'text': text, 'source_page': p+1})
                        else:
                            criterion = CRITERIA[task][index]
                            cid = f'writing_{task}_{criterion}_b{band}_2023_05'
                            chunks.append(dict(chunk_id=cid, test_part=task, criterion=criterion, band=band, version=VERSION, source_url=SOURCE_URL, text=text))
                            provenance[cid] = {'source_page': p+1, 'bbox': [round(col.x0, 3), round(row.y0, 3), round(col.x1, 3), round(row.y1, 3)]}
                    band -= 1
            if band != -1:
                raise ValueError('Missing bands')
    data = {'meta': {'source_url': SOURCE_URL, 'version': VERSION, 'total_chunks': len(chunks), 'scope': 'Academic; source cells retain labelled General Training clauses', 'normalization': 'PDF line wraps collapsed to spaces; two unmapped punctuation glyphs restored', 'source_sha256': digest}, 'chunks': chunks}
    validate_dataset(data)
    audit = {'source_url': SOURCE_URL, 'source_sha256': data['meta']['source_sha256'], 'cells': provenance, 'band_zero_policies': policies, 'rating_instruction': 'A script must fully fit the positive features of the descriptor at a particular level. Bolded text indicates negative features that will limit a rating.', 'review_status': 'Machine extraction with layout checks; independent human review still required. Bold formatting is not represented in plain text.'}
    return data, audit


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pdf', type=Path, default=ROOT / 'ielts-writing-band-descriptors.pdf')
    args = parser.parse_args()
    data, audit = extract(args.pdf)
    for name, payload in [('writing_descriptors.json', data), ('descriptor_provenance.json', audit)]:
        target = ROOT / 'data/processed' / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('Extracted 72 Task-specific cells and two separate Band 0 policies')


if __name__ == '__main__':
    main()
