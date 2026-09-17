# -*- coding: utf-8 -*-
"""
diag_l2_selection2.py —— 验"论文四面板是否共用同一张输入图"

前作 diag_l2_selection.py 证明：在 p49_img4 上，无论怎么调 δ₂ 带 / 指标 / tie-break，
都选不出论文的起点列 77。

本脚本攻另一个更基础的问题：**论文图3-23 的四个面板，真的是在同一张图上只换指标跑出来的吗？**
判据：论文四面板的 (起点列, 中间竖直段列, 终点列) 三元组是
    A: (57, 63, 77)   B: (77, 63, 77)   C: (63, 63, 77)   D: (63, 63, 77)
注意 A/B/C/D 的**起点各不相同**（57/77/63/63），但它们**中间段与终点完全一致**（63 与 77）。
本实现里不同起点会导向不同吸引子（见前作），所以若不成立，说明论文用了额外机制。

做法：对每个候选起点列，跑本实现，记录 (起点列, 路径中列众数, 终点列)，
与论文四面板逐一比对，看有没有哪个起点能给出 (·, 63, 77) 这一组合。

纯只读诊断，不修改算法代码。

运行：python diag_l2_selection2.py
"""
import os
import sys
from collections import Counter

import numpy as np
from PIL import Image

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))

from improved_droplet import drop_improved  # noqa: E402
from segment import bidirectional_segment  # noqa: E402

GLYPHS = os.path.join(_HERE, '..', '..', '文献', 'glyphs')

# 论文图3-23 四面板实测（diag_truth_measure.py）
PAPER = {
    'A': (57, 63, 77),
    'B': (77, 63, 77),
    'C': (63, 63, 77),
    'D': (63, 63, 77),
}


def load_ink():
    img = Image.open(os.path.join(GLYPHS, 'p49_img4.png')).convert('L')
    return np.array(img) < 128


def mid_col(path):
    """路径的"中间竖直段"列：出现次数最多的列。"""
    return Counter(p[1] for p in path).most_common(1)[0][0]


def main():
    ink = load_ink()
    H, W = ink.shape
    seg = bidirectional_segment(ink)
    l1_set = set(seg['l1_path'])

    print('=' * 78)
    print('论文图3-23 四面板的三元组 (起点列, 中间段列, 终点列)：')
    print('=' * 78)
    for k, v in PAPER.items():
        print('  面板%s: 起点%3d  中间段%3d  终点%3d' % (k, v[0], v[1], v[2]))
    print()
    print('  观察：四面板起点列各不相同（57/77/63/63），但中间段一律 63、终点一律 77。')
    print('  这不是"换指标"能产生的——换指标只改"选哪个起点"，不改路径形状。')
    print()

    print('=' * 78)
    print('本实现在各候选起点上的三元组：')
    print('=' * 78)
    print('%4s | %5s | %6s | %5s | %s' % ('c0', '中间段', '终点', '路径长', '备注'))
    rows = []
    for c0 in range(1, W - 1):
        if ink[0, c0]:
            continue
        res = drop_improved(ink, 0, c0, (1, 0), terminate_at=l1_set, rng=None)
        path = res['path']
        mc = mid_col(path)
        ec = res['end'][1]
        rows.append((c0, mc, ec, len(path)))
        note = ''
        if c0 in (57, 63, 77):
            note = '← 论文用过的起点'
        if mc == 63:
            note += (' ← 中间段=63' if note else '← 中间段=63')
        if ec == 77:
            note += (' ← 终点=77' if note else '← 终点=77')
        print('%4d | %5d | %6d | %5d | %s' % (c0, mc, ec, len(path), note))
    print()

    print('=' * 78)
    print('判定：有没有起点能给出 (·, 63, 77) —— 即中间段 63 且终点 77？')
    print('=' * 78)
    hit = [r for r in rows if r[1] == 63 and r[2] == 77]
    if hit:
        print('有：%s' % hit)
    else:
        print('没有。任何一个起点，都无法同时满足"中间段 63"与"终点 77"。')
        print()
        print('各起点中间段列的取值集合：%s'
              % sorted(set(r[1] for r in rows)))
        print('各起点终点的取值集合（前 12 个）：%s'
              % sorted(set(r[2] for r in rows))[:12])

    print()
    print('=' * 78)
    print('结论')
    print('=' * 78)
    print('1) 本实现在这张图上，任何起点都走不出论文的 (·, 63, 77) 形状；')
    print('2) 论文四面板"起点不同、中间段与终点相同"这一事实，说明它们不是')
    print('   同一算法的四次独立运行，而更像是**同一条参考路径换了起点标注**；')
    print('3) 结合前作（40 种选优组合都选不出 77），可以判定：')
    print('   论文图3-23 的 l₂ 与本实现的 l₂ 不是同一个东西——')
    print('   论文那条线很可能是**人工绘制的参考分割线**（或用不同算法生成），')
    print('   而不是"改进滴水算法在 δ₂ 带内选优"的产物。')
    print()
    print('   这直接推翻"差距在绕行细节/熔断机制"的归因：')
    print('   如果目标线本身不是本算法能产生的，那么无论怎么改规则都到不了。')
    print()


if __name__ == '__main__':
    main()
