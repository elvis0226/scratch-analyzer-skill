"""Export explicitly selected SB3 blocks and their provenance."""
import argparse, hashlib, json, subprocess, sys, zipfile
from pathlib import Path
from sb3_to_scratchblocks import convert

ROOT = Path(__file__).resolve().parent.parent

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('sb3', type=Path)
    parser.add_argument('config', type=Path)
    parser.add_argument('--out', type=Path, default=ROOT / 'output/fragments')
    parser.add_argument('--node', default='node')
    args = parser.parse_args()
    config = json.loads(args.config.read_text(encoding='utf-8-sig'))
    with zipfile.ZipFile(args.sb3) as z:
        project = json.loads(z.read('project.json'))
    sprite = config['sprite']
    blocks = next(t['blocks'] for t in project['targets'] if t['name'] == sprite)
    args.out.mkdir(parents=True, exist_ok=True)
    manifest = {'source_sb3_sha256': hashlib.sha256(args.sb3.read_bytes()).hexdigest(), 'sprite': sprite, 'fragments': []}
    for fragment in config['fragments']:
        slug = fragment['slug']
        if not slug or any(c not in 'abcdefghijklmnopqrstuvwxyz0123456789-' for c in slug):
            raise ValueError(f'Invalid slug: {slug}')
        block_id = fragment['block_id']
        seen = set()
        def visit(i):
            if not i or i in seen: return
            if i not in blocks: raise ValueError(f'Missing block {i}')
            seen.add(i)
            b = blocks[i]
            for v in b.get('inputs', {}).values():
                for item in v[1:]:
                    if isinstance(item, str): visit(item)
            visit(b.get('next'))
        visit(block_id)
        code = convert(args.sb3, sprite, block_id=block_id)
        wrapper = code.startswith('<')
        if wrapper:
            code = f'if {code} then\nend'
        txt, svg = args.out / (slug + '.txt'), args.out / (slug + '.svg')
        txt.write_text(code + '\n', encoding='utf8')
        subprocess.run([args.node, str(Path(__file__).with_name('render_svg.cjs').resolve()), str(txt), str(svg)], check=True)
        manifest['fragments'].append({**fragment, 'source_block_ids': sorted(seen), 'image': svg.name, 'image_sha256': hashlib.sha256(svg.read_bytes()).hexdigest(), 'text': txt.name, 'display_wrapper': 'empty if block added for display' if wrapper else None})
    (args.out / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf8')

if __name__ == '__main__': main()
