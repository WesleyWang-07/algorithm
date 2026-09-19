# -*- coding: utf-8 -*-
"""
论文参考线 vs 本实现轨迹 —— 逐字对照图（只读，产出一张 PNG）
=============================================================================
产出：`../../汇报/figs/fig4_论文真值对照.png`

为什么需要这张图
----------------
`eval_paper_tables.py` 给出的是数字（一致率、穿墨量），但数字回答不了
"差在哪里"。本脚本把两条线叠在同一张干净字形上，让差异自己现形。

三列的含义
----------
  第 1 列「论文参考线」：从论文结果格 `tab33_rNN_A.png` 里**读**出来的红/绿线，
                        画在**干净字形**（`tab33_rNN_glyph.png`）上。
                        为什么不直接用结果格原图：结果格的绿线盖住了墨迹，
                        会把字挖出缺口，看起来会误导。
  第 2 列「本实现」：默认配置 l1=D / l2=B 跑出来的两条轨迹。
  第 3 列「叠加」：淡色 = 论文线，实色 = 本实现。想看差异只看这一列。

⚠️ 只用表3-3（10 个不粘连字）
    表3-4 的 #3/#4/#5 结果格与字形格**不是同一块画布**（高度差 +25/+36/-10，
    剔除线像素后仍差 5000+ 像素），坐标不可比。判据见 `eval_paper_tables.py`。

配色约定沿用论文：l1 = 红，l2 = 绿。

运行：cd 专利滴水算法实现/diagnostics && python diag_paper_lines_overlay.py
"""
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

from run_real import load_ink                      # noqa: E402 统一 RGB 读图口径
from segment import bidirectional_segment           # noqa: E402

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt                    # noqa: E402

GLYPH_DIR = os.path.join(HERE, '..', '..', '文献', 'glyphs', 'table33_34')
OUT_PNG = os.path.join(HERE, '..', '..', '汇报', 'figs', 'fig4_论文真值对照.png')

RED = np.array([220, 40, 40], dtype=np.uint8)
GREEN = np.array([30, 160, 70], dtype=np.uint8)
RED_L = np.array([250, 190, 190], dtype=np.uint8)
GREEN_L = np.array([185, 230, 200], dtype=np.uint8)


def mask_red(a):
    return (a[..., 0] > 150) & (a[..., 1] < 110) & (a[..., 2] < 110)


def mask_green(a):
    return (a[..., 1] > 130) & (a[..., 0] < 120) & (a[..., 2] < 120)


def canvas(ink):
    """干净字形 -> RGB 白底黑字画布。"""
    H, W = ink.shape
    img = np.full((H, W, 3), 255, dtype=np.uint8)
    img[ink] = 0
    return img


def paint_path(img, path, color, H, W, thick=1):
    """把轨迹点画到画布上（出界点跳过 —— 轨迹末点 x 可能等于 W）。"""
    for (y, x) in path:
        for dy in range(-(thick // 2), thick // 2 + 1):
            yy = y + dy
            if 0 <= yy < H and 0 <= x < W:
                img[yy, x] = color


def paint_mask(img, mask, color):
    m = mask[:img.shape[0], :img.shape[1]]
    img[m] = color
    return img


def build_panels(idx):
    """返回 (论文线画布, 本实现画布, 叠加画布)。"""
    gp = os.path.join(GLYPH_DIR, 'tab33_r%02d_glyph.png' % idx)
    pp = os.path.join(GLYPH_DIR, 'tab33_r%02d_A.png' % idx)
    ink = load_ink(gp)
    H, W = ink.shape
    panel = np.array(Image.open(pp).convert('RGB')).astype(int)

    res = bidirectional_segment(ink)              # 默认 l1=D, l2=B
    l1, l2 = res['l1_path'], res['l2_path']

    p1 = canvas(ink)
    paint_mask(p1, mask_red(panel), RED)
    paint_mask(p1, mask_green(panel), GREEN)

    p2 = canvas(ink)
    paint_path(p2, l1, RED, H, W)
    paint_path(p2, l2, GREEN, H, W)

    p3 = canvas(ink)
    paint_mask(p3, mask_red(panel), RED_L)
    paint_mask(p3, mask_green(panel), GREEN_L)
    paint_path(p3, l1, RED, H, W)
    paint_path(p3, l2, GREEN, H, W)

    return p1, p2, p3, res


def main():
    plt.rcParams['font.sans-serif'] = ['Microsoft YaHei']
    plt.rcParams['axes.unicode_minus'] = False

    n = 10
    fig, axes = plt.subplots(n, 3, figsize=(8.2, 16.0), dpi=150)
    heads = ['(1) 论文参考线', '(2) 本实现  l1=D, l2=B', '(3) 叠加：淡=论文  实=本实现']

    for r in range(n):
        idx = r + 1
        p1, p2, p3, res = build_panels(idx)
        xi, yi = res['intersect']
        for c, img in enumerate((p1, p2, p3)):
            ax = axes[r][c]
            ax.imshow(img, interpolation='nearest')
            ax.set_xticks([])
            ax.set_yticks([])
            for s in ax.spines.values():
                s.set_color('#cccccc')
            if r == 0:
                ax.set_title(heads[c], fontsize=9, pad=6)
            if c == 0:
                ax.set_ylabel('第%d号' % idx, fontsize=9)
        axes[r][1].set_xlabel('锚点 (行%d, 列%d)' % (xi, yi), fontsize=7, labelpad=1)

    fig.suptitle('论文参考线 与 本实现轨迹 逐字对照（论文表3-3 的 10 个不粘连谱字，干净字形）',
                 fontsize=10.5, y=0.995)
    fig.text(0.5, 0.004,
             '红线 = l1（上下切分）  绿线 = l2（左右切分）。表3-4（粘连字）因结果图与字形图不同画布，未列入。',
             ha='center', fontsize=8, color='#444444')
    fig.tight_layout(rect=(0, 0.012, 1, 0.985))

    os.makedirs(os.path.dirname(OUT_PNG), exist_ok=True)
    fig.savefig(OUT_PNG, facecolor='white')
    plt.close(fig)
    print('OUT', os.path.abspath(OUT_PNG))


if __name__ == '__main__':
    main()
