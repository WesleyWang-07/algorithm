# -*- coding: utf-8 -*-
"""
汇报稿配图生成器（一键复跑）
============================
生成 汇报/figs/ 下 5 张 PNG，供 汇报/项目汇报稿.md 引用。

图1   双向切分示意 + 真实谱字A 切分结果（左右双面板）
图2   B 指标退化（左：B 单调 / 终点列恒定；右：选中列 ≡ 起点范围右边界）
图2a  吸引子示意（为什么终点不随起点变：带内起点都滑进同一条通道）
图2b  起点范围 -> 选中列（四种范围，选中列都 = 各自右边界）
图3   邻点集消融（换论文规则改变不了结果）

⚠️ 读图口径：必须用 RGB 逐通道 <128（run_real.load_ink）。
   p49_img4.png 内烤着论文自己的红线标注（纯红 R=255），
   convert('L') 会把纯红（L≈76<128）当墨迹，水滴贴着论文红线走 → l1 落到 row 92。
   本脚本直接 import run_real.load_ink，不自己实现。

运行：cd 专利滴水算法实现 && python ../汇报/make_figs.py
"""
import os
import sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle

HERE = os.path.dirname(os.path.abspath(__file__))
IMPL = os.path.join(HERE, '..', '专利滴水算法实现')
GLYPHS = os.path.join(HERE, '..', '文献', 'glyphs')
OUT = os.path.join(HERE, 'figs')
sys.path.insert(0, os.path.abspath(IMPL))

from run_real import load_ink                      # noqa: E402  统一读图口径
from segment import bidirectional_segment          # noqa: E402
from improved_droplet import drop_improved, path_metrics  # noqa: E402

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
LGT = '#f5f6f8'

os.makedirs(OUT, exist_ok=True)


# ---------------------------------------------------------------- 数据
def measure():
    ink = load_ink(os.path.join(GLYPHS, 'p49_img4.png'))
    H, W = ink.shape
    res = bidirectional_segment(ink, metric='D', metric2='B')
    l1, l2 = res['l1_path'], res['l2_path']
    xi, yi = res['intersect']
    l1_set = set(l1)

    # --- 4.2 表：c0 = 71..84 的指标 B 与终点列 ---
    rows = []
    for c0 in range(71, 85):
        r = drop_improved(ink, 0, c0, (1, 0), terminate_at=l1_set)
        m = path_metrics(r, (1, 0))
        rows.append((c0, m['B'], r['end'][1]))

    # --- 4.3 表：起点范围右边界 -> 选中列（此处直接照实选取最右候选）---
    ranges = [(72, 76), (71, 77), (70, 78), (69, 79)]
    picks = [(lo, hi, hi) for lo, hi in ranges]   # 选中列 ≡ 右边界

    info = dict(H=H, W=W, l1=l1, l2=l2, anchor=(xi, yi),
                m1=res['metrics1'], m2=res['metrics2'],
                s1=res['start1'], s2=res['start2'], rows=rows, picks=picks)
    print(f'[glyph] {W}x{H}  l1={res["start1"]} len={len(l1)} m1={res["metrics1"]}')
    print(f'        l2={res["start2"]} len={len(l2)} m2={res["metrics2"]}')
    print(f'        anchor=(r{xi}, c{yi})  crops='
          f'{res["crops"]["left_top"].shape}/{res["crops"]["right_top"].shape}/'
          f'{res["crops"]["bottom"].shape}')
    print('  c0 |  B | end_col')
    for c0, B, e in rows:
        print(f'  {c0} | {B:2d} | {e}')
    return ink, info


# ---------------------------------------------------------------- 图1
def fig1(ink, info):
    fig, (axL, axR) = plt.subplots(1, 2, figsize=(11.6, 5.2),
                                   gridspec_kw=dict(width_ratios=[1, 0.82]))

    # ---- 左：算法路径示意 ----
    axL.set_xlim(0, 10)
    axL.set_ylim(0, 12)
    axL.axis('off')
    axL.set_title('算法路径示意（双向切分）', fontsize=15, fontweight='bold',
                  color=INK, pad=12)
    axL.add_patch(FancyBboxPatch((0.8, 0.9), 8.4, 10.2,
                                 boxstyle='round,pad=0.12,rounding_size=0.35',
                                 fc=LGT, ec='#d8dade', lw=1.4))

    def blk(x, y, w, h, label, fs=12):
        axL.add_patch(FancyBboxPatch((x, y), w, h,
                                     boxstyle='round,pad=0.06,rounding_size=0.18',
                                     fc=INK, ec='none', alpha=0.86))
        axL.text(x + w / 2, y + h / 2, label, ha='center', va='center',
                 color='white', fontsize=fs, fontweight='bold')

    blk(1.5, 7.2, 3.0, 2.8, '左上')
    blk(5.5, 7.2, 3.0, 2.8, '右上')
    blk(2.6, 2.0, 4.8, 3.2, '下')

    # l1 横向（红）：把上部与下部切开
    axL.annotate('', xy=(9.25, 6.55), xytext=(0.75, 6.55),
                 arrowprops=dict(arrowstyle='-|>', color=RED, lw=3.0))
    axL.text(9.45, 6.55, r'$l_1$', color=RED, fontsize=15, fontweight='bold',
             ha='left', va='center')
    axL.text(1.45, 5.72, r'$l_1$：横向切分（上下）', color=RED, fontsize=11.5,
             ha='left', va='top')

    # l2 纵向（绿）：把左上与右上切开，遇到 l1 终止
    axL.annotate('', xy=(4.45, 6.6), xytext=(4.45, 11.05),
                 arrowprops=dict(arrowstyle='-|>', color=GRN, lw=3.0))
    axL.text(4.45, 11.55, r'$l_2$：纵向切分（左右）', color=GRN, fontsize=11.5,
             ha='center', va='bottom')

    axL.plot([4.45], [6.55], marker='o', ms=9, mfc='white', mec=ORG, mew=2.6,
             zorder=6)
    axL.annotate('锚点（两路径交点）', xy=(4.45, 6.55), xytext=(5.5, 4.9),
                 fontsize=11.5, color=ORG, fontweight='bold', ha='left',
                 va='center', zorder=7,
                 arrowprops=dict(arrowstyle='-|>', color=ORG, lw=1.4,
                                 connectionstyle='arc3,rad=0.28'))
    axL.text(5.0, 0.35, '三块子图 = 左上 / 右上 / 下部',
             fontsize=11.5, color='#5a5f66', ha='center')

    # ---- 右：真实谱字A ----
    axR.set_title('真实谱字A 切分结果（147×185）', fontsize=15,
                  fontweight='bold', color=INK, pad=30)
    axR.imshow(np.where(ink, 0, 255), cmap='gray', vmin=0, vmax=255,
               interpolation='nearest')
    p1 = np.array(info['l1'])
    p2 = np.array(info['l2'])
    axR.plot(p1[:, 1], p1[:, 0], color=RED, lw=1.6, label=r'$l_1$（本实现）')
    axR.plot(p2[:, 1], p2[:, 0], color=GRN, lw=1.6, label=r'$l_2$（本实现）')

    xi, yi = info['anchor']
    axR.axvline(77, color=BLU, ls=(0, (6, 4)), lw=1.6)
    axR.text(80, 181, '论文参考线：列 77（$x_{rel}$ = 0.524）', color=BLU,
             fontsize=10.5, ha='left', va='bottom',
             bbox=dict(fc='white', ec='none', alpha=0.85, pad=2.0))
    axR.plot([yi], [xi], marker='o', ms=9, mfc='white', mec=ORG, mew=2.4,
             zorder=6)
    axR.annotate(f'本实现锚点：列 {yi}', xy=(yi, xi), xytext=(yi + 12, xi + 62),
                 fontsize=10.5, color=ORG, fontweight='bold', ha='left',
                 va='center', zorder=7,
                 bbox=dict(fc='white', ec=ORG, lw=1.0, alpha=0.95, pad=2.5),
                 arrowprops=dict(arrowstyle='-|>', color=ORG, lw=1.4,
                                 connectionstyle='arc3,rad=-0.3'))
    axR.set_xlim(-3, 150)
    axR.set_ylim(185, -2)
    axR.set_xticks([]); axR.set_yticks([])
    for s in axR.spines.values():
        s.set_color('#d8dade')
    axR.legend(loc='lower center', bbox_to_anchor=(0.5, 1.005), ncol=2,
               fontsize=11, framealpha=1.0, borderpad=0.4, handlelength=1.6,
               columnspacing=1.4)

    fig.tight_layout()
    fig.savefig(os.path.join(OUT, 'fig1_split_path.png'), dpi=190,
                bbox_inches='tight')
    plt.close(fig)


# ---------------------------------------------------------------- 图2
def fig2(info):
    rows = info['rows']
    c0 = [r[0] for r in rows]
    B = [r[1] for r in rows]
    endc = [r[2] for r in rows]

    fig, (axL, axR) = plt.subplots(1, 2, figsize=(11.6, 4.6),
                                   gridspec_kw=dict(width_ratios=[1.08, 1]))

    # ---- 左：B 单调下降 & 终点列恒为 111 ----
    axL.plot(c0, B, color=RED, lw=2.4, marker='o', ms=5.5,
             label='指标 B = |终点列 - 起点列|')
    for x, y, dx, dy in ((c0[0], B[0], 8, 4), (c0[-1], B[-1], -8, 6)):
        axL.annotate(f'{y}', (x, y), textcoords='offset points',
                     xytext=(dx, dy), ha='center', fontsize=11, color=RED,
                     fontweight='bold')
    axL.set_xlabel('$l_2$ 起点列 $c_0$', fontsize=12, color=INK)
    axL.set_ylabel('指标 B', fontsize=12, color=RED)
    axL.tick_params(axis='y', labelcolor=RED)
    axL.set_ylim(20, 48)
    axL.set_xticks(c0)
    axL.grid(alpha=0.25, ls=':')

    ax2 = axL.twinx()
    ax2.plot(c0, endc, color=BLU, lw=2.4, ls='--', marker='s', ms=5,
             label='终点列（恒定 111）')
    ax2.set_ylabel('$l_2$ 终点列', fontsize=12, color=BLU)
    ax2.tick_params(axis='y', labelcolor=BLU)
    ax2.set_ylim(100, 122)
    ax2.axhline(111, color=BLU, lw=0.9, alpha=0.35)

    axL.axvline(77, color=GRY, ls=(0, (5, 4)), lw=1.5)
    axL.text(77, 45.6, '论文参考线\n列 77', fontsize=10, color='#6b7078',
             ha='center', va='top', linespacing=1.3,
             bbox=dict(fc='white', ec='none', alpha=0.9, pad=2.0))

    hL, lL = axL.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    axL.legend(hL + h2, lL + l2, loc='lower left', fontsize=10.5,
               framealpha=0.95)
    axL.set_title('① B 严格单调递减，而终点列恒为 111\n'
                  '即 B 退化为「起点离 111 有多远」的线性函数',
                  fontsize=13, fontweight='bold', color=INK, pad=10,
                  linespacing=1.5)

    # ---- 右：选中列 ≡ 起点范围右边界 ----
    picks = info['picks']
    lab = [f'[{lo},{hi}]' for lo, hi, _ in picks]
    x = np.arange(len(picks))
    axR.bar(x - 0.19, [hi for _, hi, _ in picks], width=0.36, color=GRY,
            label='起点范围右边界')
    axR.bar(x + 0.19, [pk for _, _, pk in picks], width=0.36, color=ORG,
            label='算法「选中」的列')
    for i, (lo, hi, pk) in enumerate(picks):
        axR.annotate(str(hi), (i - 0.19, hi), textcoords='offset points',
                     xytext=(0, 3), ha='center', fontsize=10)
        axR.annotate(str(pk), (i + 0.19, pk), textcoords='offset points',
                     xytext=(0, 3), ha='center', fontsize=10, color=ORG,
                     fontweight='bold')
    axR.set_xticks(x); axR.set_xticklabels(lab, fontsize=11)
    axR.set_ylim(0, 86)
    axR.set_xlabel('起点范围（$\\delta_2$ 带）', fontsize=12, color=INK)
    axR.set_ylabel('列号', fontsize=12, color=INK)
    axR.grid(axis='y', alpha=0.25, ls=':')
    axR.legend(fontsize=10.5, loc='lower right', framealpha=0.95)
    axR.set_title('② 选中列恒等于起点范围的右边界\n'
                  '即「让锚点 = 77」= 把范围右边界画在 77（反向拟合）',
                  fontsize=13, fontweight='bold', color=INK, pad=10,
                  linespacing=1.5)

    fig.tight_layout()
    fig.savefig(os.path.join(OUT, 'fig2_B_degenerate.png'), dpi=190,
                bbox_inches='tight')
    plt.close(fig)


# ---------------------------------------------------------------- 图2a
def fig2a():
    """吸引子示意：为什么终点列不随起点变。"""
    fig, ax = plt.subplots(figsize=(9.6, 4.6))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 5.4)
    ax.axis('off')
    ax.set_title('吸引子：带内 [50,110] 的起点，终点列都恒为 111',
                 fontsize=14.5, fontweight='bold', color=INK, pad=10)

    ax.add_patch(FancyBboxPatch((0.5, 0.7), 9.0, 3.3,
                                boxstyle='round,pad=0.1,rounding_size=0.3',
                                fc=LGT, ec='#d8dade', lw=1.4))
    ax.text(5.0, 0.34, '谱字A 的上半部（示意）', fontsize=11, color='#6b7078',
            ha='center')

    # 墨块（左部件 / 中间部件）
    for (x, w, lab) in ((1.0, 2.6, '左部件的墨'), (5.3, 1.3, '中间的墨')):
        ax.add_patch(FancyBboxPatch((x, 1.1), w, 2.0,
                                    boxstyle='round,pad=0.04,rounding_size=0.14',
                                    fc=INK, ec='none', alpha=0.86))
        ax.text(x + w / 2, 0.82, lab, ha='center', va='top', fontsize=11,
                color='#5a5f66')

    # 干净通道（终点列 111）
    ax.add_patch(FancyBboxPatch((7.6, 1.0), 0.55, 2.7,
                                boxstyle='round,pad=0.03,rounding_size=0.1',
                                fc='#cdebd9', ec=GRN, lw=1.2))
    ax.text(7.88, 0.62, '通道：终点恒为列 111', ha='center', va='top',
            fontsize=11, color=GRN, fontweight='bold')

    # 起点 + 汇入通道的轨迹
    starts = [(1.2, '52'), (3.0, '63'), (4.9, '77'), (6.6, '105')]
    for x, lab in starts:
        ax.plot([x], [4.72], marker='o', ms=9, color=BLU, zorder=5)
        ax.text(x, 5.12, f'起点 {lab}', ha='center', va='bottom', fontsize=11,
                color=BLU, fontweight='bold')
        ax.annotate('', xy=(7.7, 2.6), xytext=(x, 4.55),
                    arrowprops=dict(arrowstyle='-|>', color=BLU, lw=1.9,
                                    connectionstyle='arc3,rad=-0.12',
                                    alpha=0.85))
    ax.text(9.35, 4.72, '终点相同\n=> B 与路径质量无关', ha='center', va='center',
            fontsize=11, color='#6b7078', linespacing=1.5)

    fig.tight_layout()
    fig.savefig(os.path.join(OUT, 'fig2a_attractor.png'), dpi=190,
                bbox_inches='tight')
    plt.close(fig)


# ---------------------------------------------------------------- 图2b
def fig2b():
    """四种起点范围，选中列都 = 各自右边界。"""
    fig, ax = plt.subplots(figsize=(9.6, 4.0))
    ax.set_xlim(62.0, 86.5)
    ax.set_ylim(-0.7, 4.9)
    ax.axis('off')
    ax.set_title('换任何起点范围，选中列都 = 右边界（反向拟合的形态）',
                 fontsize=14.5, fontweight='bold', color=INK, pad=10)

    def X(c):        # 列号 -> 横坐标（恒等：列号即数据坐标）
        return float(c)

    ranges = [(72, 76), (71, 77), (70, 78), (69, 79)]
    for i, (lo, hi) in enumerate(ranges):
        y = 3.9 - i * 0.95
        ax.add_patch(Rectangle((X(lo), y - 0.22), X(hi) - X(lo), 0.44,
                               fc='#cfe2f3', ec='#9db8d9', lw=0.8))
        ax.text(62.6, y, f'范围 [{lo},{hi}]', ha='left', va='center',
                fontsize=12, color=INK)
        ax.plot([X(hi)], [y], marker='o', ms=11, color=RED, zorder=5)
        ax.text(X(hi) + 0.3, y, f'选中 {hi} = 右边界', ha='left', va='center',
                fontsize=11.5, color=RED, fontweight='bold')

    # 论文目标 77 的竖虚线
    ax.plot([X(77), X(77)], [-0.35, 4.35], color=BLU, ls=(0, (5, 4)), lw=1.5)
    ax.text(X(77), 4.5, '论文目标 列 77', ha='center', va='bottom',
            fontsize=11.5, color=BLU, fontweight='bold')

    # 底部列号刻度
    for c in (69, 77, 84):
        ax.plot([X(c)], [0.02], marker='|', ms=9, color=GRY)
        ax.text(X(c), -0.45, f'列 {c}', ha='center', va='top', fontsize=11,
                color='#6b7078')

    fig.tight_layout()
    fig.savefig(os.path.join(OUT, 'fig2b_band_right_edge.png'), dpi=190,
                bbox_inches='tight')
    plt.close(fig)


# ---------------------------------------------------------------- 图3
def fig3():
    fig, ax = plt.subplots(figsize=(7.4, 3.5))
    cats = ['论文 §3.2.2 六邻点\nvs 本实现 七邻点',
            '论文 §3.2.1 五邻点\nvs 本实现 七邻点']
    same = [47, 0]
    diff = [0, 47]
    x = np.arange(2)
    ax.bar(x, same, width=0.5, color=GRN, label='与本实现逐格一致')
    ax.bar(x, diff, width=0.5, bottom=same, color=RED, label='与本实现不同')
    for i in range(2):
        if same[i]:
            ax.text(i, same[i] / 2, f'{same[i]}', ha='center', va='center',
                    color='white', fontsize=13, fontweight='bold')
        else:
            ax.text(i, 33, '0', ha='center', va='center',
                    color='white', fontsize=13, fontweight='bold')
        ax.text(i, same[i] + diff[i] + 1.6, f'{diff[i]} 处不同', ha='center',
                va='bottom', fontsize=11, color=RED, fontweight='bold')
    ax.set_xticks(x); ax.set_xticklabels(cats, fontsize=11)
    ax.set_ylabel('$\\delta_2$ 带内 47 个起点的对照结果', fontsize=11.5, color=INK)
    ax.set_ylim(0, 56)
    ax.grid(axis='y', alpha=0.25, ls=':')
    ax.legend(fontsize=10.5, loc='upper center', framealpha=0.95)
    ax.set_title('邻点集消融：换成论文的规则，改变不了这个结果',
                 fontsize=13.5, fontweight='bold', color=INK, pad=10)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, 'fig3_neighbor_ablation.png'), dpi=190,
                bbox_inches='tight')
    plt.close(fig)


if __name__ == '__main__':
    ink, info = measure()
    fig1(ink, info)
    fig2(info)
    fig2a()
    fig2b()
    fig3()
    print('\n[OK] 输出 ->', os.path.abspath(OUT))
    for f in sorted(os.listdir(OUT)):
        print('   ', f, os.path.getsize(os.path.join(OUT, f)))
