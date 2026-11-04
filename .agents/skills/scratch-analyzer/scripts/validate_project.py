"""Audit a second SB3 against the existing converter without altering its logic.

Exit 0: every script converted; 1: invalid archive/project; 2: conversion blocked.
This checks structure and conversion, not Scratch runtime behaviour or teaching approval.
"""
import argparse
import ast
from collections import Counter
import hashlib
import html
import json
from pathlib import Path
import zipfile

from sb3_to_scratchblocks import convert


def supported_opcodes():
    tree = ast.parse(Path(__file__).with_name('sb3_to_scratchblocks.py').read_text(encoding='utf8'))
    return sorted({node.comparators[0].value for node in ast.walk(tree)
                   if isinstance(node, ast.Compare) and isinstance(node.left, ast.Name)
                   and node.left.id == 'o' and len(node.ops) == 1
                   and isinstance(node.ops[0], ast.Eq)
                   and isinstance(node.comparators[0], ast.Constant)
                   and isinstance(node.comparators[0].value, str)})


def audit(source):
    supported = set(supported_opcodes())
    with zipfile.ZipFile(source) as archive:
        bad = archive.testzip()
        if bad:
            raise ValueError('ZIP checksum failed: ' + bad)
        project = json.loads(archive.read('project.json'))
        files = set(archive.namelist())
    targets, issues, scripts = [], [], []
    for target in project['targets']:
        blocks = target['blocks']
        counts = Counter(block['opcode'] for block in blocks.values())
        for asset in target.get('costumes', []) + target.get('sounds', []):
            filename = asset.get('md5ext') or asset['assetId'] + '.' + asset['dataFormat']
            if filename not in files:
                issues.append({'sprite': target['name'], 'missing_asset': filename})
        for block_id, block in blocks.items():
            references = [block.get('next'), block.get('parent')]
            for value in block.get('inputs', {}).values():
                references.extend(item for item in value[1:] if isinstance(item, str))
            for reference in references:
                if reference and reference not in blocks:
                    issues.append({'sprite': target['name'], 'block_id': block_id,
                                   'missing_reference': reference})
            if block.get('topLevel') and not block.get('shadow'):
                result = {'sprite': target['name'], 'block_id': block_id,
                          'event': block['opcode']}
                try:
                    result['text'] = convert(source, sprite=target['name'], block_id=block_id)
                    result['status'] = 'converted'
                except (ValueError, KeyError) as error:
                    result.update(status='blocked', error=str(error))
                scripts.append(result)
        targets.append({'sprite': target['name'], 'is_stage': target['isStage'],
                        'block_count': len(blocks), 'opcodes': dict(sorted(counts.items())),
                        'unsupported_opcodes': {op: count for op, count in sorted(counts.items())
                                                if op not in supported}})
    return {'source_file': source.name,
            'source_sb3_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
            'scope': 'Archive/assets/references and existing converter; no game execution or teacher approval.',
            'structure_issues': issues, 'targets': targets, 'scripts': scripts,
            'status': 'invalid' if issues else ('conversion_blocked' if any(s['status'] == 'blocked' for s in scripts) else 'converted'),
            'later_stages': 'SVG and lesson generation require successfully converted scripts and teacher-authored content.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('sb3', type=Path)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.sb3)
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / 'validation.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    escape = lambda value: html.escape(str(value), quote=True)
    rows = ''.join('<tr><td>' + escape(t['sprite']) + '</td><td>' + str(t['block_count'])
                   + '</td><td>' + escape(', '.join(t['unsupported_opcodes']) or '無') + '</td></tr>' for t in result['targets'])
    failures = ''.join('<li><b>' + escape(s['sprite']) + '</b> / ' + escape(s['event'])
                       + '<pre>' + escape(s.get('error', 'converted')) + '</pre></li>' for s in result['scripts'])
    page = ('<!doctype html><html lang="zh-Hant"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>Scratch 第二案例驗證報告</title><style>body{font-family:system-ui;max-width:1000px;margin:auto;padding:24px;line-height:1.7}'
            'table{border-collapse:collapse}td,th{border:1px solid #ccc;padding:10px}pre{white-space:pre-wrap;overflow-wrap:anywhere}</style>'
            '<h1>' + escape(args.sb3.stem) + '：現有流程驗證</h1><p>此頁是技術檢查報告，非學生教材。</p>'
            '<p>檢查結果：' + escape(result['status']) + '。結構問題：' + str(len(result['structure_issues'])) + '。</p>'
            '<p>本工具檢查壓縮檔完整性、素材是否存在、積木連結，以及現有轉換器的實際轉換結果；遊戲執行測試由獨立工具進行。</p>'
            '<table><tr><th>角色</th><th>積木數（含選單）</th><th>尚未支援的 opcode</th></tr>' + rows + '</table>'
            '<h2>逐腳本轉換結果</h2><ul>' + failures + '</ul><h2>後續階段</h2>'
            '<p>此工具只驗證結構與文字轉換。若腳本轉換受阻，須先補足報告列出的積木支援，再驗證中文 SVG 圖像及教學內容；文字轉換成功不代表教材已驗收。</p>'
            '<p>教材需另以教材 JSON 和產生器建置，再進行教師審核；本報告不代表教材已驗收。</p>'
            '<p>來源 SHA-256：<code>' + result['source_sb3_sha256'] + '</code></p></html>')
    (args.out / 'validation.html').write_text(page + '\n', encoding='utf8')
    print(json.dumps({'status': result['status'], 'targets': len(result['targets']),
                      'blocks': sum(t['block_count'] for t in result['targets']),
                      'scripts': len(result['scripts']), 'converted': sum(s['status'] == 'converted' for s in result['scripts']),
                      'structure_issues': len(result['structure_issues'])}, ensure_ascii=False))
    return 1 if result['structure_issues'] else (2 if result['status'] == 'conversion_blocked' else 0)


if __name__ == '__main__':
    raise SystemExit(main())
