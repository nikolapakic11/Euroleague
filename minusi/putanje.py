"""Zajedničke putanje za skripte u minusi/ i baza/skripte/. Sve se računa od korena repozitorija,
pa skripte rade bez obzira gde je repozitorijum preuzet. Koren se može zadati i promenljivom EUROLEAGUE_ROOT."""
import os
ROOT = os.environ.get('EUROLEAGUE_ROOT') or os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
BAZA = os.path.join(ROOT, 'baza')
MINUSI = os.path.join(ROOT, 'minusi')
# lokalna kopija aplikacije sa stanjem (rezervna kopija iz repozitorijuma); skripte pišu u novi fajl, nikad preko ove kopije
APP_HTML = os.path.join(MINUSI, 'aplikacija', 'evroliga-minusi.html')
# privremeni izlazi (kandidati, planovi) ne idu u repozitorijum
RADNO = os.environ.get('EUROLEAGUE_RADNO') or '/tmp/euroleague_radno'
os.makedirs(RADNO, exist_ok=True)
