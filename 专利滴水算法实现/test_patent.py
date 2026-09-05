# -*- coding: utf-8 -*-
"""按专利 图4~图12 逐格校验改进水滴核心（Q值→动作 + 飞溅状态机）。"""
import numpy as np
from improved_droplet import _q_decision, _step_patent, drop_improved, path_metrics

G = (1, 0)          # 竖直向下
P = (0, 1)          # 水平向右
N0 = (2, 2)         # 当前滴点
NB = {1: (3, 2), 2: (3, 3), 3: (3, 1),
      4: (2, 3), 5: (2, 1), 6: (1, 3), 7: (1, 1)}


def make(open_cells):
    """构造 5x5 墨迹窗口：仅 open_cells 集合中的邻点为白(可走)，其余邻点为黑。"""
    ink = np.zeros((5, 5), bool)
    for j in range(1, 8):
        if j not in open_cells:
            r, c = NB[j]
            ink[r, c] = True
    return ink


def action(ink, k, s=0):
    nb, Q = _q_decision(ink, *N0, G, k)
    a = _step_patent(ink, *N0, G, k, s)
    return nb, Q, a


def ok(fn, label, want_desc):
    print(f'  {"PASS" if fn else "FAIL"}  {label}')
    if not fn:
        print('       期望:', want_desc)


# 图4  Q=7：仅正前方(n1)开 -> 前跳
_ink = make({1}); nb, Q, a = action(_ink, k=0)
ok(a[0] == 'move' and a[1] + 0 == 3 and a[2] == 2, 'Q=7 正前方开 -> 向下滴落(前进)', 'move 到 (3,2)')

# 图5  Q=6 (k=1)：前n1黑、前右n2开 -> 前右对角
_ink = make({2}); nb, Q, a = action(_ink, k=1)
ok(a[0] == 'move' and (a[1], a[2]) == (3, 3), 'Q=6 k=1 前右开 -> 右下对角', 'move 到 (3,3)')

# 图6  Q=5 (k=-1)：前n1黑、前左n3开 -> 前左对角
_ink = make({3}); nb, Q, a = action(_ink, k=-1)
ok(a[0] == 'move' and (a[1], a[2]) == (3, 1), 'Q=5 k=-1 前左开 -> 左下对角', 'move 到 (3,1)')

# 图7  Q=4 (k=1)：前n1、前右n2黑，右n4开 -> 右侧滑动
_ink = make({4}); nb, Q, a = action(_ink, k=1)
ok(a[0] == 'move' and (a[1], a[2]) == (2, 3), 'Q=4 k=1 右开 -> 向右滑动', 'move 到 (2,3)')

# 图8  Q=3 (k=-1)：前n1、前左n3黑，左n5开 -> 左侧滑动
_ink = make({5}); nb, Q, a = action(_ink, k=-1)
ok(a[0] == 'move' and (a[1], a[2]) == (2, 1), 'Q=3 k=-1 左开 -> 向左滑动', 'move 到 (2,1)')

# 图9/图10 Q=2/1 浅坑 - 飞溅 (k=1, 上右n6开, s=0) -> s+1 跳到上右
_ink = make({6, 7}); nb, Q, a = action(_ink, k=1, s=0)
ok(a[0] == 'move' and (a[1], a[2]) == (1, 3) and a[4] == 1, 'Q=2 浅坑 s=0 -> 上右飞溅 s=1', 'move 到 (1,3), s=1')

# 浅坑 - 回流 (s=1, k=1) -> s=3, k=-k, 原位
_ink = make({6, 7}); nb, Q, a = action(_ink, k=1, s=1)
ok(a[0] == 'reflow' and a[3] == -1 and a[4] == 3, 'Q=2 浅坑 s=1 -> 回流 k=-1 s=3', 'reflow, k=-k, s=3')

# 浅坑 - 放弃 (s=4) -> 前穿熔断
_ink = make({6, 7}); nb, Q, a = action(_ink, k=1, s=4)
ok(a[0] == 'melt', 'Q=2 浅坑 s=4 -> 熔断', 'melt')

# 图11 Q=0：全黑 -> 熔断
_ink = make(set()); nb, Q, a = action(_ink, k=0)
ok(Q == 0 and a[0] == 'melt' and (a[1], a[2]) == (3, 2), 'Q=0 全黑 -> 熔断(向下穿)', 'melt 到 (3,2)')

# 图12 Q<0 (k=1)：仅左侧白 -> 回流 k=-k
_ink = make({5, 3, 7}); nb, Q, a = action(_ink, k=1)
ok(Q < 0 and a[0] == 'reflow' and a[3] == -1, 'Q<0 k=1 仅左开 -> 回流 k=-1', 'reflow k=-1')

print('\n校验完成。')
