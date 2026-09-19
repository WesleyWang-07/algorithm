# -*- coding: utf-8 -*-
"""
B 指标退化：是"字形不同"造成的，还是"字形自身结构"造成的？
================================================================
判据（可 ASCII 判定）：
  在 l2 起点带内逐列枚举起点 c0，收集**终点列的集合** E = {end_col(c0)}。

  |E| = 1        -> 终点锁定 -> B = |常数 - c0| 是斜率为 -1 的直线 -> 退化
  |E| >= 2       -> 终点会随起点移动 -> B 至少有区分度 -> 不退化（但可能是阶梯）

关键点：这个判据**只用一个字形**就能跑。
  若同一个字形的带内就已经 |E|=1，则"字形不同"既不是原因也不是条件。

三条对照：
  (1) 谱字A 全带        -> 输出 |E| 与阶梯剖面
  (2) 谱字A 左半/右半   -> 分段的 |E|（看是不是阶梯）
  (3) 谱字B 全带        -> 输出 |E|（预期 = 1：不同字形，同样退化）

出图：汇报/figs/fig6_B退化范围.png
  (a) 终点列 vs 起点列（阶梯剖面）：谱字A 两级、谱字B 一级
  (b) B = |终点列 - 起点列| vs 起点列：谱字A 在 c0=46 触零、谱字B 一路线性

⚠️ 读图口径：load_ink（RGB 逐通道 <128）。不要用 convert('L')。
运行：cd 专利滴水算法实现 && python diagnostics/diag_B_degeneracy_scope.py
"""
import os
import sys

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, '..')))

from run_real import load_ink                            # noqa: E402
from segment import bidirectional_segment                # noqa: E402
from improved_droplet import drop_improved, path_metrics, is_open  # noqa: E402

GLYPHS = os.path.abspath(os.path.join(HERE, '..', '..', '文献', 'glyphs'))
OUT = os.path.abspath(os.path.join(HERE, '..', '..', '汇报', 'figs'))

plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['savefig.facecolor'] = 'white'
plt.rcParams['figure.facecolor'] = 'white'

INK = '#2b2b2b'
RED = '#d62728'
GRN = '#2e9e4f'
BLU = '#1f77b4'
ORG = '#e08b1a'
GRY = '#9aa0a6'


def l2_band(W):
    """segment.py 的 δ2 = (2/7 M, 3/5 M)。"""
    w1 = int(round(2 / 7 * W)); w2 = int(round(3 / 5 * W))
    return list(range(max(1, w1), min(W - 1, w2)))


def scan(ink, cols, l1_set):
    """在给定起点列集合上枚举，返回逐列的 (c0, end_col, B, stopped_by)。"""
    out = []
    for c0 in cols:
        if not is_open(ink, 0, c0):
            continue
        r = drop_improved(ink, 0, c0, (1, 0), terminate_at=l1_set)
        m = path_metrics(r, (1, 0))
        out.append((c0, r['end'][1], m['B'], r['stopped_by']))
    return out


def rle(rows):
    """把 c0->end_col 剖成连续段，看是不是阶梯函数。"""
    segs = []
    for c0, e, _B, _s in rows:
        if segs and segs[-1][2] == e and segs[-1][1] == c0 - 1:
            segs[-1][1] = c0
        else:
            segs.append([c0, c0, e])
    return ' '.join(f'{a}-{b}->{e}' if a != b else f'{a}->{e}' for a, b, e in segs)


def report(tag, rows):
    if not rows:
        print(f'{tag}: (no open entry)')
        return None
    ends = sorted({r[1] for r in rows})
    Bs = sorted({r[2] for r in rows})
    hit = sum(1 for r in rows if r[3] == 'terminate_at')
    print(f'{tag}: n={len(rows):3d}  |E|={len(ends):2d} '
          f'end_cols={ends[:8]}{"..." if len(ends) > 8 else ""}  '
          f'B_range=[{min(Bs)},{max(Bs)}]  reach_l1={hit}/{len(rows)}')
    return ends


def per_glyph(name, fname, subbands=None):
    ink = load_ink(os.path.join(GLYPHS, fname))
    H, W = ink.shape
    res = bidirectional_segment(ink, metric='D', metric2='B')
    l1_set = set(res['l1_path'])
    band = l2_band(W)
    pick = res['start2'][1]
    print(f'\n=== {name}  ({fname})  {W}x{H}   '
          f'band=[{band[0]},{band[-1]}] ({len(band)} cols)  '
          f'algo_pick={pick}  anchor_col={res["intersect"][1]}')
    prof = scan(ink, band, l1_set)
    report('  full band  ', prof)
    print(f'  阶梯剖面   : {rle(prof)}')
    if subbands:
        mid = (band[0] + band[-1]) // 2
        for tg, cols in (('  left half  ', [c for c in band if c <= mid]),
                         ('  right half ', [c for c in band if c > mid])):
            report(tg, scan(ink, cols, l1_set))
    return dict(name=name, band=band, prof=prof, pick=pick,
                anchor=res['intersect'][1])


def make_fig(data):
    """图6：(a) 终点列阶梯剖面  (b) B 随起点列的走向。"""
    fig, (axR, axB) = plt.subplots(2, 1, figsize=(9.8, 7.0), sharex=True,
                                   gridspec_kw=dict(height_ratios=[1, 1],
                                                    hspace=0.16))
    colors = [RED, BLU]
    for d, col in zip(data, colors):
        c0 = [r[0] for r in d['prof']]
        endc = [r[1] for r in d['prof']]
        Bs = [r[2] for r in d['prof']]
        lab = f"{d['name']}（带 [{d['band'][0]},{d['band'][-1]}]）"
        axR.step(c0, endc, where='post', color=col, lw=2.4, label=lab)
        axR.plot(c0, endc, ls='none', marker='o', ms=3.5, color=col, alpha=0.6)
        axB.plot(c0, Bs, color=col, lw=2.4, label=lab)
        axB.plot(c0, Bs, ls='none', marker='o', ms=3.5, color=col, alpha=0.6)
        axB.plot([d['pick']], [min(Bs)], marker='*', ms=17, color=ORG,
                 mec='white', mew=1.1, zorder=6)

    axR.set_ylabel('$l_2$ 终点列 $E(c_0)$', fontsize=12, color=INK)
    axR.set_ylim(28, 152)
    axR.grid(alpha=0.25, ls=':')
    axR.legend(fontsize=10.5, loc='center right', framealpha=0.95)
    axR.set_title('终点列是"起点列"的阶梯函数：同一级内终点恒定\n'
                  '（谱字A 两级 46 / 111；谱字B 整整 43 列只有一级 127）',
                  fontsize=13.5, fontweight='bold', color=INK, pad=10,
                  linespacing=1.5)
    # 台阶标注
    axR.annotate('42-49 -> 46', xy=(45.5, 46), xytext=(43, 74), color=RED,
                 fontsize=10.5, fontweight='bold',
                 arrowprops=dict(arrowstyle='-|>', color=RED, lw=1.3))
    axR.annotate('50-87 -> 111', xy=(78, 111), xytext=(63, 88), color=RED,
                 fontsize=10.5, fontweight='bold',
                 arrowprops=dict(arrowstyle='-|>', color=RED, lw=1.3))
    axR.annotate('40-82 -> 127（唯一一级，终点在带外）', xy=(62, 127),
                 xytext=(43, 140), color=BLU, fontsize=10.5,
                 fontweight='bold',
                 arrowprops=dict(arrowstyle='-|>', color=BLU, lw=1.3))

    axB.set_xlabel('$l_2$ 起点列 $c_0$（论文 $\\delta_2$ 带内逐列）', fontsize=12,
                   color=INK)
    axB.set_ylabel('$l_2$ 指标 B', fontsize=12, color=INK)
    axB.set_ylim(0, 118)
    axB.grid(alpha=0.25, ls=':')
    axB.legend(fontsize=10.5, loc='upper center', framealpha=0.95)
    axB.set_title('同一级内 B 单调 => B 只反映"起点离那个通道有多远"\n'
                  '（★ = 算法实际选中；谱字A 触零于 c0=46，即"起点=终点"）',
                  fontsize=13.5, fontweight='bold', color=INK, pad=10,
                  linespacing=1.5)
    axB.annotate('B = 0：起点即终点\nB 对中途偏移完全不敏感', xy=(46, 0),
                 xytext=(50, 22), color=ORG, fontsize=10.5, fontweight='bold',
                 linespacing=1.4,
                 bbox=dict(fc='white', ec=ORG, lw=1.0, alpha=0.95, pad=2.5),
                 arrowprops=dict(arrowstyle='-|>', color=ORG, lw=1.3))

    fig.savefig(os.path.join(OUT, 'fig6_B退化范围.png'), dpi=190,
                bbox_inches='tight')
    plt.close(fig)
    print('\n[fig] ->', os.path.join(OUT, 'fig6_B退化范围.png'))


if __name__ == '__main__':
    print('判据：|E|=1 => B 退化为直线（终点锁定）；|E|>=2 => 阶梯/不退化')
    data = [per_glyph('谱字A (p49_img4)', 'p49_img4.png', subbands=True),
            per_glyph('谱字B (p47_img1)', 'p47_img1.png')]
    make_fig(data)
