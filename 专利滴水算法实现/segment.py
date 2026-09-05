# -*- coding: utf-8 -*-
"""
双向切分 + 四种优化指标（专利权利要求 5、论文 3.3 节）
======================================================

把完整泛音谱字切成三张子图：左上、右上、下部。

流程
----
1) 第一次切分 l1（红色，横向）：重力方向 g=(0,1)，水滴从图像左缘中部滴落、向右滑动，
   得到"上下切分路径"，把上部(左上+右上)与下部切开。
2) 第二次切分 l2（绿色，纵向）：重力方向 g=(1,0)，水滴从上部区域上缘中部滴落、向下滑动，
   得到"左右切分路径"，把左上与右上切开；碰到 l1 时终止（两路径交点即分割锚点）。
3) 依据两条路径的最大/最小坐标（交点），直接裁剪出 左上 / 右上 / 下部 三张子图。

初始滴点优化（权利要求5 的 A/B/C/D 四种指标）：
    A: 熔断量最小   d
    B: 始末偏移最小 |x* - x°|
    C: 累计偏移最小 v
    D: 融合指标最小 d + |x* - x°| + v     （论文结论 D 最优，默认使用）
"""

import numpy as np
from improved_droplet import drop_improved, is_open, path_metrics


def build_synthetic_character(H=160, W=220, connect_top=True):
    """
    构造一个"仿古琴泛音谱字"的二值图：左上部件 + 右上部件 + 下部部件。
    connect_top=True 让左上/右上之间有一条细"笔画粘连"竖线（考验 l2 的落水滴/熔断能力）。
    返回 ink：HxW 布尔阵，True=黑色墨迹。
    """
    ink = np.zeros((H, W), dtype=bool)

    def blob(r0, r1, c0, c1):
        ink[r0:r1, c0:c1] = True

    # 左上部件：左上象限一个方形墨块
    blob(20, 58, 22, 90)
    # 右上部件：右上象限一个方形墨块
    blob(20, 58, 132, 198)
    # 下部部件：下方一个较大的墨块
    blob(92, 138, 28, 192)

    if connect_top:
        # 左上与右上之间的"粘连"竖线（中部）
        ink[24:58, 108:114] = True

    return ink


def bidirectional_segment(ink, metric='D', seed=20241016):
    """
    对二值谱字图像做双向切分。
    返回 dict：
        l1_path, l2_path   : 两条水滴轨迹
        intersect          : 交点 (xi, yi)
        crops              : {'left_top','right_top','bottom'} 三张子图(ink 阵列)
        metrics1, metrics2 : 选中初始滴点的四指标

    seed：传给水滴的 S102 遇阻随机取向随机源；固定默认值保证结果可复现。
    """
    if metric not in ('A', 'B', 'C', 'D'):
        raise ValueError(f"metric 必须是 'A'/'B'/'C'/'D' 之一，收到 {metric!r}")
    rng = np.random.default_rng(seed)
    H, W = ink.shape

    # ---- 第一次切分 l1：横向（上下切分），起点左缘、行在中间带 ----
    # 论文: 上下切分初始滴点 δ1 ∈ (2/5 N, 3/5 N), N=高度(行数)
    n1 = int(round(0.4 * H)); n2 = int(round(0.6 * H))
    r_span = list(range(max(1, n1), min(H - 1, n2)))
    # 固定 c0=0（左缘），枚举 r0
    g1 = (0, 1)
    best1 = None
    for r0 in r_span:
        if not is_open(ink, r0, 0):
            continue
        res = drop_improved(ink, r0, 0, g1, rng=rng)
        m = path_metrics(res, g1)
        score = m[metric]
        if best1 is None or score < best1[0]:
            best1 = (score, r0, res, m)
    if best1 is None:
        # 中间带入口全被墨迹挡住（黑边框/污渍）：回退带中点强制起步
        r0_best = (r_span[0] + r_span[-1]) // 2 if r_span else H // 2
        res1 = drop_improved(ink, r0_best, 0, g1, rng=rng)
        m1 = path_metrics(res1, g1)
    else:
        _, r0_best, res1, m1 = best1
    l1_path = res1['path']

    # l1 的格点集，用于 l2 终止
    l1_set = set(l1_path)

    # ---- 第二次切分 l2：纵向（左右切分），起点上缘、列在中间带 ----
    # 论文: 左右切分初始滴点 δ2 ∈ (2/7 M, 3/5 M), M=宽度(列数，上方区域)
    w1 = int(round(2 / 7 * W)); w2 = int(round(3 / 5 * W))
    c_span = list(range(max(1, w1), min(W - 1, w2)))
    g2 = (1, 0)
    best2 = None
    for c0 in c_span:
        if not is_open(ink, 0, c0):
            continue
        res = drop_improved(ink, 0, c0, g2, terminate_at=l1_set, rng=rng)
        m = path_metrics(res, g2)
        if best2 is None or m[metric] < best2[0]:
            best2 = (m[metric], c0, res, m)
    if best2 is None:
        # 同 l1：上缘入口全被挡住时回退带中点
        c0_best = (c_span[0] + c_span[-1]) // 2 if c_span else W // 2
        res2 = drop_improved(ink, 0, c0_best, g2, terminate_at=l1_set, rng=rng)
        m2 = path_metrics(res2, g2)
    else:
        _, c0_best, res2, m2 = best2
    l2_path = res2['path']
    if res2['stopped_by'] == 'terminate_at':
        xi, yi = l2_path[-1]
    else:
        # 没碰到 l1：用 l2 落到底部的那一点
        xi, yi = res2['end']

    # ---- 依据交点裁剪三张子图 ----
    xi = min(max(xi, 0), H - 1)
    yi = min(max(yi, 0), W - 1)
    crops = {
        'left_top':  ink[0:xi, 0:yi],
        'right_top': ink[0:xi, yi:W],
        'bottom':    ink[xi:H, 0:W],
    }

    return {
        'l1_path': l1_path,
        'l2_path': l2_path,
        'intersect': (xi, yi),
        'crops': crops,
        'metrics1': m1,
        'metrics2': m2,
        'start1': (r0_best, 0),
        'start2': (0, c0_best),
    }
