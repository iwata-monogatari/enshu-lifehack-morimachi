"""Check that basic-information disclaimers do not deny cited research on the same page."""
import json
import re
from pathlib import Path
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent.parent


def main():
    errors = []
    checked = 0
    for folder, dataset, key in [('temple/temples', 'temples.json', 'temples'), ('shrine/shrines', 'shrines.json', 'shrines')]:
        rows = json.loads((ROOT / 'data' / dataset).read_text(encoding='utf-8-sig'))[key]
        for row in rows:
            path = ROOT / folder / row['slug'] / 'index.html'
            soup = BeautifulSoup(path.read_text(encoding='utf-8'), 'html.parser')
            text = soup.get_text(' ', strip=True)
            research = soup.select_one('.deep-research')
            researched = research.get_text(' ', strip=True) if research else ''
            checked += 1
            if row.get('saijin') and '御祭神については、今回参照した公開情報から確かな表記を得られませんでした' in text:
                errors.append(f'{path.relative_to(ROOT)}: recorded shrine deity and unknown-deity disclaimer coexist')
            if row.get('main_deity') not in (None, '', '未確認') and '本尊については、今回参照した公開資料から確かな案内を得られませんでした' in text:
                errors.append(f'{path.relative_to(ROOT)}: recorded temple deity and unknown-deity disclaimer coexist')
            if researched and any(word in researched for word in ['本尊は', '大日如来', '阿弥陀如来']) and '本尊については、今回参照した公開資料から確かな案内を得られませんでした' in text:
                errors.append(f'{path.relative_to(ROOT)}: cited research and blanket deity denial coexist')
            if researched and re.search(r'[0-9]{3,4}年', researched) and 'このページでは付け加えていません' in text:
                errors.append(f'{path.relative_to(ROOT)}: dated research and blanket history denial coexist')
            if researched and '公開資料にない本尊、御朱印、拝観条件、連絡先は補っていません' in text:
                errors.append(f'{path.relative_to(ROOT)}: outdated blanket source disclaimer')
    t27 = BeautifulSoup((ROOT / 'temple/temples/t27/index.html').read_text(encoding='utf-8'), 'html.parser').get_text(' ', strip=True)
    if '仙巌禅忠' in t27 or '仙応全忠' not in t27 or '白龍頭観音' not in t27:
        errors.append('t27: tourism-source name or principal deity mismatch')
    print(f'Sacred consistency: {checked} pages, {len(errors)} errors')
    for error in errors:
        print(error)
    return bool(errors)


if __name__ == '__main__':
    raise SystemExit(main())
