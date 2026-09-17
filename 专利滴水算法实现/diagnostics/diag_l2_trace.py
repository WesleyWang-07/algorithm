# -*- coding: utf-8 -*-
"""
l2 轨迹诊断：固定起点列，逐格打印 (r, c | j, Q, k, s) 与动作，定位"右滑"从哪一格开始。

用法：
  python diag_l2_trace.py            # 跑默认的对比组（真值列 77 / 本实现选中列 46）
  python diag_l2_trace.py 77         # 只看某一列
  python diag_l2_trace.py 77 60 46   # 看多列

注意：本脚本**不修改任何现有代码**，只 import 现有函数做只读诊断。
"""
import os

import sys as _sys
_sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sys

import numpy as np
from PIL import Image

from improved_droplet import (drop_improved, is_open, _q_decision, _neighbors,
                              _theta_j, _G7, _step_patent)
from segment import bidirectional_segment

GLYPHS = os.path.join(os.path.dirname(__file__), '..', '..', '文献', 'glyphs')


def load_ink(path, thresh=128):
    im = Image.open(path).convert('RGB')
    a = np.array(im).astype(int)
    return (a[..., 0] < thresh) & (a[..., 1] < thresh) & (a[..., 2] < thresh)


def trace(ink, r0, c0, g, terminate_at=None, max_rows=200):
    """复刻 drop_improved 的主循环，但把每一步的决策细节记下来。"""
    H, W = ink.shape
    g = tuple(g)
    nbrs = _neighbors(g)
    r, c = r0, c0
    k, s = 0, 0
    oriented = False
    visited = {(r, c)}
    rows = []

    for step_i in range(8 * (H + W) + 2000):
        if terminate_at is not None and (r, c) in terminate_at and step_i > 0:
            rows.append(dict(step=step_i, r=r, c=c, note='STOP terminate_at'))
            break

        if not oriented:
            j0, Q0 = _q_decision(ink, r, c, g, k)
            if Q0 == 0 or Q0 < 0 or j0 in (6, 7):
                oriented = True
                rows.append(dict(step=step_i, r=r, c=c, k=k, s=s,
                                 note='ORIENT (rng=None -> k 不变) Q=%s j=%s' % (Q0, j0)))

        j, Q = _q_decision(ink, r, c, g, k)

        # 记录胜出邻点的原始权值，便于看 Q 是怎么算出来的
        raw = None
        if j is not None:
            raw = _G7[j] * _theta_j(j, k)
        # 同时记录"如果 k=0 会选谁"——用于判断取向是否改变了选择
        j_chk, Q_chk = _q_decision(ink, r, c, g, 0)

        rows.append(dict(step=step_i, r=r, c=c, g=g, k=k, s=s, j=j, Q=Q,
                         raw=raw, j_k0=j_chk, Q_k0=Q_chk))

        # 用一个副本调 _step_patent 拿动作（避免污染）
        act = _step_patent(ink, r, c, g, k, s)
        if act[0] == 'reflow':
            nk, ns = act[3], act[4]
            if ns > 5:
                rows[-1]['act'] = 'REF(>5)->melt'
                r, c = r + g[0], c + g[1]
                s, k = 0, nk
            else:
                rows[-1]['act'] = 'reflow'
                k, s = nk, ns
        elif act[0] == 'melt':
            rows[-1]['act'] = 'melt'
            r, c, k, s = act[1], act[2], act[3], act[4]
        else:
            nr, nc = act[1], act[2]
            if (nr, nc) == (r, c) or (nr, nc) in visited:
                rows[-1]['act'] = 'move->visited! melt'
                r, c = r + g[0], c + g[1]
                s = 0
            else:
                rows[-1]['act'] = 'move'
                r, c, k, s = nr, nc, act[3], act[4]

        visited.add((r, c))
        if r < 0 or r >= H or c < 0 or c >= W:
            rows.append(dict(step=step_i + 1, r=r, c=c, note='EXIT boundary'))
            break

        if len(rows) > max_rows * 4:
            rows.append(dict(r=r, c=c, note='too many'))
            break

    return rows


def summarize(ink, c0, g=(1, 0), terminate_at=None, verbose_steps=80):
    H, W = ink.shape
    rows = trace(ink, 0, c0, g, terminate_at=terminate_at)

    # 展平：只保留"位置发生变化"的记录行 + 关键 note
    positions = [(rows[0]['r'], rows[0]['c'])]
    for w in rows[1:]:
        if (w.get('r'), w.get('c')) != positions[-1]:
            positions.append((w.get('r'), w.get('c')))

    end = positions[-1]
    print(f'\n{"="*78}')
    print(f'起点列 c0={c0}  起点相对宽 x_rel={c0/(W-1):.3f}')
    print(f'  终点 = {end}   落点列相对宽 x_rel={end[1]/(W-1):.3f}')
    print(f'  列漂移 = {end[1]-c0:+d}   行数 = {end[0]}')
    print(f'  路径格点数 = {len(positions)}   停因 = {rows[-1].get("note", rows[-1].get("act",""))}')
    print(f'{"-"*78}')
    print(f'  {"step":>4} {"r":>4} {"c":>4} {"k":>2} {"s":>2} {"j":>3} {"Q":>3} '
          f'{"j(k=0)":>7} {"Q(k=0)":>7}  act')
    shown = 0
    for w in rows:
        if 'act' in w or 'note' in w:
            note = w.get('act') or w.get('note')
            j_s = '-' if w.get('j') is None else str(w['j'])
            Q_s = '-' if w.get('Q') is None else str(w['Q'])
            jk_s = '-' if w.get('j_k0') is None else str(w['j_k0'])
            Qk_s = '-' if w.get('Q_k0') is None else str(w['Q_k0'])
            if 'note' in w:
                print(f'  {w["step"]:>4} {w["r"]:>4} {w["c"]:>4} '
                      f'{w.get("k",""):>2} {w.get("s",""):>2}   *  '
                      f'   *        *       *  {note}')
            else:
                print(f'  {w["step"]:>4} {w["r"]:>4} {w["c"]:>4} {w["k"]:>2} {w["s"]:>2} '
                      f'{j_s:>3} {Q_s:>3} {jk_s:>7} {Qk_s:>7}  {note}')
            shown += 1
            if shown >= verbose_steps:
                print(f'  ... (共 {sum(1 for x in rows if "act" in x or "note" in x)} 条记录，已截断)')
                break
    return positions, rows


def main():
    cols = [int(x) for x in sys.argv[1:]] or [77, 46]
    path = os.path.join(GLYPHS, 'p49_img4.png')
    ink = load_ink(path)
    H, W = ink.shape
    print(f'[p49_img4 / 谱字A] {W}x{H}')

    # 先用编排层跑一遍，拿到 l1 集合作为 terminate_at
    res = bidirectional_segment(ink, metric='D', metric2='B')
    l1_set = set(res['l1_path'])
    xi, yi = res['intersect']
    print(f'编排层结果: l1起点{res["start1"]} l2起点{res["start2"]} 锚点({xi},{yi}) '
          f'x_rel={yi/(W-1):.3f}')
    print(f'l2 指标 = {res["metrics2"]}')

    for c0 in cols:
        if not is_open(ink, 0, c0):
            print(f'\n*** c0={c0} 上缘被墨迹占据，跳过')
            continue
        summarize(ink, c0, g=(1, 0), terminate_at=l1_set, verbose_steps=120)


if __name__ == '__main__':
    main()
