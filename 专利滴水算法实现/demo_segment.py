# -*- coding: utf-8 -*-
"""
演示：改进滴水算法的双向切分 + 四指标初始滴点优化
==================================================

运行：
    python demo_segment.py

输出到 ./output/：
    overlay.png       原始图 + 红色 l1(上下切分) + 绿色 l2(左右切分)
    crop_left_top.png 左上子图
    crop_right_top.png 右上子图
    crop_bottom.png   下部子图
    并在终端打印四指标与最优初始滴点。
"""

import os
import numpy as np
from PIL import Image, ImageDraw
from segment import build_synthetic_character, bidirectional_segment


def ink_to_image(ink):
    """布尔墨迹 -> 白底黑字的 RGB 图。"""
    a = np.where(ink, 0, 255).astype(np.uint8)
    return Image.fromarray(a, mode='L').convert('RGB')


def draw_path(img, path, color, width=3):
    d = ImageDraw.Draw(img)
    pts = [(c, r) for (r, c) in path]              # PIL 用 (x,y) = (col,row)
    if len(pts) >= 2:
        d.line(pts, fill=color, width=width, joint='curve')
    else:
        for p in pts:
            d.ellipse([p[0] - width, p[1] - width, p[0] + width, p[1] + width],
                      fill=color)
    return img


def main():
    out = 'output'
    os.makedirs(out, exist_ok=True)

    print('=' * 70)
    print('改进滴水算法 —— 双向切分 + 四指标优化（专利：基于水滴双向飞溅的滴水路径优化）')
    print('=' * 70)

    for connect in (True, False):
        tag = '粘连' if connect else '无粘连'
        ink = build_synthetic_character(connect_top=connect)
        H, W = ink.shape
        print(f'\n{"-"*70}\n[合成谱字] H={H} W={W}  粘连: {tag}')

        res = bidirectional_segment(ink, metric='D')
        l1, l2 = res['l1_path'], res['l2_path']
        xi, yi = res['intersect']

        print(f'  最优初始滴点 l1(横向/红色): {res["start1"]}   '
              f'l2(纵向/绿色): {res["start2"]}')
        print(f'  l1 指标(A/B/C/D): '
              f'{res["metrics1"]["A"]}/{res["metrics1"]["B"]}/'
              f'{res["metrics1"]["C"]}/{res["metrics1"]["D"]}')
        print(f'  l2 指标(A/B/C/D): '
              f'{res["metrics2"]["A"]}/{res["metrics2"]["B"]}/'
              f'{res["metrics2"]["C"]}/{res["metrics2"]["D"]}')
        print(f'  两路径交点(分割锚点): (r={xi}, c={yi})   '
              f'横长 {len(l1)} 竖长 {len(l2)}')

        # ---- 叠加可视化：红 l1 / 绿 l2 ----
        img = ink_to_image(ink)
        draw_path(img, l1, (255, 0, 0))       # 红：上下切分
        draw_path(img, l2, (0, 180, 0))       # 绿：左右切分
        img.save(os.path.join(out, f'overlay_{tag}.png'))

        # ---- 三张子图 ----
        for name, arr in res['crops'].items():
            Image.fromarray(np.where(arr, 0, 255).astype(np.uint8), mode='L') \
                .convert('RGB') \
                .save(os.path.join(out, f'crop_{name}_{tag}.png'))

        print(f'  已保存: output/overlay_{tag}.png 及 3 张 crop_*_{tag}.png')

    print('\n' + '=' * 70)
    print('完成。可视化请查看 output/ 下的 PNG。')


if __name__ == '__main__':
    main()
