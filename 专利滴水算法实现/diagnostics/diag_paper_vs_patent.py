# -*- coding: utf-8 -*-
"""
决策对比诊断：对 c0=77 的完整路径，逐格列出
  ① 本实现（专利2024版：g_j 权值 7..1 + 遇阻随机取向 + 飞溅状态机）
  ② 论文2023版（§3.2.1：Q_i = max_{j=1..5}(z_j·g_j)，只用前5邻点，无对角后向）
  的胜出方向，标出两者分歧点。

论文 §3.2.1 原文依据（文献/论文.md:290-314）：
  "Q_i = max_{j=1..5}(z_j g_j)"  —— 只在前 5 个邻点里取最大
  "沿水平方向的往复循环被检测到后，强制水滴回流到开放侧"
"""
import os

import sys as _sys
_sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from PIL import Image

from improved_droplet import _neighbors, _G7, _theta_j, is_open

GLYPHS = os.path.join(os.path.dirname(__file__), '..', '..', '文献', 'glyphs')


def load_ink(path, thresh=128):
    im = Image.open(path).convert('RGB')
    a = np.array(im).astype(int)
    return (a[..., 0] < thresh) & (a[..., 1] < thresh) & (a[..., 2] < thresh)


# 论文 2023 版：只有 5 个邻点参与（前、前对角、左、右），无后向对角
PAPER_G = {1: 7, 2: 6, 3: 5, 4: 4, 5: 3}


def paper_decision(ink, r, c, g):
    """论文 §3.2.1 的 Q_i = max_{j=1..5}(z_j g_j)，返回 (j, Q)。"""
    nb = _neighbors(g)
    bj, bq = None, None
    for j in range(1, 6):
        dr, dc = nb[j]
        if not is_open(ink, r + dr, c + dc):
            continue
        q = PAPER_G[j]
        if bq is None or q > bq:
            bq, bj = q, j
    if bq is None:
        return None, 0
    return bj, bq


def patent_decision(ink, r, c, g, k=0):
    nb = _neighbors(g)
    bj, bq = None, None
    for j in range(1, 8):
        dr, dc = nb[j]
        if not is_open(ink, r + dr, c + dc):
            continue
        q = _G7[j] * _theta_j(j, k)
        if bq is None or q > bq:
            bq, bj = q, j
    if bq is None:
        return None, 0
    return bj, bq


def main():
    ink = load_ink(os.path.join(GLYPHS, 'p49_img4.png'))
    H, W = ink.shape
    g = (1, 0)
    nb = _neighbors(g)

    print(f'[p49_img4 / 谱字A] {W}x{H}   g={g} (竖直向下)')
    print('论文 §3.2.1 用 5 邻点 {1,2,3,4,5}；本实现(专利2024) 用 7 邻点 {1..7}\n')

    # ---- 沿 c=77 直落时，逐行看两个版本会不会分歧 ----
    print('=' * 88)
    print('【A】固定列 c=77 逐行侦察：两个版本各自的胜出方向')
    print(f'  {"r":>4} {"论文j":>6} {"论文Q":>6} {"本实j":>6} {"本实Q":>6}  分歧?  邻点开闭(1-7)')
    diverge_rows = []
    for r in range(0, 100):
        pj, pq = paper_decision(ink, r, 77, g)
        tj, tq = patent_decision(ink, r, 77, g, 0)
        opens = ''.join('1' if is_open(ink, r + nb[j][0], 77 + nb[j][1]) else '0'
                        for j in range(1, 8))
        mark = ''
        if pj != tj:
            mark = '  <<< 分歧'
            diverge_rows.append((r, pj, pq, tj, tq, opens))
        if r < 26 or mark:
            print(f'  {r:>4} {str(pj):>6} {pq:>6} {str(tj):>6} {tq:>6}  {mark:>8}  {opens}')
    print(f'\n  分歧行数 = {len(diverge_rows)}')
    for d in diverge_rows:
        print(f'    r={d[0]}: 论文选 j={d[1]}(Q={d[2]})  本实现选 j={d[3]}(Q={d[4]})  开闭={d[5]}')

    # ---- 关键：从 c=77 出发，论文版逐格走一遍，看它去哪个列 ----
    print('\n' + '=' * 88)
    print('【B】论文版（5 邻点）从 (0,77) 出发的轨迹')
    r, c = 0, 77
    visited = {(r, c)}
    traj = [(r, c)]
    for step in range(400):
        j, Q = paper_decision(ink, r, c, g)
        if j is None:
            # 全黑：熔断前穿
            nr, nc = r + g[0], c + g[1]
        else:
            dr, dc = nb[j]
            nr, nc = r + dr, c + dc
        if (nr, nc) in visited and (nr, nc) != (r, c):
            pass
        r, c = nr, nc
        if r < 0 or r >= H or c < 0 or c >= W:
            traj.append((r, c)); break
        if (r, c) in visited and step > 2:
            traj.append((r, c)); break
        visited.add((r, c))
        traj.append((r, c))
    print(f'  终点 = {traj[-1]}  x_rel={traj[-1][1]/(W-1):.3f}  格数={len(traj)}')
    print(f'  轨迹: {traj[:60]}')
    if len(traj) > 60:
        print(f'        ...{traj[-20:]}')

    # ---- 对照：论文版从各候选列出发，看哪个能落到真值附近 ----
    print('\n' + '=' * 88)
    print('【C】论文版（5 邻点）从 δ2 带内各列出发的终列')
    print(f'  {"c0":>4} {"x_rel":>7} {"论文版终点列":>12} {"x_rel":>7}  {"本实现终点列":>12} {"x_rel":>7}')
    for c0 in range(42, 89, 2):
        if not is_open(ink, 0, c0):
            continue
        # 论文版
        r, c = 0, c0
        vis = {(r, c)}
        for step in range(500):
            j, Q = paper_decision(ink, r, c, g)
            if j is None:
                nr, nc = r + g[0], c + g[1]
            else:
                dr, dc = nb[j]
                nr, nc = r + dr, c + dc
            r, c = nr, nc
            if not (0 <= r < H and 0 <= c < W):
                break
            if (r, c) in vis:
                break
            vis.add((r, c))
        pc_end = c
        # 本实现
        from improved_droplet import drop_improved
        res = drop_improved(ink, 0, c0, g)
        pc_end2 = res['end'][1]
        flag = '  *' if abs(c0 / (W - 1) - 0.524) < 0.02 else ''
        print(f'  {c0:>4} {c0/(W-1):>7.3f} {pc_end:>12} {pc_end/(W-1):>7.3f}  '
              f'{pc_end2:>12} {pc_end2/(W-1):>7.3f}{flag}')


if __name__ == '__main__':
    main()
