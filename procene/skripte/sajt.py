"""Javna stranica kao samostalan sajt (GitHub Pages), van Claude naloga.

  python3 procene/skripte/sajt.py <folder sajta>      npr. /home/claude/evroliga-plus-minus

Upisuje u folder sajta samo ovo:
  index.html   procene/javno/predlozi.html umotan u pun HTML dokument
  .nojekyll    da GitHub Pages ne obrađuje fajlove
U sajt ne ide ništa drugo iz repozitorijuma: ni model, ni skripte, ni ponude, ni minusi/.
"""
import os, sys

KOREN = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

GLAVA = """<!doctype html>
<html lang="sr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="robots" content="noindex,nofollow">
<style>:root{color-scheme:light;box-sizing:border-box;padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}body{margin:0;padding:0;font:14px -apple-system,BlinkMacSystemFont,sans-serif}img{max-width:100%}[hidden]{display:none!important}</style>
</head>
<body>
"""
REP = "\n</body>\n</html>\n"


def main(folder):
    src = os.path.join(KOREN, 'procene', 'javno', 'predlozi.html')
    telo = open(src, encoding='utf-8').read()
    # oznaka za Claude prikaz nije potrebna na običnom sajtu
    telo = telo.replace('<meta name="claude:viewport-fit-sides" content="cover">\n', '')
    # naslov i fontovi idu u <head>
    import re
    glava_dod = ''.join(re.findall(r'<title>.*?</title>\n|<link [^>]*>\n', telo))
    for x in re.findall(r'<title>.*?</title>\n|<link [^>]*>\n', telo):
        telo = telo.replace(x, '', 1)
    os.makedirs(folder, exist_ok=True)
    with open(os.path.join(folder, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(GLAVA.replace('</head>', glava_dod + '</head>') + telo + REP)
    open(os.path.join(folder, '.nojekyll'), 'w').close()
    print('sajt:', os.path.join(folder, 'index.html'))


if __name__ == '__main__':
    main(sys.argv[1])
