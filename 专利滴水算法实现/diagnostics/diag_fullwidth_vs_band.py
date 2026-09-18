# -*- coding: utf-8 -*-
"""
对照实验：起点范围 = 论文 δ 带  vs  专利全宽 [0, M]
====================================================
背景：代码 segment.py 第 87/114 行用论文的 δ1=(2/5N,3/5N) / δ2=(2/7M,3/5M)；
      而专利权利要求 5 写的是 x_o ∈ [0, M]（全宽枚举，无 δ）。
本脚本在真实谱字上逐列/逐行扫描，比较两种范围下的选优结果是否一致。

只读。输出纯 ASCII 数字，便于判定。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from PIL import Image

from improved_droplet import drop_improved, is_open, path_metrics

HERE = os.path.dirname(os.path.abspath(__file__))
G = os.path.join(HERE, '..', '..', '文献', 'glyphs', 'p49_img4.png')

# ⚠️ 输入口径（2026-09-18 修正）：见 diag_l2_selection.py 中的说明 ——
#    convert('L') 会把图内烤着的论文红线当成墨迹，必须按 RGB 逐通道判定。
_a = np.array(Image.open(G).convert('RGB')).astype(int)
ink = (_a[..., 0] < 128) & (_a[..., 1] < 128) & (_a[..., 2] < 128)
H, W = ink.shape
print('IMG %d x %d  (H x W)' % (H, W))

# ---------------- l1 : g=(0,1)，起点 (r0, 0) ----------------
g1 = (0, 1)
band1 = list(range(max(1, int(round(0.4 * H))), min(H - 1, int(round(0.6 * H)))))
full1 = list(range(1, H - 1))
print('l1 BAND rows %d..%d (n=%d) | FULL rows %d..%d (n=%d)'
      % (band1[0], band1[-1], len(band1), full1[0], full1[-1], len(full1)))


def scan_l1(rows, metric):
    best = None
    for r0 in rows:
        if not is_open(ink, r0, 0):
            continue
        res = drop_improved(ink, r0, 0, g1, rng=None)
        m = path_metrics(res, g1)
        if best is None or m[metric] < best[0]:
            best = (m[metric], r0, m, res)
    return best


sel_l1 = {}
for tag, rows in (('BAND', band1), ('FULL', full1)):
    for mt in 'ABCD':
        b = scan_l1(rows, mt)
        if b is None:
            print('l1 %s %s -> NONE' % (tag, mt))
            continue
        print('l1 %s %s -> score=%-4s r0=%-4d ABCD=%s'
              % (tag, mt, b[0], b[1], [b[2][k] for k in 'ABCD']))
        if mt == 'D':
            sel_l1[tag] = b

r_band = sel_l1['BAND'][1]
r_full = sel_l1['FULL'][1]
print('l1 SELECTED  band_r0=%d  full_r0=%d  SAME=%s'
      % (r_band, r_full, r_band == r_full))

# ---------------- l2 : g=(1,0)，起点 (0, c0)，终止于 l1 ----------------
g2 = (1, 0)
band2 = list(range(max(1, int(round(2 / 7 * W))), min(W - 1, int(round(3 / 5 * W)))))
full2 = list(range(1, W - 1))
print('l2 BAND cols %d..%d (n=%d) | FULL cols %d..%d (n=%d)'
      % (band2[0], band2[-1], len(band2), full2[0], full2[-1], len(full2)))

l1_set = set(sel_l1['BAND'][3]['path'])


def scan_l2(cols, metric):
    best = None
    for c0 in cols:
        if not is_open(ink, 0, c0):
            continue
        res = drop_improved(ink, 0, c0, g2, terminate_at=l1_set, rng=None)
        m = path_metrics(res, g2)
        if best is None or m[metric] < best[0]:
            best = (m[metric], c0, m, res)
    return best


sel_l2 = {}
for tag, cols in (('BAND', band2), ('FULL', full2)):
    for mt in 'ABCD':
        b = scan_l2(cols, mt)
        if b is None:
            print('l2 %s %s -> NONE' % (tag, mt))
            continue
        end = b[3]['path'][-1]
        print('l2 %s %s -> score=%-4s c0=%-4d ABCD=%-16s end=%s'
              % (tag, mt, b[0], b[1], str([b[2][k] for k in 'ABCD']), end))
        if mt == 'B':
            sel_l2[tag] = b

c_band = sel_l2['BAND'][1]
c_full = sel_l2['FULL'][1]
print('l2 SELECTED (metric B)  band_c0=%d  full_c0=%d  SAME=%s'
      % (c_band, c_full, c_band == c_full))
print('DONE')
