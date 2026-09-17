# -*- coding: utf-8 -*-
"""核对 p49_img4 的方向与尺寸约定，并重算 x_rel 的几种可能口径。"""
import os
import numpy as np
from PIL import Image

GLYPHS = os.path.join(os.path.dirname(__file__), '..', '..', '文献', 'glyphs')


def load_ink(path, thresh=128):
    im = Image.open(path).convert('RGB')
    a = np.array(im).astype(int)
    return (a[..., 0] < thresh) & (a[..., 1] < thresh) & (a[..., 2] < thresh)


def main():
    for name in ['p49_img4.png', 'p47_img0.png']:
        p = os.path.join(GLYPHS, name)
        if not os.path.exists(p):
            continue
        im = Image.open(p)
        ink = load_ink(p)
        H, W = ink.shape
        ys, xs = np.where(ink)
        print(f'{name}: PIL size={im.size} (宽x高)  ndarray shape={ink.shape} (行x列)')
        print(f'  墨迹 bbox: rows {ys.min()}..{ys.max()} (跨 {ys.max()-ys.min()+1} 行)'
              f'  cols {xs.min()}..{xs.max()} (跨 {xs.max()-xs.min()+1} 列)')
        print(f'  墨迹占比 {ink.mean():.4f}  总像素 {ink.size}')
        # 逐行墨迹宽度 vs 逐列墨迹高度，判断哪个方向是"字高"
        row_span = int(xs.max() - xs.min() + 1)
        col_span = int(ys.max() - ys.min() + 1)
        print(f'  水平跨度={row_span}  垂直跨度={col_span}  -> '
              f'{"横向更宽(符合谱字:上宽下窄的扁平字)" if row_span > col_span else "纵向更高"}')
        print()

    # 两种口径下的 x_rel
    ink = load_ink(os.path.join(GLYPHS, 'p49_img4.png'))
    H, W = ink.shape
    print(f'p49_img4: H(行数)={H}  W(列数)={W}')
    print('\n本实现锚点在两种"相对宽"口径下：')
    for c in (46, 77, 110):
        print(f'  c={c:>3}: c/W = {c/W:.4f}   c/(W-1) = {c/(W-1):.4f}')
    print(f'\n若真值 0.524 按 c/W 反解:  c = {0.524*W:.2f}  -> col {int(round(0.524*W))}')
    print(f'若真值 0.524 按 c/(W-1) 反解: c = {0.524*(W-1):.2f} -> col {int(round(0.524*(W-1)))}')
    print(f'\n若按"墨迹包围盒宽"反解（bbox 跨 {146+1} 列）: c_abs = {0.524*147:.1f}')


if __name__ == '__main__':
    main()
