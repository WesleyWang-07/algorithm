# -*- coding: utf-8 -*-
"""
演示：改进滴水算法的双向切分 + 四指标初始滴点优化
==================================================

运行：
    python demo_segment.py

它会依次跑两个用例：
    · 粘连   ：左上/右上之间有一条 1 像素"粘连竖线"（考验第二刀的熔断能力）
    · 无粘连 ：干净谱字（老师发给你的样例就是这种）
每个用例输出到 ./output/：
    overlay_粘连.png  / overlay_无粘连.png  原始图 + 红色 l1(上下切分) + 绿色 l2(左右切分)
    crop_left_top_*.png / crop_right_top_*.png / crop_bottom_*.png   三张子图
    并在终端打印最优初始滴点与四指标 A/B/C/D。

第 55 行 metric='A' 是"第 3 步：四种指标对比"练习改的（原默认 'D'），练完记得改回 'D'。
"""

import os                     # 建文件夹 / 拼路径用
import numpy as np            # 操作布尔数组：二值图就是 True/False 组成的矩阵
from PIL import Image, ImageDraw   # Pillow 库：Image 读写图片，ImageDraw 画线画点
# 下面两个函数来自同目录的 segment.py（"黑盒"，本脚本只负责调用它们）：
from segment import build_synthetic_character, bidirectional_segment


def ink_to_image(ink):
    """布尔墨迹 -> 白底黑字的 RGB 图。"""
    # ink: True=墨迹, False=空白。"说明书"数据，先变成能看到图。
    a = np.where(ink, 0, 255).astype(np.uint8)   # 墨迹→0(黑)，空白→255(白)；uint8=0~255 整数
    return Image.fromarray(a, mode='L').convert('RGB')   # mode='L'=灰度图；转 RGB 为后面能画彩色线


def draw_path(img, path, color, width=3):
    """把一条水滴轨迹画到 img 上。path 的元素是 (r, c)（行, 列），都是 0 基坐标。"""
    d = ImageDraw.Draw(img)
    # 关键：PIL 画图坐标是 (x, y)，x=列、y=行，而我们的路径是 (行, 列) —— 必须互换！
    pts = [(c, r) for (r, c) in path]              # 列表推导式：逐点把 (r,c) 换成 (c,r)
    if len(pts) >= 2:
        d.line(pts, fill=color, width=width, joint='curve')   # 连成线；joint='curve' 拐角更圆滑
    else:
        # 防御性写法：路径只有一个点时 d.line 会报错，改画一个小圆点（椭圆）
        for p in pts:
            d.ellipse([p[0] - width, p[1] - width, p[0] + width, p[1] + width],
                      fill=color)
    return img    # 返回图片，方便链式调用（其实不写 return 也能用）


def main():
    out = 'output'
    os.makedirs(out, exist_ok=True)    # 没有 output/ 文件夹就建一个；已有则跳过不报错

    print('=' * 70)                    # 纯装饰性的分隔线
    print('改进滴水算法 —— 双向切分 + 四指标优化（专利：基于水滴双向飞溅的滴水路径优化）')
    print('=' * 70)

    # ---------- 用例循环：粘连 (True) 和无粘连 (False) 各跑一遍 ----------
    for connect in (True, False):
        tag = '粘连' if connect else '无粘连'     # 中文标签，用来区分文件名
        ink = build_synthetic_character(connect_top=connect)   # "造谱字"：160x220 布尔矩阵
        H, W = ink.shape                         # H=行数(160)，W=列数(220)
        print(f'\n{"-"*70}\n[合成谱字] H={H} W={W}  粘连: {tag}')

        # ---------- 核心调用（第 3 步练习就是改这里的 metric） ----------
        res = bidirectional_segment(ink, metric='A')
        print(type(res), list(res.keys()))
        # res 是一个"结果包"，里面装着：
        #   l1_path：红色第一刀（横向，切上/下）的轨迹；l2_path：绿色第二刀（纵向，切左/右上）
        #   intersect：两刀交点 (xi, yi) —— 切分锚点
        #   crops：按锚点裁出的三张子图；start1/start2：选中的初始滴点
        #   metrics1/metrics2：两刀各自的 A/B/C/D 得分
        l1, l2 = res['l1_path'], res['l2_path']
        xi, yi = res['intersect']

        # ---------- 打印数字（第 3 步表格里抄的就是这些） ----------
        # f-string：{} 里的表达式会被算出来塞进字符串；键名含双引号，所以外层用单引号
        print(f'  最优初始滴点 l1(横向/红色): {res["start1"]}   '
              f'l2(纵向/绿色): {res["start2"]}')
        print(f'  l1 指标(A/B/C/D): '
              f'{res["metrics1"]["A"]}/{res["metrics1"]["B"]}/'
              f'{res["metrics1"]["C"]}/{res["metrics1"]["D"]}')   # 四指标用 "/" 连成一个串
        print(f'  l2 指标(A/B/C/D): '
              f'{res["metrics2"]["A"]}/{res["metrics2"]["B"]}/'
              f'{res["metrics2"]["C"]}/{res["metrics2"]["D"]}')
        print(f'  两路径交点(分割锚点): (r={xi}, c={yi})   '
              f'横长 {len(l1)} 竖长 {len(l2)}')      # 横长/竖长=轨迹上的点数（步数 + 起点）

        # ---------- 叠加可视化：红 l1 / 绿 l2 ----------
        img = ink_to_image(ink)                    # 布尔矩阵 -> 白底黑字图（正常看得到的图）
        draw_path(img, l1, (255, 0, 0))            # 红：上下切分（RGB 三元组，255=纯红）
        draw_path(img, l2, (0, 180, 0))            # 绿：左右切分（180：纯绿太刺眼，压暗一点）
        img.save(os.path.join(out, f'overlay_{tag}.png'))    # os.path.join 只是拼路径

        # ---------- 三张子图 ----------
        for name, arr in res['crops'].items():     # crops 是字典 {left_top, right_top, bottom}
            # 子图同样转白底黑字：墨→0、白→255，再转 RGB 存盘（如 crop_left_top_粘连.png）
            Image.fromarray(np.where(arr, 0, 255).astype(np.uint8), mode='L') \
                .convert('RGB') \
                .save(os.path.join(out, f'crop_{name}_{tag}.png'))

        print(f'  已保存: output/overlay_{tag}.png 及 3 张 crop_*_{tag}.png')

    print('\n' + '=' * 70)
    print('完成。可视化请查看 output/ 下的 PNG。')


if __name__ == '__main__':
    # 固定写法：只有"直接运行本文件"才执行 main()；
    # 如果别的文件 import 这个模块，这行不会触发（避免误运行）。
    main()
