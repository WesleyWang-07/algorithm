# -*- coding: utf-8 -*-
"""
关键格点局部放大：在 c0=77 路径的转折格 (21,77)、(80,103) 附近打印 ink 窗口 + 7 邻点权值表。

目的：看清"Q=4 侧滑"到底是绕行（绕过黑块）还是误滑（本可直落）。
只读诊断，不改任何代码。
"""
import os

import sys as _sys
_sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from PIL import Image

from improved_droplet import _neighbors, _q_decision, _theta_j, _G7

GLYPHS = os.path.join(os.path.dirname(__file__), '..', '..', '文献', 'glyphs')


def load_ink(path, thresh=128):
    im = Image.open(path).convert('RGB')
    a = np.array(im).astype(int)
    return (a[..., 0] < thresh) & (a[..., 1] < thresh) & (a[..., 2] < thresh)


def show_window(ink, r, c, g, k, half=6, tag=''):
    """打印以 (r,c) 为中心的 ink 窗口，并在窗口里标注 7 个邻点位置。"""
    H, W = ink.shape
    nb = {j: _neighbors(g)[j] for j in range(1, 8)}
    # 反向映射：(dr,dc) -> j
    pos2j = {(dr, dc): j for j, (dr, dc) in nb.items()}

    print(f'\n--- 窗口 {tag}  中心 (r={r}, c={c})  g={g} k={k} ---')
    hdr = '      ' + ''.join(f'{cc%100:>3}' for cc in range(c - half, c + half + 1))
    print(hdr)
    for rr in range(r - half, r + half + 1):
        line = f'  {rr:>4}'
        for cc in range(c - half, c + half + 1):
            if rr == r and cc == c:
                ch = ' @ '          # 水滴当前位
            elif (rr - r, cc - c) in pos2j:
                ch = f' {pos2j[(rr - r, cc - c)]} '  # 邻点编号
            else:
                ch = ' . ' if (0 <= rr < H and 0 <= cc < W and not ink[rr, cc]) else ' # '
            # 邻点若为黑，显示为 X 覆盖
            if ch != ' @ ' and (rr - r, cc - c) in pos2j:
                if not (0 <= rr < H and 0 <= cc < W) or ink[rr, cc]:
                    ch = f'X{pos2j[(rr-r, cc-c)]} '
            line += ch
        print(line)
    print('  图例: # = 黑(墨迹)  数字 = 白邻点(编号j)  X数字 = 该邻点是黑  . = 更远的空白  @ = 水滴')

    # 权值表
    print(f'\n  j : 位置(Δr,Δc)   z(白=1)   g_j   o_j   z*g*o')
    jj, QQ = _q_decision(ink, r, c, g, k)
    for j in range(1, 8):
        dr, dc = nb[j]
        rr, cc = r + dr, c + dc
        z = 1 if (0 <= rr < H and 0 <= cc < W and not ink[rr, cc]) else 0
        # 越界按白
        if not (0 <= rr < H and 0 <= cc < W):
            z = 1
        o = _theta_j(j, k)
        prod = z * _G7[j] * o
        mark = '  <== 胜出' if j == jj else ''
        star = ' (z=0 跳过)' if z == 0 else ''
        print(f'  {j} : ({dr:+d},{dc:+d})          {z}      {_G7[j]:>2}   {o:>+2}    '
              f'{prod:>+3}{star}{mark}')
    print(f'  => Q = {QQ}  , 胜出 j = {jj}')


def main():
    ink = load_ink(os.path.join(GLYPHS, 'p49_img4.png'))
    H, W = ink.shape
    print(f'[p49_img4] {W}x{H}')
    g = (1, 0)

    # 三个关键格：转折开始 (21,77)、纯直落段中一点 (50,103) 作对照、第二次侧滑 (80,103)
    for (r, c, tag) in [(20, 77, 'r=20 直落最后一格'),
                        (21, 77, 'r=21 开始侧滑 (j=4)'),
                        (22, 79, 'r=22 c=79 前右对角'),
                        (30, 102, 'r=30 c=102 侧滑收尾'),
                        (50, 103, 'r=50 c=103 纯直落段'),
                        (80, 103, 'r=80 c=103 第二次侧滑')]:
        show_window(ink, r, c, g, 0, half=6, tag=tag)

    # 逐列竖直空隙深度剖面：从 r=0 往下，每列第一段连续空白有多深
    print(f'\n{"="*78}')
    print('竖直空隙深度剖面（每列从顶部起第一段连续空白的深度）')
    print('  列  深度   说明')
    for c in range(0, W, 3):
        d = 0
        while d < H and not ink[d, c]:
            d += 1
        bar = '#' * min(d // 2, 40)
        print(f'  {c:>3} {d:>5}   {bar}')
    print('\n  （本实现 l2 起点带 = δ2 ∈ (2/7·W, 3/5·W) '
          f'= ({int(round(2/7*W))}, {int(round(3/5*W))})，真值列 c0≈{int(round(0.524*(W-1)))}）')


if __name__ == '__main__':
    main()
