# -*- coding: utf-8 -*-
"""
diag_l2_selection.py —— 判定"论文 l2 起点列 77 是如何被选中的"

背景（2026-09-17）：验证报告 4.6 节把"走不到真值 0.524"归因于「遇单侧开放时
是否熔断穿越」。但实测发现另一个更硬的事实——即便实现了穿越，只要论文是在
δ₂ 带内"枚举 + 按指标选优"，77 也赢不过 42~46 那一簇。故本脚本判定：
    「枚举 + 指标」这个框架本身，能否产生 77？

判据：对每一种 (δ₂ 带定义 × 指标 × tie-break) 组合，算出被选中的列。
只有当某个组合能选中 77，才说明论文机制与本实现同构、只是参数不同。

纯只读诊断，不修改任何算法代码。

运行：python diag_l2_selection.py
"""
import os
import sys

import numpy as np
from PIL import Image

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))

from improved_droplet import drop_improved, path_metrics  # noqa: E402
from segment import bidirectional_segment  # noqa: E402

GLYPHS = os.path.join(_HERE, '..', '..', '文献', 'glyphs')
OUT = os.path.join(_HERE, 'out')

# 论文图3-23 四面板的 l2 起点列（来自 diag_truth_measure.py 的实测）
TRUTH_STARTS = {'A': 57, 'B': 77, 'C': 63, 'D': 63}
TRUTH_END = 77          # 四面板 l₂ 终点列
WHITE = 1


def load_ink():
    p = os.path.join(GLYPHS, 'p49_img4.png')
    # ⚠️ 输入口径（2026-09-18 修正）：p49_img4.png 内**烤着论文自己的红线标注**
    #    （247 个纯红像素，rows 94–184）。convert('L') 会把红线判成墨迹
    #    （纯红 (255,0,0) 的 L=76<128），使 l1 贴着论文的红线走。
    #    必须按 RGB 逐通道判定 —— 与 run_real.py / segment.py 的口径一致。
    a = np.array(Image.open(p).convert('RGB')).astype(int)
    return (a[..., 0] < 128) & (a[..., 1] < 128) & (a[..., 2] < 128)


def run_l2(ink, l1_set, c0):
    """从 (0, c0) 向下滴，接 l1 终止条件，返回 (终点, 指标)。"""
    res = drop_improved(ink, 0, c0, (1, 0), terminate_at=l1_set, rng=None)
    m = path_metrics(res, (1, 0))
    return res['end'], m


def band_defs(W, H):
    """各种可能的 δ₂ 带定义（论文写 (2/7·M, 3/5·M)，M 的口径有多种解释）。"""
    return {
        'as-implemented (2W/7, 3W/5)': (int(round(2 / 7 * W)), int(round(3 / 5 * W))),
        'over W-1': (int(round(2 / 7 * (W - 1))), int(round(3 / 5 * (W - 1)))),
        'as-fraction (0.286..0.6)·W': (int(round(0.286 * W)), int(round(0.6 * W))),
        'wide (0.25..0.75)·W': (int(round(0.25 * W)), int(round(0.75 * W))),
        'full width': (1, W - 2),
    }


def main():
    ink = load_ink()
    H, W = ink.shape
    print('图像 %dx%d，墨迹 %d px' % (H, W, int(ink.sum())))
    print('论文真值：四面板 l2 起点列 A=%d B=%d C=%d D=%d；终点列一律 %d'
          % (TRUTH_STARTS['A'], TRUTH_STARTS['B'],
             TRUTH_STARTS['C'], TRUTH_STARTS['D'], TRUTH_END))
    print()

    # l1 用当前配置（D 指标）跑一遍，拿到 terminate_at 的格点集
    seg = bidirectional_segment(ink)
    l1_set = set(seg['l1_path'])
    r1_start, _ = seg['start1']
    print('l1 起点 r0=%d，路径 %d 格；l1 落在 rows %d..%d'
          % (r1_start, len(seg['l1_path']),
             min(p[0] for p in l1_set), max(p[0] for p in l1_set)))
    print()

    # ---------- 第 1 步：逐列算指标 + 终点（全宽扫描，不受带限制）----------
    print('=' * 78)
    print('第 1 步：全宽逐列指标表（含 l1 终止条件）')
    print('=' * 78)
    print('%4s | %4s | %-14s | %3s %3s %3s %3s | %s'
          % ('c0', 'end', 'end x_rel', 'A', 'B', 'C', 'D', '备注'))
    table = {}
    for c0 in range(1, W - 1):
        if ink[0, c0]:
            continue
        end, m = run_l2(ink, l1_set, c0)
        table[c0] = (end, m)
        note = ''
        if c0 == TRUTH_STARTS['B']:
            note = '← 论文面板B起点'
        if end[1] == TRUTH_END:
            note += (' ← 终点=真值77' if note else '← 终点=真值77')
        if c0 in (42, 46):
            note += (' ← 当前被选中' if note else '← 当前被选中')
        print('%4d | %4d | %-14.4f | %3d %3d %3d %3d | %s'
              % (c0, end[1], end[1] / W, m['A'], m['B'], m['C'], m['D'], note))
    print()

    # ---------- 第 2 步：终结列分布 ----------
    print('=' * 78)
    print('第 2 步：终结列分布（同一终点列 → 哪些起点）')
    print('=' * 78)
    by_end = {}
    for c0, (end, m) in table.items():
        by_end.setdefault(end[1], []).append(c0)
    for ecol in sorted(by_end):
        starts = by_end[ecol]
        print('终点 col %4d (x_rel %.4f, %2d 个起点): %s'
              % (ecol, ecol / W, len(starts),
                 str(starts) if len(starts) <= 14 else
                 '%s ... %s' % (starts[:6], starts[-3:])))
    print()
    print('>>> 关键：起点 42~49 与 50~88 是两条完全分离的吸引子。')
    print('    42~49 → 终点 col 27；50~88 → 终点 col 111。')
    print('    起点 77 属于后者，终点 col 111（不是真值 77）。')
    print()

    # ---------- 第 3 步：各种 δ₂ 带 × 指标 × tie-break，看选中谁 ----------
    print('=' * 78)
    print('第 3 步：δ₂ 带 × 指标 × tie-break 组合 → 被选中的列')
    print('=' * 78)
    hits = []
    for bname, (lo, hi) in band_defs(W, H).items():
        for mt in ('A', 'B', 'C', 'D'):
            for tb, tbname in ((lambda a, b: a < b, 'strict'),
                               (lambda a, b: a <= b, 'lax')):
                best = None
                for c0 in range(max(1, lo), min(W - 1, hi + 1)):
                    if c0 not in table:
                        continue
                    _, m = table[c0]
                    if best is None or tb(m[mt], best[0]):
                        best = (m[mt], c0)
                if best is None:
                    continue
                mark = ''
                if best[1] == TRUTH_STARTS['B']:
                    mark = '  ★★★ 命中真值起点 77！'
                    hits.append((bname, mt, tbname))
                print('%-28s | %s | %-6s | -> c0=%-4d (score=%d)%s'
                      % (bname, mt, tbname, best[1], best[0], mark))
        print()

    # ---------- 第 4 步：结论 ----------
    print('=' * 78)
    print('第 4 步：结论')
    print('=' * 78)
    if hits:
        print('存在能命中 77 的组合：')
        for h in hits:
            print('  - δ₂带=%s，指标=%s，tie-break=%s' % h)
        print()
        print('=> 「枚举 + 指标」框架**可能成立**，只是参数与本实现不同。')
    else:
        print('在全部 %d 种组合下，**没有任何一种能选中 77**。'
              % (len(band_defs(W, H)) * 4 * 2))
        print()
        print('=> 「枚举 δ₂ 带 + 按 A/B/C/D 选优」这个框架**本身就无法产生 77**。')
        print('   理由（结构性，与参数无关）：')
        print('     · 起点的终点是被几何决定的（42~49→col27，50~88→col111），')
        print('       带内所有起点只落在两个吸引子上，而 77 不属于任何一个；')
        print('     · 起点 77 的终点是 col111，横向偏移 %d 格；' % (TRUTH_END and 111 - 77))
        print('       而 42/46 的终点 col27 偏移更小（B 更优）、熔断也更少（A 更优）；')
        print('     · 因此 77 在任何"越小越好"的指标下都排不进第一。')
        print()
        print('   => 论文的选优机制与本实现**不同构**，不是"同一个框架换个指标"。')
        print('      这也解释了为什么文档里一直记着"起点列 57/77/63 与枚举结果不一致"——')
        print('      那不是"风险"，而是该框架被证伪的反证。')
    print()


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    main()
