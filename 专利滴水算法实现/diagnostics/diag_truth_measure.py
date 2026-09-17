# -*- coding: utf-8 -*-
"""
【精确量测】图3-23 四面板（论文真值）的 l2 终点列，与 0.524 对账。

方法：在每张 147x185 面板里分离出"绿色像素"（l2 竖切线的颜色），
      找绿色像素的每一行的中心列，终点 = 绿色最低行的中心列。
同时分离红色像素（l1 横切线）用于确认交点。
"""
import os
import numpy as np
from PIL import Image

TH = os.path.join(os.path.dirname(__file__), 'out', 'thesis')
GLY = os.path.join(os.path.dirname(__file__), '..', '..', '文献', 'glyphs')


def analyze(path, tag):
    im = Image.open(path).convert('RGB')
    a = np.array(im).astype(int)
    H, W = a.shape[:2]
    R, G, B = a[..., 0], a[..., 1], a[..., 2]

    # 绿色：G 明显高于 R、B
    green = (G > 100) & (G - R > 50) & (G - B > 50)
    # 红色：R 明显高于 G、B
    red = (R > 100) & (R - G > 50) & (R - B > 50)
    # 黑色墨迹
    black = (R < 100) & (G < 100) & (B < 100)

    print(f'\n{"="*76}')
    print(f'{tag}  尺寸 {W}x{H}')
    print(f'  绿像素 {green.sum()}  红像素 {red.sum()}  黑像素 {black.sum()}')

    if green.sum() == 0:
        print('  (无绿色像素)')
        return
    gy, gx = np.where(green)
    print(f'  绿色 rows {gy.min()}..{gy.max()}   cols {gx.min()}..{gx.max()}')

    # 逐行绿线中心列
    print(f'  {"row":>5} {"绿中心列":>10} {"相对宽(c/W)":>12} {"相对宽(c/(W-1))":>14}')
    rows = sorted(set(gy.tolist()))
    for r in rows[::max(1, len(rows)//18)]:
        cols = gx[gy == r]
        cc = cols.mean()
        print(f'  {r:>5} {cc:>10.1f} {cc/W:>12.3f} {cc/(W-1):>14.3f}')

    # 终点 = 绿线最低一行的中心列
    r_end = gy.max()
    cols_end = gx[gy == r_end]
    c_end = cols_end.mean()
    print(f'\n  ★ 绿线终点: row={r_end}  col={c_end:.1f}')
    print(f'     相对宽 c/W      = {c_end/W:.4f}')
    print(f'     相对宽 c/(W-1)  = {c_end/(W-1):.4f}')
    print(f'     vs 声称真值 0.524 -> 差 {c_end/W - 0.524:+.4f} (按 c/W)')

    # 红线水平范围（l1）
    if red.sum():
        ry, rx = np.where(red)
        print(f'  红线 rows {ry.min()}..{ry.max()}  cols {rx.min()}..{rx.max()}')
        # 红线最低点（l1 的终点）
        r_l1 = ry.max()
        cols_l1 = rx[ry == r_l1]
        print(f'  红线最低行 row={r_l1} 中心列={cols_l1.mean():.1f} '
              f'(x_rel={cols_l1.mean()/(W-1):.3f})')


def main():
    print('#' * 76)
    print('# 图3-23 四面板（论文真值线）l2 终点精确量测')
    print('#' * 76)
    for i in range(4):
        p = os.path.join(TH, f'p47_img{i}_147x185.png')
        if os.path.exists(p):
            analyze(p, f'图3-23 面板{i} (p47_img{i})')

    # 对照：p49_img4（我们的输入）是否含绿线
    p = os.path.join(GLY, 'p49_img4.png')
    if os.path.exists(p):
        analyze(p, 'p49_img4 (本项目输入)')

    # 也看 p48_img4（之前判定为图3-25）
    p = os.path.join(TH, 'p48_img4_147x185.png')
    if os.path.exists(p):
        analyze(p, 'p48_img4 (原判图3-25)')


if __name__ == '__main__':
    main()
