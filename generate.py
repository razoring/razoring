import urllib.request
import re

DARK = ["#151b23", "#033a16", "#196c2e", "#2ea043", "#56d364"]
LIGHT = ["#eff2f5", "#a5e4b3", "#4ac26b", "#2da44e", "#116329"]
COLS, ROWS, CELL, GAP, PAD = 53, 7, 10, 3, 10
GENS, HOLD = 200, 5

req = urllib.request.Request("https://github.com/users/razoring/contributions", headers={'User-Agent': 'Mozilla'})
html = urllib.request.urlopen(req).read().decode()

rows = []
for tr in re.findall(r'<tr[^>]*>(.*?)</tr>', html, re.I | re.S):
    if 'data-level' in tr:
        levels = [int(lvl) for lvl in re.findall(r'data-level="(\d+)"', tr)]
        rows.append(levels)
rows = rows[:ROWS]

# cleanse data / padding rows
for i, r in enumerate(rows):
    if len(r) < COLS:
        rows[i] = [0] * (COLS - len(r)) + r
    else:
        rows[i] = r[-COLS:]

# start sim
grid = [[rows[r][c] for r in range(ROWS)] for c in range(COLS)]
history = [grid]
for _ in range(GENS):
    new = [[0] * ROWS for _ in range(COLS)]
    for c in range(COLS):
        for r in range(ROWS):
            # find neighbours for immigration variant
            nb = []
            for dc in (-1, 0, 1):
                for dr in (-1, 0, 1):
                    if (dc, dr) != (0, 0) and 0 <= c + dc < COLS and 0 <= r + dr < ROWS:
                        if grid[c + dc][r + dr] > 0:
                            nb.append(grid[c + dc][r + dr])
            
            if grid[c][r] > 0:
                new[c][r] = grid[c][r] if len(nb) in (2, 3) else 0
            elif len(nb) == 3:
                new[c][r] = round(sum(nb) / 3)
                
    if new in history:
        break
    history.append(new)
    grid = new

# calculate weighted average colour
avg = []
for g in history:
    total_val = sum(c * (1 + 1 * c) for row in g for c in row)
    weighted_count = max(1, sum((1 + 1 * c) if c > 0 else 0.1 for row in g for c in row))
    avg.append(min(4, round(total_val / weighted_count)))

# hold first/last frames
avg = [avg[0]] * HOLD + avg + [avg[-1]] * HOLD + [avg[0]]

# produce svg
w = COLS * CELL + (COLS - 1) * GAP + 2 * PAD
h = ROWS * CELL + (ROWS - 1) * GAP + 2 * PAD + 15
for name, colors in [("dark", DARK), ("light", LIGHT)]:
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="100%" viewBox="0 0 {w} {h}">',
        f'  <rect width="{w}" height="{h}" fill="transparent" />'
    ]
    
    for c in range(COLS):
        for r in range(ROWS):
            x = PAD + c * (CELL + GAP)
            y = PAD + r * (CELL + GAP)
            
            hist = [g[c][r] for g in history]
            hist = [hist[0]] * HOLD + hist + [hist[-1]] * HOLD + [hist[0]]
            
            if any(hist):
                vals = ";".join([colors[v] for v in hist])
                out.extend([
                    f'  <rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2" ry="2" fill="{colors[hist[0]]}">',
                    f'    <animate attributeName="fill" values="{vals}" dur="{len(history) * 0.2}s" repeatCount="indefinite" />',
                    f'  </rect>'
                ])
            else:
                out.append(f'  <rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2" ry="2" fill="{colors[0]}" />')
                
    text_vals = ";".join([colors[v] for v in avg])
    out.extend([
        f'  <text x="{w - PAD}" y="{h - PAD + 2}" font-family="sans-serif" font-size="10" font-weight="bold" text-anchor="end" fill="{colors[avg[0]]}">Game of Commits',
        f'    <animate attributeName="fill" values="{text_vals}" dur="{len(history) * 0.2}s" repeatCount="indefinite" />',
        f'  </text>',
        f'</svg>'
    ])
    
    with open(f"{name}.svg", "w", encoding="utf-8") as f: f.write("\n".join(out))