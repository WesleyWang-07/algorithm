# -*- coding: utf-8 -*-
"""
真值线几何核对：把 图3-25 的 l1/l2 坐标轴框（O 原点、Y 向右、X 向下、宽 M 高 N）
与 p49_img4 的实际墨迹对齐，量出 图3-25 里 l2 终点蓝点 (x1,y1) 的相对位置，
和论文正文/报告声称的 0.524 做交叉验证。

方法：在 p49_img4 上叠加网格与候选竖线，输出对比图供肉眼核对。
"""
import os
import numpy as np
from PIL import Image, ImageDraw

GLYPHS = os.path.join(os.path.dirname(__file__), '..', '..', '文献', 'glyphs')
OUT = os.path.join(os.path.dirname(__file__), 'out')


def load_ink(path, thresh=128):
    im = Image.open(path).convert('RGB')
    a = np.array(im).astype(int)
    return (a[..., 0] < thresh) & (a[..., 1] < thresh) & (a[..., 2] < thresh)


def ink_to_img(ink):
    return Image.fromarray(np.where(ink, 0, 255).astype(np.uint8), mode='L').convert('RGB')


def bbox(ink):
    ys, xs = np.where(ink)
    return ys.min(), ys.max(), xs.min(), xs.max()


def main():
    os.makedirs(OUT, exist_ok=True)
    full = load_ink(os.path.join(GLYPHS, 'p49_img4.png'))
    H, W = full.shape
    print(f'[p49_img4] 全图 {W}x{H}')
    r0, r1, c0_, c1_ = bbox(full)
    print(f'  墨迹包围盒: rows {r0}..{r1} ({r1-r0+1}), cols {c0_}..{c1_} ({c1_-c0_+1})')

    img = ink_to_img(full)
    d = ImageDraw.Draw(img)

    # 画 10% 网格（相对全图宽）
    for k in range(1, 10):
        x = int(round(W * k / 10))
        d.line([(x, 0), (x, H)], fill=(200, 200, 200), width=1)
        d.text((x + 1, 2), str(k), fill=(120, 120, 120))

    # 三条候选竖线：本实现锚点 46 / 报告真值列 77 / 论文版吸引子 110
    cand = [(46, (0, 170, 0), 'ours 46'),
            (77, (255, 0, 0), 'rep 77'),
            (110, (0, 0, 255), 'attract 110')]
    for c, col, _ in cand:
        d.line([(c, 0), (c, H)], fill=col, width=2)

    # 画 δ2 带边界
    w1 = int(round(2 / 7 * W)); w2 = int(round(3 / 5 * W))
    for c in (w1, w2):
        for y in range(0, H, 12):
            d.line([(c, y), (c, y + 6)], fill=(255, 165, 0), width=2)

    p = os.path.join(OUT, 'truth_check_cols.png')
    img.save(p)
    print(f'  已存 {p}')

    # 逐列统计"该列自上而下第一次遇到墨迹的行"
    print('\n  列  首次撞墨行  相对宽  备注')
    for c in range(0, W, 1):
        if c < 30 or c > 125:
            continue
        # 第一段空白深度
        dep = 0
        while dep < H and not full[dep, c]:
            dep += 1
        tag = ''
        if abs(c - 46) < 2:
            tag = '<== 本实现锚点'
        if abs(c - 77) < 2:
            tag = '<== 报告声称真值'
        if abs(c - 110) < 2:
            tag = '<== 吸引子'
        if dep < 30:
            print(f'  {c:>3} {dep:>10}   {c/(W-1):>6.3f}  {tag}')


if __name__ == '__main__':
    main()
