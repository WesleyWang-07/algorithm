# -*- coding: utf-8 -*-
"""
真实谱字验证：用论文《HUNNUThesis》里的真实手写减字谱字"谱字A(=大/七/勾)"跑双向切分，
并与论文公开的"切分结果"（图3-24 的三个部件：大、七、勾）做 IoU 校验。
运行：python run_real.py   （依赖 ../文献/glyphs/ 下提取的嵌入图）
"""
import os
import numpy as np
from PIL import Image, ImageDraw
from segment import bidirectional_segment

GLYPHS = os.path.join(os.path.dirname(__file__), '..', '文献', 'glyphs')
OUT = 'output_real'
os.makedirs(OUT, exist_ok=True)


def load_ink(path, thresh=128):
    """读图 -> 布尔 ink（True=暗色墨迹）。红线因 R 高自然被排除。"""
    im = Image.open(path).convert('RGB')
    a = np.array(im).astype(int)
    ink = (a[..., 0] < thresh) & (a[..., 1] < thresh) & (a[..., 2] < thresh)
    return ink


def ink_to_img(ink):
    return Image.fromarray(np.where(ink, 0, 255).astype(np.uint8), mode='L').convert('RGB')


def draw_path(img, path, color, width=3):
    d = ImageDraw.Draw(img)
    pts = [(c, r) for (r, c) in path]
    if len(pts) >= 2:
        d.line(pts, fill=color, width=width, joint='curve')
    return img


def bbox_sil(ink):
    """返回 ink 的包围盒子图（bool）。"""
    ys, xs = np.where(ink)
    if len(ys) == 0:
        return np.zeros((1, 1), bool)
    return ink[ys.min():ys.max() + 1, xs.min():xs.max() + 1]


def norm_sil(ink, size=(48, 48)):
    b = bbox_sil(ink).astype(np.uint8) * 255
    im = Image.fromarray(b, mode='L').resize(size, Image.NEAREST)
    return np.array(im) > 127


def iou(a, b):
    i = (a & b).sum()
    u = (a | b).sum()
    return i / u if u else 0.0


def main():
    full = load_ink(os.path.join(GLYPHS, 'p49_img4.png'))    # 完整谱字A（剔除红线）
    H, W = full.shape
    print(f'[真实谱字A] 尺寸 {W}x{H}  ink占比 {full.mean():.3f}')
    ink_to_img(full).save(os.path.join(OUT, 'real_char_clean.png'))

    res = bidirectional_segment(full, metric='D')
    l1, l2 = res['l1_path'], res['l2_path']
    xi, yi = res['intersect']
    print(f'  最优初始滴点 l1={res["start1"]} l2={res["start2"]}')
    print(f'  指标 l1(A/B/C/D): ', res['metrics1'])
    print(f'  指标 l2(A/B/C/D): ', res['metrics2'])
    print(f'  两路径交点(切分锚点) = (r={xi}, c={yi})  l1长{len(l1)} l2长{len(l2)}')

    # 叠加可视化（红 l1 / 绿 l2）
    img = ink_to_img(full)
    draw_path(img, l1, (255, 0, 0))
    draw_path(img, l2, (0, 170, 0))
    img.save(os.path.join(OUT, 'real_overlay.png'))
    for name, arr in res['crops'].items():
        ink_to_img(arr).save(os.path.join(OUT, f'real_crop_{name}.png'))

    # ---- 用论文公开的三个部件(大/七/勾)做 IoU 校验 ----
    true = {
        '大': load_ink(os.path.join(GLYPHS, 'p49_img2.png')),
        '七': load_ink(os.path.join(GLYPHS, 'p49_img3.png')),
        '勾': load_ink(os.path.join(GLYPHS, 'p49_img1.png')),
    }
    got = {'left_top': res['crops']['left_top'],
           'right_top': res['crops']['right_top'],
           'bottom': res['crops']['bottom']}

    print('\n=== IoU 校验（裁剪块 vs 论文真值 大/七/勾） ===')
    sil_true = {k: norm_sil(v) for k, v in true.items()}
    sil_got = {k: norm_sil(v) for k, v in got.items()}
    print(f'  {"":<12}' + ''.join(f'{k:>10}' for k in sil_true))
    match = {}
    for gk, gsil in sil_got.items():
        row = {tk: iou(gsil, tsil) for tk, tsil in sil_true.items()}
        best = max(row, key=row.get)
        match[gk] = (best, round(row[best], 3))
        print(f'  {gk:<12}' + ''.join(f'{row[tk]:>10.3f}' for tk in sil_true)
              + f'   -> 匹配 {best}')
    print()
    expect = {'left_top': '大', 'right_top': '七', 'bottom': '勾'}
    all_ok = all(match[k][0] == v for k, v in expect.items())
    for k, v in expect.items():
        ok = match[k][0] == v
        print(f'  {k:>12} 期望={v}  实际={match[k][0]}  IoU={match[k][1]:.3f}  '
              f'{"✓" if ok else "✗"}')
    print(f'\n判定：三块子图与真实部件(大/七/勾)一一对应 -> '
          f'{"校验通过 ✓" if all_ok else "部分不匹配 ✗"}')


if __name__ == '__main__':
    main()
