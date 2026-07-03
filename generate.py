import urllib.request, re

DARK = ["#151b23", "#033a16", "#196c2e", "#2ea043", "#56d364"]
LIGHT = ["#eff2f5", "#a5e4b3", "#4ac26b", "#2da44e", "#116329"]
COLS, ROWS, CELL, GAP, PAD, GENS, HOLD = 53, 7, 10, 3, 10, 200, 5

html = urllib.request.urlopen(urllib.request.Request("https://github.com/users/razoring/contributions", headers={'User-Agent': 'Mozilla'})).read().decode()
rows = [[int(lvl) for lvl in re.findall(r'data-level="(\d+)"', tr)] for tr in re.findall(r'<tr[^>]*>(.*?)</tr>', html, re.I | re.S) if 'data-level' in tr][:ROWS]
rows = [[0]*(COLS-len(r))+r if len(r)<COLS else r[-COLS:] for r in rows]
grid = [[rows[r][c] for r in range(ROWS)] for c in range(COLS)]

history = [grid]
for _ in range(GENS):
    new = [[0]*ROWS for _ in range(COLS)]
    for c in range(COLS):
        for r in range(ROWS):
            nb = [grid[c+x][r+y] for x in (-1,0,1) for y in (-1,0,1) if (x,y)!=(0,0) and 0<=c+x<COLS and 0<=r+y<ROWS and grid[c+x][r+y]>0]
            new[c][r] = grid[c][r] if grid[c][r]>0 and len(nb) in (2,3) else round(sum(nb)/3) if grid[c][r]==0 and len(nb)==3 else 0
    if new in history: break
    history.append(new)
    grid = new

w, h = COLS*CELL+(COLS-1)*GAP+2*PAD, ROWS*CELL+(ROWS-1)*GAP+2*PAD
for name, colors in [("dark", DARK), ("light", LIGHT)]:
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">', f'  <rect width="{w}" height="{h}" fill="{colors[0]}" />']
    for c in range(COLS):
        for r in range(ROWS):
            x, y = PAD+c*(CELL+GAP), PAD+r*(CELL+GAP)
            hist = [g[c][r] for g in history]
            hist = [hist[0]]*HOLD+hist+[hist[-1]]*HOLD+[hist[0]]
            if any(hist):
                vals = ";".join([colors[v] for v in hist])
                out += [f'  <rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2" ry="2" fill="{colors[hist[0]]}">', f'    <animate attributeName="fill" values="{vals}" dur="{len(history)*0.2}s" repeatCount="indefinite" />', '  </rect>']
            else: out.append(f'  <rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2" ry="2" fill="{colors[0]}" />')
    open(f"{name}.svg", "w", encoding="utf-8").write("\n".join(out+['</svg>']))