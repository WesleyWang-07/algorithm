# -*- coding: utf-8 -*-
"""
邻点集消融实验：论文 §3.2.1（5 邻点） / 论文 §3.2.2（6 邻点） / 专利 2024（7 邻点）

要回答的问题
------------
汇报稿里说"指标 B 在谱字A上退化了"。用户问：**这是不是两代算法的规则差异造成的？**

做法
----
三套邻点集共用**完全相同**的决策逻辑与终止条件，只有一个变量不同：参与竞争的邻点集合。
  · 决策：贪心取 max g_j（g_j = 8-j），k=0 ⇒ o_j ≡ 1（即关闭遇阻随机取向）
  · 终止：触到 l1 所在行 r>=L1_ROW / 出界 / 重复访问
这样任何输出差异都只能归因于邻点集，不能归因于状态机或编码细节。

若三套规则下的终点列都"不随起点变"，则 B = |终点列 - 起点列| 在三套规则下**都是**
起点的单调函数 ⇒ B 退化与"哪一代算法"无关。

只读，不修改任何算法代码。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from PIL import Image

from improved_droplet import _G7, _neighbors, is_open

GLYPHS = os.path.join(os.path.dirname(__file__), '..', '..', '文献', 'glyphs')
L1_ROW = 92          # l1 在谱字A上的行（验证报告：轨迹 rows 92–93）

NSETS = {
    'P5 论文3.2.1': range(1, 6),
    'P6 论文3.2.2': range(1, 7),
    'P7 专利2024': range(1, 8),
}
KEYS = list(NSETS)


def load_ink(path, thresh=128):
    a = np.array(Image.open(path).convert('RGB')).astype(int)
    return (a[..., 0] < thresh) & (a[..., 1] < thresh) & (a[..., 2] < thresh)


def walk(ink, r0, c0, g, jset, stop_row=L1_ROW, max_step=500):
    """贪心滴水，返回轨迹。终止：r>=stop_row / 出界 / 重复访问 / 步数上限。"""
    H, W = ink.shape
    nb = _neighbors(g)
    r, c = r0, c0
    traj = [(r, c)]
    seen = {(r, c)}
    for _ in range(max_step):
        best_j, best_q = None, None
        for j in jset:
            dr, dc = nb[j]
            if not is_open(ink, r + dr, c + dc):
                continue
            q = _G7[j]
            if best_q is None or q > best_q:
                best_q, best_j = q, j
        if best_j is None:
            nr, nc = r + g[0], c + g[1]        # 全黑 → 熔断前穿 1px
        else:
            dr, dc = nb[best_j]
            nr, nc = r + dr, c + dc
        r, c = nr, nc
        traj.append((r, c))
        if not (0 <= r < H and 0 <= c < W):
            break
        if r >= stop_row:
            break
        if (r, c) in seen:
            break
        seen.add((r, c))
    return traj


def main():
    ink = load_ink(os.path.join(GLYPHS, 'p49_img4.png'))
    H, W = ink.shape
    g = (1, 0)
    print('谱字A / p49_img4.png  %dx%d   l2: g=(1,0)' % (W, H))
    print('终止条件：r>=%d (l1) / 出界 / 重复访问 ; k=0' % L1_ROW)

    c0s = [c for c in range(42, 89) if is_open(ink, 0, c)]
    print('δ2 带 (42, 88) 内顶行可用的起点列：%d 个\n' % len(c0s))

    # ---- 表一：汇报稿用的 c0=71..84 ----
    print('=' * 92)
    print('[表一] c0 = 71..84：三套邻点集的 (终点列, 指标B)')
    print('  %-5s' % 'c0' + ''.join('%24s' % k for k in KEYS))
    for c0 in range(71, 85):
        line = '  %-5d' % c0
        for k in KEYS:
            e = walk(ink, 0, c0, g, NSETS[k])[-1][1]
            line += '%24s' % ('(%d, %d)' % (e, abs(e - c0)))
        print(line)

    # ---- 表二：全带单调性判定 ----
    print('\n' + '=' * 92)
    print('[表二] δ2 带全段：终点列取值集合 与 B 的单调性')
    print('  %-14s %-26s %-10s %-14s' % ('邻点集', '终点列取值集合', 'B严格递减', 'B 范围'))
    for k in KEYS:
        ends, Bs = [], []
        for c0 in c0s:
            e = walk(ink, 0, c0, g, NSETS[k])[-1][1]
            ends.append(e)
            Bs.append(abs(e - c0))
        uniq = sorted(set(ends))
        mono = all(Bs[i] > Bs[i + 1] for i in range(len(Bs) - 1))
        print('  %-14s %-26s %-10s %d..%d'
              % (k, str(uniq)[:26], str(mono), min(Bs), max(Bs)))

    # ---- 表三：6 邻点 vs 7 邻点逐格比对 ----
    print('\n' + '=' * 92)
    print('[表三] 逐格轨迹比对：论文飞溅版(6) vs 专利(7)')
    print('  %-5s %-16s %-16s %-12s %s' % ('c0', 'P6终点', 'P7终点', '轨迹首异步', '结论'))
    same = 0
    for c0 in c0s:
        a = walk(ink, 0, c0, g, NSETS['P6 论文3.2.2'])
        b = walk(ink, 0, c0, g, NSETS['P7 专利2024'])
        n = min(len(a), len(b))
        diff = [i for i in range(n) if a[i] != b[i]]
        ident = (a == b)
        same += ident
        if c0 in (42, 46, 50, 63, 71, 77, 84, 88) or not ident:
            print('  %-5d %-16s %-16s %-12s %s'
                  % (c0, str(a[-1]), str(b[-1]),
                     ('-' if ident else str(diff[0])),
                     ('逐格完全一致' if ident else '有差异')))
    print('  → 带内 %d/%d 个起点上，6 邻点与 7 邻点**逐格完全一致**' % (same, len(c0s)))

    # ---- 表四：与 5 邻点的比对 ----
    print('\n' + '=' * 92)
    print('[表四] 5 邻点 vs 7 邻点：终点列是否不同')
    bad = 0
    for c0 in c0s:
        e5 = walk(ink, 0, c0, g, NSETS['P5 论文3.2.1'])[-1][1]
        e7 = walk(ink, 0, c0, g, NSETS['P7 专利2024'])[-1][1]
        if e5 != e7:
            bad += 1
            if bad <= 6:
                print('   c0=%-4d  P5终点=%d   P7终点=%d' % (c0, e5, e7))
    print('  → 带内 %d/%d 个起点上，两者的终点列不同' % (bad, len(c0s)))

    # ---- 表五：真实实现（含状态机 + terminate_at）复核 ----
    print('\n' + '=' * 92)
    print('[表五] 真实实现复核：drop_improved(..., terminate_at=l1) 在 δ2 带内逐列')
    from improved_droplet import drop_improved
    from segment import bidirectional_segment

    seg = bidirectional_segment(ink)
    l1_set = set(seg['l1_path'])
    print('  l1 起点 %s  锚点(l2 选中) %s' % (seg['start1'], seg['intersect']))

    real = []
    for c0 in c0s:
        res = drop_improved(ink, 0, c0, g, terminate_at=l1_set)
        yi = res['path'][-1][1] if res['stopped_by'] == 'terminate_at' else res['end'][1]
        real.append((c0, yi, abs(yi - c0)))
    pick = min(real, key=lambda t: t[2])
    print('  B 在带内的最小值 → c0=%d, 终点列=%d, B=%d' % pick)
    ends = sorted(set(t[1] for t in real))
    print('  终点列取值集合 = %s' % ends)
    for label, lo, hi in (('左簇 42..49', 42, 49), ('右簇 50..88', 50, 88)):
        sub = [t for t in real if lo <= t[0] <= hi]
        if not sub:
            continue
        e = sorted(set(t[1] for t in sub))
        mono = all(sub[i][2] > sub[i + 1][2] for i in range(len(sub) - 1))
        print('  %-12s 终点列=%s  B 严格递减=%s  B=%d..%d'
              % (label, e, mono, sub[0][2], sub[-1][2]))

    print('\nDONE')


if __name__ == '__main__':
    main()
