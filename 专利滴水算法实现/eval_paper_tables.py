# -*- coding: utf-8 -*-
"""
论文表3-3 / 表3-4 真值对照（**只读**：读 `文献/glyphs/table33_34/`，不写任何文件）
=============================================================================
这是本项目唯一一处"拿论文的图当参照"的评测，用来回答"我实际能做到什么"。
在此之前，所有结论都只能定性说"跑得通"——因为没有分母。

数据来源
--------
`文献/glyphs/table33_34/{tab33|tab34}_rNN_glyph.png`  +  同行的 `_A/_B/_C/_D.png`
（由 `diagnostics/diag_extract_tables.py` 从 `文献/HUNNUThesis.pdf` 抽取）

- `_glyph` 格 = 论文表格第 1 列，**干净字形**，已断言无彩色像素 → 可作算法输入
- `_A/_B/_C/_D` 格 = 论文用四个优化指标各跑一遍的结果图 → **只用来读线**

⚠️ 红线一：`_A~_D` 格不能当输入
    论文的绿线画在墨迹之上，覆盖 16% 的压墨像素、在列方向把墨挖出缺口。
    实测：同一张谱字A，干净图 → 锚点 col 46；带绿线的图 → col 76。
    所以本脚本只用 glyph 格跑算法、只用结果格读线。

⚠️ 红线二：读图口径必须用 `run_real.load_ink`（RGB 逐通道 <128）
    `convert('L') < 128` 会把图内红线（灰度约 76）当成墨迹。

本脚本给出四个量（不要只看其中一个）
------------------------------------
[0] 栅格一致性检验
    论文的结果格与字形格是不是同一块画布？判据：把结果格的红/绿像素剔掉后，
    剩下的墨迹与字形格**逐像素**比。放宽到 8 邻域膨胀 1px 仍有大量差异 ⇒ 不同画布。
    **不同画布 ⇒ 坐标不可比 ⇒ 该行必须从 [2][3] 中剔除。**
    （这是一个客观的排版事实，不是本实现的评价。）

[1] 参考线读法：把结果格里的红线/绿线读成"逐列行号/逐行列号"两条折线。

[2] 一致率（仅对「同格」的行）
    l₁：逐列比行号；l₂：逐行比列号。中位差 ≤ TOL 记为一致。

[3] 穿墨量对照（**同一把尺子**）
    把论文的线与本实现的轨迹分别叠在**干净字形**上，数各自压在墨迹上的像素。
    必须先**统一线宽**：论文画的红/绿线是 3px 粗、本实现的轨迹是 1px，
    不统一就等于让本实现白占便宜。故本脚本把两边都按 3px 统计。

[4] l₂ 选优指标 B vs D
    本实现默认 `metric2='B'`（依据论文表3-1 对谱字B 的两字轶事）。
    而论文 §3.4.5 的集级统计（表3-5/3-6）明确写「优化指标 B 在四个优化指标中
    表现最差」，论文最终选 **D**。此处按 [3] 的同一把尺子实测两者的差别。

运行：cd 专利滴水算法实现 && python eval_paper_tables.py
"""
import os
import sys

import numpy as np
from PIL import Image
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from run_real import load_ink                      # noqa: E402 统一 RGB 读图口径
from segment import bidirectional_segment           # noqa: E402

GLYPH_DIR = os.path.join(HERE, '..', '文献', 'glyphs', 'table33_34')
TOL = 3          # 行/列差 ≤ 3px 记为"一致"（抽图 300dpi 下约 1.5 格）
GRID_TOL = 5     # 判定"同画布"时允许的残余墨像素数
LINE_W = 3       # 论文线宽
METRICS = ('A', 'B', 'C', 'D')

# 论文正文声明的"该字哪几个指标切分正确"（§3.4.3 p55 / §3.4.4 p56 原文）
PAPER_OK = {
    ('tab33', 1): 'ABCD', ('tab33', 2): 'ABCD', ('tab33', 3): 'ABCD',
    ('tab33', 4): 'ABCD', ('tab33', 5): 'ABCD', ('tab33', 6): 'ABCD',
    ('tab33', 7): 'ABCD', ('tab33', 8): 'ABCD', ('tab33', 9): 'ABCD',
    ('tab33', 10): 'AD',                          # B/C 过度追求小偏移 → 熔断
    ('tab34', 1): 'BCD', ('tab34', 2): 'ACD', ('tab34', 3): 'BCD',
    ('tab34', 4): 'ABCD', ('tab34', 5): 'AD',
}
ROWS = [('tab33', i) for i in range(1, 11)] + [('tab34', i) for i in range(1, 6)]


def load_png(path):
    return np.array(Image.open(path).convert('RGB')).astype(int)


def mask_red(a):
    return (a[..., 0] > 150) & (a[..., 1] < 110) & (a[..., 2] < 110)


def mask_green(a):
    return (a[..., 1] > 130) & (a[..., 0] < 120) & (a[..., 2] < 120)


def paths_from_panel(panel):
    """读结果格：返回 (l1 逐列行号 dict, l2 逐行列号 dict)。"""
    red, grn = mask_red(panel), mask_green(panel)
    l1 = {}
    for c in range(red.shape[1]):
        rr = np.where(red[:, c])[0]
        if len(rr):
            l1[c] = int(round(rr.mean()))
    l2 = {}
    for r in range(grn.shape[0]):
        cc = np.where(grn[r, :])[0]
        if len(cc):
            l2[r] = int(round(cc.mean()))
    return l1, l2


def same_canvas(ink, panel):
    """结果格剔掉线像素后，与字形格是否同一栅格？

    两图尺寸可能不等（结果格宽度恒为 183，字形格 182；高度也可能差几像素），
    故先按左上对齐裁到公共尺寸再比 —— 尺寸差本身由调用方单独打印。
    """
    H = min(ink.shape[0], panel.shape[0])
    W = min(ink.shape[1], panel.shape[1])
    ink2 = ink[:H, :W]
    lines = (mask_red(panel) | mask_green(panel))[:H, :W]
    pk = load_ink_from(panel)[:H, :W] & ~lines
    st = ndimage.generate_binary_structure(2, 2)
    d_ink = ndimage.binary_dilation(ink2, st, iterations=1)
    d_pk = ndimage.binary_dilation(pk, st, iterations=1)
    miss = int((ink2 & ~d_pk).sum())
    extra = int((pk & ~d_ink).sum())
    return miss + extra, miss, extra


def load_ink_from(panel):
    """把已读入的 RGB 数组按 load_ink 的同一口径二值化（RGB 逐通道 <128）。"""
    return (panel[..., 0] < 128) & (panel[..., 1] < 128) & (panel[..., 2] < 128)


def paint_thickness(mask_hw, thick=LINE_W):
    """把 1px 轨迹加粗到 thick 像素，公平比较穿墨量。"""
    if thick <= 1:
        return mask_hw
    st = ndimage.generate_binary_structure(2, 2)
    return ndimage.binary_dilation(mask_hw, st, iterations=thick // 2)


def crossings(ink, pts, thick):
    H, W = ink.shape
    m = np.zeros((H, W), dtype=bool)
    for (y, x) in pts:
        if 0 <= y < H and 0 <= x < W:
            m[y, x] = True
    return int((paint_thickness(m, thick) & ink).sum())


def main():
    # ---------- [0] 栅格一致性 ----------
    print('=' * 78)
    print('[0] 栅格一致性检验：论文结果格 vs 字形格 是否同一块画布')
    print('    判据：剔掉红/绿线像素后，8 邻域膨胀 1px 仍差的墨像素数（≤%d 记为同格）'
          % GRID_TOL)
    usable = set()
    for key in ROWS:
        tbl, idx = key
        ink = load_ink(os.path.join(GLYPH_DIR, '%s_r%02d_glyph.png' % (tbl, idx)))
        panel = load_png(os.path.join(GLYPH_DIR, '%s_r%02d_A.png' % (tbl, idx)))
        diff, miss, extra = same_canvas(ink, panel)
        ok = diff <= GRID_TOL
        if ok:
            usable.add(key)
        print('    %s#%-3d 尺寸 %dx%d vs %dx%d   残余差 %-5d(失%d/多%d)   %s'
              % (tbl, idx, ink.shape[0], ink.shape[1],
                 panel.shape[0], panel.shape[1], diff, miss, extra,
                 '同格' if ok else '★ 不同画布 → 坐标不可比'))
    print('    ⇒ 可用于坐标比较：%d/%d 行' % (len(usable), len(ROWS)))

    # ---------- [1][2] 一致率 ----------
    print()
    print('=' * 78)
    print('[1][2] 参考线一致率（TOL=%dpx，只统计同格的行）' % TOL)
    print('       l1 逐列比行号 / l2 逐行比列号')
    print('%-10s%-5s%10s%10s%7s%10s%10s%7s'
          % ('字', '指标', '我们l1', '论文l1', 'Δ中位', '我们l2', '论文l2', 'Δ中位'))

    detail = {}
    for key in ROWS:
        tbl, idx = key
        ink = load_ink(os.path.join(GLYPH_DIR, '%s_r%02d_glyph.png' % (tbl, idx)))
        if key not in usable:
            continue
        detail[key] = {}
        for m in METRICS:
            panel = load_png(os.path.join(GLYPH_DIR, '%s_r%02d_%s.png' % (tbl, idx, m)))
            p1, p2 = paths_from_panel(panel)
            res = bidirectional_segment(ink, metric=m, metric2=m)
            o1 = {(y, x)[1]: (y, x)[0] for (y, x) in res['l1_path']}
            o2 = {(y, x)[0]: (y, x)[1] for (y, x) in res['l2_path']}
            d1 = [abs(o1[c] - p1[c]) for c in p1 if c in o1]
            d2 = [abs(o2[r] - p2[r]) for r in p2 if r in o2]
            detail[key][m] = dict(d1=np.median(d1) if d1 else None,
                                  d2=np.median(d2) if d2 else None)
            print('%-10s%-5s%10s%10s%7s%10s%10s%7s'
                  % ('%s#%d' % (tbl, idx), m,
                     res['l1_path'][0][0], p1.get(0, '-'),
                     '%.1f' % detail[key][m]['d1'] if d1 else '-',
                     res['intersect'][1], max(p2.values()) if p2 else '-',
                     '%.1f' % detail[key][m]['d2'] if d2 else '-'))

    n_ok = sum(1 for per in detail.values() for v in per.values()
               if v['d1'] is not None and v['d1'] <= TOL)
    n_tot = sum(1 for per in detail.values() for v in per.values() if v['d1'] is not None)
    print('    l1 逐列中位差 ≤%dpx 的比例：%d/%d = %.1f%%' % (TOL, n_ok, n_tot, 100.0 * n_ok / max(n_tot, 1)))
    n_ok = sum(1 for per in detail.values() for v in per.values()
               if v['d2'] is not None and v['d2'] <= TOL)
    n_tot = sum(1 for per in detail.values() for v in per.values() if v['d2'] is not None)
    print('    l2 逐行中位差 ≤%dpx 的比例：%d/%d = %.1f%%' % (TOL, n_ok, n_tot, 100.0 * n_ok / max(n_tot, 1)))

    # ---------- [3] 穿墨量对照 ----------
    print()
    print('=' * 78)
    print('[3] 穿墨量对照（同一把尺子：都按 %dpx 线宽统计，叠在干净字形上）' % LINE_W)
    print('%-10s%12s%12s%12s%12s'
          % ('字', '论文l1穿墨', '我们l1穿墨', '论文l2穿墨', '我们l2穿墨'))
    t = [0, 0, 0, 0]
    for key in ROWS:
        tbl, idx = key
        ink = load_ink(os.path.join(GLYPH_DIR, '%s_r%02d_glyph.png' % (tbl, idx)))
        panelA = load_png(os.path.join(GLYPH_DIR, '%s_r%02d_A.png' % (tbl, idx)))
        p1, p2 = paths_from_panel(panelA)
        res = bidirectional_segment(ink)
        # 论文线：逐列行号 -> 点集
        pp1 = [(p1[c], c) for c in p1 if key in usable]
        pp2 = [(r, p2[r]) for r in p2 if key in usable]
        v = (crossings(ink, pp1, LINE_W),
             crossings(ink, res['l1_path'], LINE_W),
             crossings(ink, pp2, LINE_W),
             crossings(ink, res['l2_path'], LINE_W))
        if key not in usable:
            print('%-10s      —— 不同画布，不计 ——' % ('%s#%d' % (tbl, idx)))
            continue
        for i in range(4):
            t[i] += v[i]
        print('%-10s%12d%12d%12d%12d' % ('%s#%d' % (tbl, idx), v[0], v[1], v[2], v[3]))
    print('%-10s%12d%12d%12d%12d' % ('合计(同格行)', t[0], t[1], t[2], t[3]))

    # ---------- [4] l2 指标 B vs D ----------
    print()
    print('=' * 78)
    print('[4] l2 选优指标 B vs D（l1 固定 D；论文 §3.4.5 说 B 最差、最终选 D）')
    print('%-10s%16s%22s%22s'
          % ('字', '论文 l2 起点/锚点', 'B: 起点/锚点/穿墨', 'D: 起点/锚点/穿墨'))
    sb = sd = 0
    wd = wb = 0
    for key in ROWS:
        tbl, idx = key
        if key not in usable:
            continue
        ink = load_ink(os.path.join(GLYPH_DIR, '%s_r%02d_glyph.png' % (tbl, idx)))
        panelA = load_png(os.path.join(GLYPH_DIR, '%s_r%02d_A.png' % (tbl, idx)))
        _, p2 = paths_from_panel(panelA)
        rows = sorted(p2)
        pr = p2[rows[-1]]
        out = {}
        for mt in 'BD':
            r = bidirectional_segment(ink, metric='D', metric2=mt)
            out[mt] = (r['start2'][1], r['intersect'][1],
                       crossings(ink, r['l2_path'], 1))
        db, dd = abs(out['B'][1] - pr), abs(out['D'][1] - pr)
        sb += out['B'][2]
        sd += out['D'][2]
        if dd < db:
            wd += 1
        if db < dd:
            wb += 1
        print('%-10s%16s%22s%22s'
              % ('%s#%d' % (tbl, idx), '%d/%d' % (p2[rows[0]], pr),
                 '%d/%d/%d' % out['B'], '%d/%d/%d' % out['D']))
    print('    l2 穿墨合计：B=%d   D=%d' % (sb, sd))
    print('    锚点更接近论文线的次数：B 胜 %d 次，D 胜 %d 次' % (wb, wd))

    # ---------- 结论 ----------
    print()
    print('=' * 78)
    print('【结论 —— 读数前请先读这三条限制】')
    print(' 1. 表3-4（粘连字）的结果格与字形格不是同一画布，坐标不可比，')
    print('    已从一致率与穿墨量中剔除；本脚本对粘连字只证明了"跑得通"。')
    print(' 2. 论文结果格里的红/绿线是**画上去的参考线**，不是程序逐格输出：')
    print('    - 表3-3 十个字的 l2 起点列恒为 72（≈0.40W），与指标无关；')
    print('    - 三个字的四个指标面板绿线**逐像素完全相同**。')
    print('    所以"一致率"只说明"两版走同一条线"，不等于"切分正确"。')
    print(' 3. 论文自己的 l2 线也会切穿笔画（表3-3 上合计 %d 像素），' % t[2])
    print('    故"切线必须走空白通道"不是论文的判据，不能拿它当自动真值。')
    print()
    print(' 论文自身在表3-5/3-6 上报的集级准确率：谱字集A 99.06% / 集B 95.53%')
    print(' （四指标里 D 最优、B 最差；集 A：A=99.06 B=96.26 C=97.20 D=99.06，')
    print('   传统滴水 93.45，投影分割 53.27）。')


if __name__ == '__main__':
    main()
