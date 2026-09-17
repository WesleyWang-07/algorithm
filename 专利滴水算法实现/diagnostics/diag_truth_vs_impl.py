# -*- coding: utf-8 -*-
"""
【终极核对】论文真值 l2 的实际形状 vs 本实现从同一列出发的路径。

已量出的事实（diag_truth_measure.py）：
  面板A: 起点 col≈57, rows 0-10；折到 63（rows12-72）；折到 77（rows84-124）；终点 (124, 77)
  面板B: 起点 col=77, rows 0-45；折到 63（rows 55-65）；折回 77（rows 85-90）；终点 (90, 77)
  面板C/D: 起点 col=63, rows 0-65；折到 77（rows 80-92）；终点 (92, 77)

关键观察：面板 A 的绿线最低行 = 124，比其他面板深（B/C/D 是 90/92）。
          而面板 A 的红线也到 row=124。

本脚本：把真值线叠加到 p49_img4 上，并打印真值线经过的每一格是白还是黑，
        由此判断"论文的水滴是否在熔断"。
"""
import os
import numpy as np
from PIL import Image, ImageDraw

TH = os.path.join(os.path.dirname(__file__), 'out', 'thesis')
GLY = os.path.join(os.path.dirname(__file__), '..', '..', '文献', 'glyphs')
OUT = os.path.join(os.path.dirname(__file__), 'out')


def load_ink(path, thresh=128):
    a = np.array(Image.open(path).convert('RGB')).astype(int)
    return (a[..., 0] < thresh) & (a[..., 1] < thresh) & (a[..., 2] < thresh)


def green_cols(path):
    """返回 {row: 绿线中心列}"""
    a = np.array(Image.open(path).convert('RGB')).astype(int)
    R, G, B = a[..., 0], a[..., 1], a[..., 2]
    g = (G > 100) & (G - R > 50) & (G - B > 50)
    out = {}
    for r in range(a.shape[0]):
        cols = np.where(g[r])[0]
        if len(cols):
            out[r] = cols.mean()
    return out


def main():
    ink = load_ink(os.path.join(GLY, 'p49_img4.png'))
    H, W = ink.shape
    print(f'p49_img4: {W}x{H}')

    for i in range(4):
        p = os.path.join(TH, f'p47_img{i}_147x185.png')
        if not os.path.exists(p):
            continue
        gc = green_cols(p)
        if not gc:
            continue
        rows = sorted(gc)
        print(f'\n{"="*76}')
        print(f'图3-23 面板{i}: 真值 l2 逐格墨迹命中检查')
        print(f'  {"row":>4} {"真值col":>8} {"取整":>5} {"该格墨迹?":>10}  说明')

        # 检查每一步真值线是否踩在墨迹上
        on_ink = 0
        checked = 0
        prev_c = None
        for r in rows:
            c = int(round(gc[r]))
            # 真值线一格宽，检查 c-1..c+1
            band = [c - 1, c, c + 1]
            band = [x for x in band if 0 <= x < W]
            is_ink = any(ink[r, x] for x in band)
            if is_ink:
                on_ink += 1
            checked += 1
            if r % 6 == 0 or (prev_c is not None and abs(c - prev_c) >= 3):
                print(f'  {r:>4} {gc[r]:>8.1f} {c:>5} {"黑(熔断!)" if is_ink else "白":>10}  '
                      f'{"列跳变" if prev_c is not None and abs(c - prev_c) >= 3 else ""}')
            prev_c = c
        print(f'  => 共 {checked} 行，其中 {on_ink} 行踩在墨迹上'
              f'（{on_ink/checked*100:.1f}%）')

        # 叠加真值线到本项目输入图
        img = Image.fromarray(np.where(ink, 0, 255).astype(np.uint8), mode='L').convert('RGB')
        d = ImageDraw.Draw(img)
        pts = [(gc[r], r) for r in rows]
        if len(pts) >= 2:
            d.line(pts, fill=(0, 190, 0), width=2)
        d.line([(77, 0), (77, H)], fill=(255, 0, 255), width=1)
        img.save(os.path.join(OUT, f'truth_overlay_panel{i}.png'))
        print(f'  叠加图 -> truth_overlay_panel{i}.png')


if __name__ == '__main__':
    main()
