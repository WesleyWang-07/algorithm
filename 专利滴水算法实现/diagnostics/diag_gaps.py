# -*- coding: utf-8 -*-
"""
【核心验证】划线确认：谱字A 的"大/七"竖直分界缝在哪一列？

方法：对每一列 c，统计"从该列顶部往下，能在不碰墨迹的前提下走多远"
（= 逐列渗透深度），并画出所有候选列，定位那条真正能贯穿上部的缝。

再叠加本实现锚点(46)、报告声称真值(77)、吸引子(110) 做视觉对比。
"""
import os
import numpy as np
from PIL import Image, ImageDraw

GLY = os.path.join(os.path.dirname(__file__), '..', '..', '文献', 'glyphs')
OUT = os.path.join(os.path.dirname(__file__), 'out')


def load_ink(path, thresh=128):
    a = np.array(Image.open(path).convert('RGB')).astype(int)
    return (a[..., 0] < thresh) & (a[..., 1] < thresh) & (a[..., 2] < thresh)


def main():
    ink = load_ink(os.path.join(GLY, 'p49_img4.png'))
    H, W = ink.shape
    print(f'p49_img4: H={H} (行) W={W} (列)')

    # 逐列渗透深度：从 r=0 往下，直到第一次碰墨
    depths = []
    for c in range(W):
        d = 0
        while d < H and not ink[d, c]:
            d += 1
        depths.append(d)
    depths = np.array(depths)

    # 找"局部深通道"：深度明显大于邻居的列区间
    print('\n  逐列渗透深度（cols 40..135，只列变化处）：')
    prev = None
    for c in range(40, 136):
        d = depths[c]
        if prev is None or d != prev:
            print(f'    col={c:>4} ({c/(W-1):>6.3f})  渗透深度={d:>4}')
        prev = d

    # 深通道 = 深度 >= 40 的连续列区间
    print('\n  渗透深度 >= 40 的连续列区间（= 能从上缘一路深入的空隙）：')
    runs = []
    start = None
    for c in range(W):
        if depths[c] >= 40:
            if start is None:
                start = c
        else:
            if start is not None:
                runs.append((start, c - 1))
                start = None
    if start is not None:
        runs.append((start, W - 1))
    for a, b in runs:
        print(f'    cols {a:>4}..{b:<4}  (相对宽 {a/(W-1):.3f}..{b/(W-1):.3f})  '
              f'宽 {b-a+1}  深度 {depths[a:b+1].min()}..{depths[a:b+1].max()}')

    # 只保留落在 δ2 带内 (42, 88) 的深通道
    w1 = int(round(2 / 7 * W)); w2 = int(round(3 / 5 * W))
    print(f'\n  δ2 带 = ({w1}, {w2})；带内的深通道：')
    for a, b in runs:
        if b >= w1 and a <= w2:
            aa, bb = max(a, w1), min(b, w2)
            print(f'    cols {aa}..{bb}  (相对宽 {aa/(W-1):.3f}..{bb/(W-1):.3f})  '
                  f'带内宽 {bb-aa+1}')

    # ---- 画图：叠加"缝"的标注 ----
    img = Image.fromarray(np.where(ink, 0, 255).astype(np.uint8), mode='L').convert('RGB')
    # 放大 3x
    img = img.resize((W * 3, H * 3), Image.NEAREST)
    d = ImageDraw.Draw(img)
    # 渗透深度曲线：把 depths 画成红点列
    for c in range(W):
        for r in range(0, depths[c]):
            pass
    # 标出深通道区间（绿色半透明竖带）
    for a, b in runs:
        if depths[a:b+1].max() >= 40:
            d.rectangle([a * 3, 0, (b + 1) * 3 - 1, H * 3 - 1],
                        outline=(0, 200, 0), width=2)
            d.text((a * 3 + 2, 4), f'{a}-{b}', fill=(0, 160, 0))
    # 三条候选
    for c, col, lab in [(46, (255, 0, 0), 'ours46'),
                        (77, (255, 0, 255), 'rep77'),
                        (110, (0, 0, 255), 'att110')]:
        d.line([(c * 3, 0), (c * 3, H * 3)], fill=col, width=2)
        d.text((c * 3 + 2, 30), lab, fill=col)
    # δ2 带边界
    for c in (w1, w2):
        for y in range(0, H * 3, 30):
            d.line([(c * 3, y), (c * 3, y + 15)], fill=(255, 165, 0), width=3)

    p = os.path.join(OUT, 'gaps_analysis.png')
    img.save(p)
    print(f'\n  已存 {p}')


if __name__ == '__main__':
    main()
