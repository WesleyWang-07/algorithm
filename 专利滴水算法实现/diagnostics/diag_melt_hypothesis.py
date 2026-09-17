# -*- coding: utf-8 -*-
"""
【验"熔断斩横笔"假设】

假设：论文 l2 通过熔断在 cols 70~82 斩断"大"字横笔，从而竖直穿缝而下，锚点落在 0.50~0.53。

本脚本回答两个问题：
  Q1: 本实现的熔断分支（Q==0 -> melt 前穿）在 cols 70~82 这段能否被触发？
  Q2: 若不能，是哪条规则抢先消化了状态（让水滴滑走而不是熔断）？

方法：设计一个"只看横笔"的场景——把水滴直接放到 cols 70..82 各列的
      "横笔正上方"位置，看它下一步决策是被挡后熔断，还是滑走。
"""
import os

import sys as _sys
_sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from PIL import Image

from improved_droplet import (_q_decision, _neighbors, _G7, _theta_j, _step_patent,
                              is_open, drop_improved)

GLY = os.path.join(os.path.dirname(__file__), '..', '..', '文献', 'glyphs')


def load_ink(path, thresh=128):
    a = np.array(Image.open(path).convert('RGB')).astype(int)
    return (a[..., 0] < thresh) & (a[..., 1] < thresh) & (a[..., 2] < thresh)


def main():
    ink = load_ink(os.path.join(GLY, 'p49_img4.png'))
    H, W = ink.shape
    g = (1, 0)

    # ---- 先定位"大"字横笔的纵向范围（在 cols 60..95 这些列，墨迹的上下边界）----
    print('=' * 84)
    print('【定位】cols 60..100 各列的墨迹纵向分布（找横笔的上下边）')
    print(f'  {"col":>4} {"x_rel":>7}  墨迹行段（连续段）')
    for c in range(60, 101, 2):
        col = np.where(ink[:, c])[0]
        if len(col) == 0:
            print(f'  {c:>4} {c/(W-1):>7.3f}  (无墨迹)')
            continue
        segs = []
        s = col[0]; p = col[0]
        for v in col[1:]:
            if v - p > 1:
                segs.append((s, p)); s = v
            p = v
        segs.append((s, p))
        txt = '  '.join(f'{a}-{b}' for a, b in segs if b - a >= 1)
        print(f'  {c:>4} {c/(W-1):>7.3f}  {txt}')

    # ---- Q1: 把水滴放在横笔正上方，看决策 ----
    print('\n' + '=' * 84)
    print('【Q1】水滴放在各列"横笔正上方 1 格"，看下一步决策（k=0, s=0）')
    print(f'  {"col":>4} {"x_rel":>7} {"放点(r,c)":>12} {"胜出j":>6} {"Q":>4} {"动作":>22}  邻点开闭(1-7)')
    nb = _neighbors(g)
    for c in range(45, 100, 1):
        col = np.where(ink[:, c])[0]
        if len(col) == 0:
            continue
        # 找该列第一段墨迹的起点
        first_ink = col[0]
        if first_ink < 2:
            continue
        r = first_ink - 1          # 放在横笔正上方一格（该格应为白）
        if not is_open(ink, r, c):
            continue
        j, Q = _q_decision(ink, r, c, g, 0)
        act = _step_patent(ink, r, c, g, 0, 0)
        opens = ''.join('1' if is_open(ink, r + nb[k2][0], c + nb[k2][1]) else '0'
                        for k2 in range(1, 8))
        actname = act[0]
        if act[0] == 'move':
            actname = f'move->({act[1]},{act[2]}) j={j}'
        flag = ''
        if act[0] == 'melt':
            flag = '  <<< 熔断！'
        print(f'  {c:>4} {c/(W-1):>7.3f} {str((r, c)):>12} {str(j):>6} {Q:>4.1f} '
              f'{actname:>22}  {opens}{flag}')

    # ---- Q2: 分析 r=21,c=77 那种格子的完整决策链 ----
    print('\n' + '=' * 84)
    print('【Q2】r=21,c=77（真实路径的被迫侧滑点）完整决策链展开')
    r, c = 21, 77
    nb = _neighbors(g)
    print(f'  当前 (r={r}, c={c})  k=0 s=0')
    for k in (0, 1, -1):
        j, Q = _q_decision(ink, r, c, g, k)
        print(f'    k={k:>2}: 胜出 j={j}  Q={Q}')
        for jj in range(1, 8):
            dr, dc = nb[jj]
            z = 1 if is_open(ink, r + dr, c + dc) else 0
            o = _theta_j(jj, k)
            mark = ' <==' if jj == j else ''
            print(f'        j={jj} ({dr:+d},{dc:+d}) z={z} g={_G7[jj]} o={o:+d} '
                  f'zgo={z*_G7[jj]*o:+d}{mark}')
    act = _step_patent(ink, r, c, g, 0, 0)
    print(f'  -> 动作 = {act}')

    # ---- 反事实：如果这格强制熔断，路径会怎样？ ----
    print('\n' + '=' * 84)
    print('【反事实实验】若在 r=21,c=77 强制熔断前穿 1px，会怎样？')
    print('  （前穿 = 在墨迹上穿 1 格，然后从 (22,77) 继续；看能否竖直落下去）')
    r, c = 21, 77
    r += 1                     # 前穿
    print(f'  前穿后到 (r={r}, c={c})，该格墨迹={ink[r, c]}')
    # 从前穿后继续走
    for step in range(8):
        j, Q = _q_decision(ink, r, c, g, 0)
        act = _step_patent(ink, r, c, g, 0, 0)
        print(f'    step{step}: (r={r},c={c}) j={j} Q={Q} act={act[0]}'
              f'{"->" + str(act[1:3]) if act[0] == "move" else ""}')
        if act[0] == 'move':
            r, c = act[1], act[2]
        elif act[0] == 'melt':
            r, c = act[1], act[2]
        else:
            break
        if r >= H:
            break

    # ---- 统计：整张图在 cols 40..100 区间能不能形成"竖直穿缝" ----
    print('\n' + '=' * 84)
    print('【几何判定】cols 40..100 区间，每一列从顶部到 l1 之间有多少墨迹"厚度"需要穿越')
    print(f'  {"col":>4} {"x_rel":>7} {"顶部墨迹段":>18} {"需穿越厚度":>10}')
    for c in range(40, 101, 3):
        col = np.where(ink[:, c])[0]
        if len(col) == 0:
            continue
        # 只看 rows 0..96（l1 位置）之间的墨迹
        seg = col[col <= 96]
        if len(seg) == 0:
            print(f'  {c:>4} {c/(W-1):>7.3f} {"(无)":>18} {0:>10}')
            continue
        # 找第一段
        s = seg[0]; p = seg[0]; segs = []
        for v in seg[1:]:
            if v - p > 1:
                segs.append((s, p)); s = v
            p = v
        segs.append((s, p))
        thickness = sum(b - a + 1 for a, b in segs)
        print(f'  {c:>4} {c/(W-1):>7.3f} {str(segs[0]):>18} {thickness:>10}  '
              f'（共{len(segs)}段）')


if __name__ == '__main__':
    main()
