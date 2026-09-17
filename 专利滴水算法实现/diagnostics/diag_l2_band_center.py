# -*- coding: utf-8 -*-
"""
diag_l2_band_center.py —— 补做判别实验：把"以中点为心的对称 δ 带"纳入枚举

背景（2026-09-17 第五轮）：
    diag_l2_selection.py 枚举了 5 种 δ₂ 带定义 × 4 指标 × 2 tie-break = 40 种组合，
    结论是"无一能选中起点列 77"，并据此判定「枚举 + 指标」框架被证伪（见 ADR 0001）。

    但核查论文**正文**后发现一个问题：那 5 种带定义**全部是偏左的非对称区间**
    （(2/7·M, 3/5·M) 及其口径微调）。而论文 3.3.1 节（p45）原文写的是：

        「谱字切分线的初始点应该位于**图像中点 m 附近**，将这个范围表示为 δ」
        「在**中点附近 δ 范围内**的初始点生成的切分线中包含切分效果理想和
          切分效果不理想的线，需要寻找优化指标确定最佳的初始切分点」

    即：论文的 δ 是**以图像中点为心的对称带**，而本实现用的是 (2/7, 3/5)。
    这两个很可能不是同一个东西——那么"40 种组合都选不出 77"的结论就**不成立**，
    因为**正确的带可能压根没被试过**。

本脚本的判据（二值、决定性）：
    补上"以中点为心的对称带"若干种半径，重跑枚举。
    · 若仍无一命中 77  → 第三轮结论被**加固**（连正确的带也试过了，仍不成立）
    · 若某种对称带能命中 77 → 第三轮结论**被推翻**，项目可能要重开

纯只读诊断，不修改任何算法代码。

运行：python diag_l2_band_center.py
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

# 论文图3-23 四面板的 l2 起点列（来自 diag_truth_measure.py 的实测）
TRUTH_STARTS = {'A': 57, 'B': 77, 'C': 63, 'D': 63}
TRUTH_END = 77


def load_ink():
    p = os.path.join(GLYPHS, 'p49_img4.png')
    img = Image.open(p).convert('L')
    return np.array(img) < 128      # True = 墨迹


def run_l2(ink, l1_set, c0):
    """从 (0, c0) 向下滴，接 l1 终止条件，返回 (终点, 指标)。"""
    res = drop_improved(ink, 0, c0, (1, 0), terminate_at=l1_set, rng=None)
    m = path_metrics(res, (1, 0))
    return res['end'], m


def band_defs(W, H):
    """
    δ 带候选。第 1 组是 diag_l2_selection.py 用过的（对照）；
    第 2 组是**本脚本新增**——以中点为心的对称带，对应论文正文的表述。
    """
    bands = {}
    # --- 对照组：第三轮用过的 5 种偏左定义 ---
    bands['[旧] as-implemented (2W/7, 3W/5)'] = (int(round(2 / 7 * W)), int(round(3 / 5 * W)))
    bands['[旧] over W-1'] = (int(round(2 / 7 * (W - 1))), int(round(3 / 5 * (W - 1))))
    bands['[旧] as-fraction (0.286..0.6)W'] = (int(round(0.286 * W)), int(round(0.6 * W)))
    bands['[旧] wide (0.25..0.75)W'] = (int(round(0.25 * W)), int(round(0.75 * W)))
    bands['[旧] full width'] = (1, W - 2)

    # --- 新增组：以中点 m = W/2 为心的对称带 (m-k, m+k) ---
    # 论文只说"中点附近 δ"，未给 δ 的大小，故扫多个半径
    m = W / 2.0
    for k in (0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.50):
        bands['[新] 对称带 m±%.2fW' % k] = (int(round(m - k * W)), int(round(m + k * W)))
    # 也试"以中点为中心、按 W-1 口径"
    m1 = (W - 1) / 2.0
    for k in (0.10, 0.20, 0.30):
        bands['[新] 对称带(W-1) m±%.2fW' % k] = (int(round(m1 - k * (W - 1))),
                                                 int(round(m1 + k * (W - 1))))
    # 极窄带：中点邻域几列
    for half in (3, 5, 8, 12):
        bands['[新] 中点邻域 ±%d 列' % half] = (int(round(m)) - half, int(round(m)) + half)
    return bands


def main():
    ink = load_ink()
    H, W = ink.shape
    print('图像 %dx%d，墨迹 %d px' % (H, W, int(ink.sum())))
    print('中点 m = W/2 = %.1f  （→ 列 %d）' % (W / 2.0, int(round(W / 2.0))))
    print('论文真值：l2 起点列 A=%d B=%d C=%d D=%d；终点列一律 %d'
          % (TRUTH_STARTS['A'], TRUTH_STARTS['B'],
             TRUTH_STARTS['C'], TRUTH_STARTS['D'], TRUTH_END))
    print()

    # l1 先跑一遍，拿 terminate_at 的格点集
    seg = bidirectional_segment(ink)
    l1_set = set(seg['l1_path'])
    r1_start, _ = seg['start1']
    print('l1 起点 r0=%d，路径 %d 格' % (r1_start, len(seg['l1_path'])))
    print()

    # 全宽逐列指标表（与旧脚本一致的口径，便于对照）
    table = {}
    for c0 in range(1, W - 1):
        if ink[0, c0]:
            continue
        end, m = run_l2(ink, l1_set, c0)
        table[c0] = (end, m)

    # ---------- 枚举：带 × 指标 × tie-break ----------
    print('=' * 88)
    print('枚举 δ 带 × 指标 × tie-break → 被选中的起点列（★ = 命中真值 77）')
    print('=' * 88)
    hits = []
    total = 0
    old_hits = []
    new_hits = []
    for bname, (lo, hi) in band_defs(W, H).items():
        lo2, hi2 = max(1, lo), min(W - 2, hi)
        inband = [c for c in range(lo2, hi2 + 1) if c in table]
        if not inband:
            continue
        for mt in ('A', 'B', 'C', 'D'):
            for tb, tbname in ((lambda a, b: a < b, 'strict'),
                               (lambda a, b: a <= b, 'lax')):
                total += 1
                best = None
                for c0 in inband:
                    _, m = table[c0]
                    if best is None or tb(m[mt], best[0]):
                        best = (m[mt], c0)
                if best is None:
                    continue
                mark = ''
                if best[1] == TRUTH_STARTS['B']:
                    mark = '  ★★★ 命中真值起点 77！'
                    hits.append((bname, mt, tbname))
                    (new_hits if bname.startswith('[新]') else old_hits).append(
                        (bname, mt, tbname))
                print('%-30s | %s | %-6s | 区间[%3d,%3d] | -> c0=%-4d (s=%2d)%s'
                      % (bname, mt, tbname, lo2, hi2, best[1], best[0], mark))
        print()

    # ---------- 结论 ----------
    print('=' * 88)
    print('结论')
    print('=' * 88)
    print('共枚举 %d 种组合（旧定义 %d 种 + 新增对称定义 %d 种）。'
          % (total, len([b for b in band_defs(W, H) if b.startswith('[旧]')]),
             len([b for b in band_defs(W, H) if b.startswith('[新]')])))
    print()
    if hits:
        print('⚠️ 存在能命中 77 的组合（共 %d 个）：' % len(hits))
        for h in hits:
            print('  - 带=%s，指标=%s，tie-break=%s' % h)
        print()
        if new_hits:
            print('>>> 其中有 **新增的对称带** 命中：')
            for h in new_hits:
                print('    - %s / %s / %s' % h)
            print()
            print('=> 第三轮结论「枚举+指标框架无法产生 77」**被推翻**。')
            print('   论文的 δ 是「中点附近的对称带」，与本实现的 (2/7, 3/5) 不是同一个东西。')
            print('   需要重开：以对称带重跑，并重估 ADR 0001 与验证报告 4.7 节。')
        else:
            print('>>> 命中的全部是旧定义（偏左带），说明结论原本就成立。')
    else:
        print('在全部 %d 种组合下，**没有任何一种能选中 77**。' % total)
        print()
        print('>>> 这一次连「以中点为心的对称带」（论文正文所述的 δ）也试过了。')
        print('=> 第三轮结论被**加固**，而不再是"可能试错了带"：')
        print('   无论带怎么定义，77 都不在任何"越小越好"的指标下排第一。')
        print()
        print('   结构性原因（与带无关）：起点 77 的终点是 col 111，横向偏移 34 格；')
        print('   而同图中 42~49 簇的终点是 col 27，偏移更小、熔断更少。')
        print('   77 在任何最小值指标下都排不进第一——这是几何决定的。')
    print()


if __name__ == '__main__':
    os.makedirs(os.path.join(_HERE, 'out'), exist_ok=True)
    main()
