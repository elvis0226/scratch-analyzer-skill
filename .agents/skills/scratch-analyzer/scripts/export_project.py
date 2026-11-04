"""Export all audited top-level scripts as Chinese SVGs and a local review page."""
import argparse
import hashlib
import html
import json
from pathlib import Path
import subprocess
import zipfile

from validate_project import audit

RENDERER = Path(__file__).with_name('render_svg.cjs').resolve()


def export(source, output, node='node'):
    report = audit(source)
    if report['status'] != 'converted':
        raise ValueError('Project must pass structure and script conversion checks before export')
    with zipfile.ZipFile(source) as archive:
        project = json.loads(archive.read('project.json'))
    output.mkdir(parents=True, exist_ok=True)
    manifest = {'source_sb3_sha256': report['source_sb3_sha256'], 'language': 'zh-tw', 'scripts': []}
    sections = []
    escape = lambda value: html.escape(str(value), quote=True)
    for index, script in enumerate(report['scripts'], 1):
        blocks = next(t['blocks'] for t in project['targets'] if t['name'] == script['sprite'])
        seen = set()

        def visit(block_id):
            if not block_id or block_id in seen:
                return
            seen.add(block_id)
            block = blocks[block_id]
            for value in block.get('inputs', {}).values():
                for reference in value[1:]:
                    if isinstance(reference, str):
                        visit(reference)
            visit(block.get('next'))

        visit(script['block_id'])
        stem = f'script-{index:02d}'
        text, image = output / (stem + '.txt'), output / (stem + '.svg')
        text.write_text(script['text'] + '\n', encoding='utf8')
        subprocess.run([node, str(RENDERER), str(text), str(image)], check=True)
        manifest['scripts'].append({key: script[key] for key in ('sprite', 'event', 'block_id')}
                                  | {'source_block_ids': sorted(seen), 'text': text.name,
                                     'text_sha256': hashlib.sha256(text.read_bytes()).hexdigest(),
                                     'image': image.name, 'image_sha256': hashlib.sha256(image.read_bytes()).hexdigest()})
        event = {'event_whenflagclicked': '綠旗啟動', 'control_start_as_clone': '分身產生'}.get(script['event'], script['event'])
        title = escape(script['sprite'] + '：' + event)
        sections.append('<section><h2>' + title + '</h2><div class="image"><img src="' + image.name + '" alt="' + title + '"></div></section>')
    (output / 'scripts-manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    (output / 'preview.html').write_text(
        '<!doctype html><html lang="zh-Hant"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
        '<title>Scratch 原始積木檢視</title><style>body{font-family:system-ui;max-width:1000px;margin:auto;padding:24px;line-height:1.7}'
        '.image{overflow-x:auto;border:1px solid #ddd;padding:12px}img{display:block;max-width:none}section{margin:28px 0}</style>'
        '<h1>' + escape(source.stem) + '：原始積木檢視</h1>'
        '<p>以下為 SB3 的完整腳本擷取，供教師核對；執行驗證與教材審核需另行確認。圖片可左右捲動。</p>'
        + ''.join(sections) + '</html>\n', encoding='utf8')
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('sb3', type=Path)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--node', default='node')
    args = parser.parse_args()
    manifest = export(args.sb3, args.out, args.node)
    print(f'Exported {len(manifest["scripts"])} scripts with source provenance.')


if __name__ == '__main__':
    main()
