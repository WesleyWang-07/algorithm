# -*- coding: utf-8 -*-
"""
非粘连字的失败机制 —— 放大对照图（只读，产出一张 PNG）
=============================================================
产出：`../../汇报/figs/fig5_失败机制.png`

回答的问题
----------
表3-3 的 10 个不粘连谱字里，本实现默认配置（l₂=B）在 #6、#9 上会切穿笔画
（穿墨 9 / 29 像素），#1~#5、#7、#8、#10 却不会。为什么？

答案（本脚本用数据与图共同证明）
--------------------------------
**B = |起点列 − 终点列|，一条"直上直下、锯穿笔画"的路径 B = 0** ——
因为水滴没被偏移过，起点就是终点。B 眼里它与"走干净通道的直路"一样完美。

对"空缺但交错"的字（论文 #7~#10 那一类），δ₂ 带内 B=0 的列往往**不止一个**
（多个吸引子簇的簇边都是 B=0），而选优代码用严格小于比较、**先扫到的赢**：

    tab33#6:  B=0 的列有 67(穿墨9) 与 73~86(穿墨0)  → 选了 67
    tab33#9:  B=0 的列有 52(穿墨29)、78(穿墨0)、101(穿墨13) → 选了 52（最差的一个）

D = d + B + v 把熔断量 d 加进分数，锯墨路径 d>0 被罚：
    #6: D=0 落在干净通道 → 选 73，穿墨 0
    #9: D 最小 4 在 c0=78 → 选 78，穿墨 0

这正是论文 §3.4.3 那句「为了追求更小的偏移量选择了对字符进行熔断初始滴点
对应的路径，导致切分错误」的机制层版本。

三列含义：左 = 本实现 l₂=B（失败，品红为穿墨像素）；
         中 = 本实现 l₂=D（论文最终选择）；右 = 论文参考线。

运行：cd 专利滴水算法实现/diagnostics && python diag_fail_mechanism.py
"""
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

from run_real import load_ink                      # noqa: E402
from improved_droplet import drop_improved, is_open, path_metrics  # noqa: E402
from segment import bidirectional_segment           # noqa: E402

import matplotlib                                   # noqa: E402
matplotlib.use('Agg')
import matplotlib.pyplot as plt                     # noqa: E402

GLYPH_DIR = os.path.join(HERE, '..', '..', '文献', 'glyphs', 'table33_34')
OUT_PNG = os.path.join(HERE, '..', '..', '汇报', 'figs', 'fig5_失败机制.png')

RED = np.array([220, 40, 40], dtype=np.uint8)
GREEN = np.array([30, 160, 70], dtype=np.uint8)
BAD = np.array([200, 30, 200], dtype=np.uint8)      # 品红 = 穿墨像素
RED_L = np.array([250, 190, 190], dtype=np.uint8)
GREEN_L = np.array([185, 230, 200], dtype=np.uint8)


def mask_red(a):
    return (a[..., 0] > 150) & (a[..., 1] < 110) & (a[..., 2] < 110)


def mask_green(a):
    return (a[..., 1] > 130) & (a[..., 0] < 120) & (a[..., 2] < 120)


def canvas(ink):
    H, W = ink.shape
    img = np.full((H, W, 3), 255, dtype=np.uint8)
    img[ink] = 0
    return img


def paint(img, path, color, H, W, thick=1, mark_ink=None):
    for (y, x) in path:
        if not (0 <= y < H and 0 <= x < W):
            continue
        for dy in range(-(thick // 2), thick // 2 + 1):
            yy = y + dy
            if 0 <= yy < H:
                hit = mark_ink is not None and mark_ink[yy, x]
                img[yy, x] = BAD if hit else color


def l2_candidates(ink, l1):
    """枚举 δ₂ 带内每个起点的 (c0, B, D, 穿墨, 路径)。"""
    H, W = ink.shape
    l1set = set(l1)
    w1, w2 = int(round(2 / 7 * W)), int(round(3 / 5 * W))
    out = []
    for c0 in range(max(1, w1), min(W - 1, w2)):
        if not is_open(ink, 0, c0):
            continue
        r = drop_improved(ink, 0, c0, (1, 0), terminate_at=l1set, rng=None)
        m = path_metrics(r, (1, 0))
        cr = sum(1 for (y, x) in r['path'] if 0 <= y < H and 0 <= x < W and ink[y, x])
        out.append(dict(c0=c0, B=m['B'], D=m['D'], cross=cr, path=r['path']))
    return out


def pick(cands, key):
    """与 segment.py 同款选优：严格小于，先扫到的赢。"""
    best = None
    for c in cands:
        if best is None or c[key] < best[key]:
            best = c
    return best


def build(idx):
    ink = load_ink(os.path.join(GLYPH_DIR, 'tab33_r%02d_glyph.png' % idx))
    H, W = ink.shape
    res = bidirectional_segment(ink, metric='D')          # l1 固定 D
    l1 = res['l1_path']
    cands = l2_candidates(ink, l1)
    b_sel = pick(cands, 'B')
    d_sel = pick(cands, 'D')

    panel = np.array(Image.open(os.path.join(
        GLYPH_DIR, 'tab33_r%02d_A.png' % idx)).convert('RGB')).astype(int)
    p3 = canvas(ink)
    p3[mask_red(panel)[:H, :W]] = RED_L
    p3[mask_green(panel)[:H, :W]] = GREEN_L
    return ink, l1, b_sel, d_sel, p3, cands


def main():
    plt.rcParams['font.sans-serif'] = ['Microsoft YaHei']
    plt.rcParams['axes.unicode_minus'] = False

    rows = [6, 9]
    fig, axes = plt.subplots(len(rows), 3, figsize=(8.0, 6.8), dpi=150)
    heads = ['(1) 本实现 l2=B（失败）', '(2) 本实现 l2=D（论文之选）', '(3) 论文参考线']

    for r, idx in enumerate(rows):
        ink, l1, b_sel, d_sel, p3, cands = build(idx)
        H, W = ink.shape
        zeros = [c['c0'] for c in cands if c['B'] == 0]

        for c, (sel, is_paper) in enumerate(((b_sel, False), (d_sel, False), (None, True))):
            ax = axes[r][c]
            img = canvas(ink)
            paint(img, l1, RED, H, W)
            if is_paper:
                img = p3
                sub = '论文画的绿线（起点列恒为 72）'
            else:
                paint(img, sel['path'], GREEN, H, W, thick=1, mark_ink=ink)
                tag = 'B' if sel is b_sel else 'D'
                sub = ('起点列 %d，终点列 %d，B=%d，穿墨 %d 像素'
                       % (sel['c0'], sel['path'][-1][1], sel[tag], sel['cross']))
            ax.imshow(img, interpolation='nearest')
            ax.set_xticks([])
            ax.set_yticks([])
            for s in ax.spines.values():
                s.set_color('#cccccc')
            if r == 0:
                ax.set_title(heads[c], fontsize=9, pad=6)
            ax.set_xlabel(sub, fontsize=7.5, labelpad=2)
            if c == 0:
                ax.set_ylabel('第%d号' % idx, fontsize=9)

    fig.suptitle('非粘连字的失败机制：B 只看"直不直"，不看"切没切到墨"\n'
                 '品红 = l2 轨迹压在笔画上的像素', fontsize=10, y=0.995)
    fig.tight_layout(rect=(0, 0, 1, 0.93))

    os.makedirs(os.path.dirname(OUT_PNG), exist_ok=True)
    fig.savefig(OUT_PNG, facecolor='white')
    plt.close(fig)

    # 控制台摘要（ASCII 可判定）
    for idx in rows:
        ink, l1, b_sel, d_sel, p3, cands = build(idx)
        zeros = [c['c0'] for c in cands if c['B'] == 0]
        print('tab33#%d: B=0 的起点列 = %s' % (idx, zeros))
        print('  B 选中 c0=%d 穿墨=%d | D 选中 c0=%d 穿墨=%d'
              % (b_sel['c0'], b_sel['cross'], d_sel['c0'], d_sel['cross']))
    print('OUT', os.path.abspath(OUT_PNG))


if __name__ == '__main__':
    main()
