# -*- coding: utf-8 -*-
"""
【最终定位】真值线在横笔处的"穿越"动作 vs 本实现的"滑走"动作。

真值(面板0)：col 63 (rows 12-72) -> col 73.5 (row 78) -> col 77 (rows 84+)
  即：在 rows 72~84 这 12 行里，从 63 横移到 77，同时下降 12 行。

本实现(c0=77)：row 21 遇阻 -> 向右滑 -> col 103 -> 直落 -> col 111

问题：为什么真值线在 col 63~77 之间能向下走（同时踩墨迹），
      而本实现在 col 77 遇到黑格就滑走了？

关键假设：真值线的起点更低处的"墨迹"其实不是横笔，而是"大"字的撇捺！
本脚本逐行打印 cols 55..85 的墨迹分布，还原真值线所在位置的真实拓扑。
"""
import os
import numpy as np
from PIL import Image

GLY = os.path.join(os.path.dirname(__file__), '..', '..', '文献', 'glyphs')


def load_ink(path, thresh=128):
    a = np.array(Image.open(path).convert('RGB')).astype(int)
    return (a[..., 0] < thresh) & (a[..., 1] < thresh) & (a[..., 2] < thresh)


def main():
    ink = load_ink(os.path.join(GLY, 'p49_img4.png'))
    H, W = ink.shape
    print(f'p49_img4 {W}x{H}')
    print('\n【核心区域逐行墨迹分布】rows 15..95, cols 50..90')
    print('  （# = 墨迹, . = 白；行首数字为 row）')
    hdr = '       ' + ''.join(str((c // 10) % 10) for c in range(50, 91))
    print(hdr)
    print('       ' + ''.join(str(c % 10) for c in range(50, 91)))
    for r in range(15, 96):
        line = ''.join('#' if ink[r, c] else '.' for c in range(50, 91))
        mark = ''
        if r == 21:
            mark = '  <== 本实现 c0=77 遇阻处'
        if r == 78:
            mark = '  <== 真值线横折处(row78, col≈73.5)'
        print(f'  {r:>4} {line}{mark}')

    # 真值线 col=63 从 rows 12..72 的墨迹命中情况
    print('\n【真值线 col=63 逐行检查】rows 10..90')
    miss = []
    for r in range(10, 91):
        band = [62, 63, 64]
        is_ink = any(ink[r, x] for x in band)
        if is_ink:
            miss.append(r)
    print(f'  col=63±1 踩墨迹的行: {miss}')
    print(f'  共 {len(miss)} 行 / 81 行')

    # 关键：col 63 在 rows 12..72 是否被"大"的撇挡住？
    print('\n【拓扑分析】col=63 处各墨迹段的纵向位置')
    col = np.where(ink[:, 63])[0]
    if len(col):
        segs = []
        s = col[0]; p = col[0]
        for v in col[1:]:
            if v - p > 1:
                segs.append((s, p)); s = v
            p = v
        segs.append((s, p))
        for a, b in segs:
            print(f'    rows {a}..{b}  厚 {b-a+1}')
    print('\n  对比 col=77 处各墨迹段：')
    col = np.where(ink[:, 77])[0]
    if len(col):
        segs = []
        s = col[0]; p = col[0]
        for v in col[1:]:
            if v - p > 1:
                segs.append((s, p)); s = v
            p = v
        segs.append((s, p))
        for a, b in segs:
            print(f'    rows {a}..{b}  厚 {b-a+1}')

    print('\n  ★ 关键问题：col=77 的第一段墨迹 rows 22..27（厚 6），')
    print('     本实现在 row=21（即该段正上方）遇到它，j=1/2/3 全黑 -> 滑走。')
    print('     若能在 rows 22..27 连续熔断 6 次，即可穿到 row=28 以下。')
    # 检查穿过后是否通畅
    print('\n  穿越 rows 22..27 后，从 (28, 77) 往下是否通畅？')
    r = 28
    ok = True
    while r < H and not ink[r, 77]:
        r += 1
    print(f'    从 (28,77) 直落到 row={r} 才碰墨迹（可走 {r-28} 行）')
    if r < H:
        col2 = np.where(ink[:, 77])[0]
        segs = []
        s = col2[0]; p = col2[0]
        for v in col2[1:]:
            if v - p > 1:
                segs.append((s, p)); s = v
            p = v
        segs.append((s, p))
        print(f'    col=77 全部墨迹段: {segs}')
        print(f'    -> 只要连续熔断穿过所有墨迹段，就能一路到 l1(row≈96)。')
        total = sum(b - a + 1 for a, b in segs if a < 96)
        print(f'    需熔断总厚度 = {total}')


if __name__ == '__main__':
    main()
