# -*- coding: utf-8 -*-
"""
改进滴水算法 —— 按专利《基于水滴双向飞溅的滴水路径优化》(CN 20241016 发明) 忠实实现
================================================================================

本文件只依赖本专利，严格按权利要求书第 1-5 条实现：

  S101  设计当前滴点的重力势能计算窗口大小及其权重分布
        窗口 = n0 周围 7 个邻点 (图1)，权值 g_j = 8 - j (图2)
  S102  设计水滴滚动函数，添加遇阻随机取向机制 k，改变不同方向下的重力势能窗口变化
        k ∈ {-1,0,1}，o_j 分段因子 (图3)：见 _theta_j
  S103  设计优先级从高到低为：滴落、飞溅、回流、熔断的滴水规则
        Q_i = max_j(z_j·g_j·o_j)，Q 值 → 动作 + 飞溅状态机 s∈{0..5} (图4~图12)
  S104  设计滴水路径的优化指标，优化路径的初始点 (权利要求5)：A/B/C/D

坐标约定
--------
专利：x 轴正方向竖直向下，y 轴正方向水平向右，待分割图为 M×N。
本实现：img[r, c]  (r=行/竖直, c=列/水平)，与专利 (x,y)=(r,c) 一致。
重力方向 g 允许任意单位方向，以便 l1 横向、l2 纵向两个切分都复用同一份规则。
"""

import numpy as np


# ----------------------------------------------------------------------
# 邻点编号与权值 (权利要求2 / 图1 / 图2)
# ----------------------------------------------------------------------
# 在"重力-垂线"基 (g, p) 下，p = 垂直右侧方向。j=1..7 对应：
#   j=1: +g      (正前方/正下方)    权 7
#   j=2: +g+p    (前右对角)         权 6
#   j=3: +g-p    (前左对角)         权 5
#   j=4: +p      (右侧)             权 4
#   j=5: -p      (左侧)             权 3
#   j=6: -g+p    (后右对角)         权 2
#   j=7: -g-p    (后左对角)         权 1
# 当 g=(1,0) 竖直向下、p=(0,1) 水平向右时，正好是专利图1/图2 的布局。
_G7 = {j: 8 - j for j in range(1, 8)}          # g_j = 8 - j


def perp_of(g):
    """重力方向 g 的垂直右侧方向 (g[1], g[0])。"""
    return (g[1], g[0])


def is_open(ink, r, c):
    """(r,c) 是否是"白色可走"。越界按白处理（允许水滴贴边逃逸）。"""
    H, W = ink.shape
    if r < 0 or c < 0 or r >= H or c >= W:
        return True
    return not ink[r, c]


def _neighbors(g):
    """返回 {j: (dr,dc)}，j=1..7 的邻点相对位移（重力基）。"""
    p = perp_of(g)
    return {
        1: (g[0], g[1]),
        2: (g[0] + p[0], g[1] + p[1]),
        3: (g[0] - p[0], g[1] - p[1]),
        4: (p[0], p[1]),
        5: (-p[0], -p[1]),
        6: (-g[0] + p[0], -g[1] + p[1]),
        7: (-g[0] - p[0], -g[1] - p[1]),
    }


def _theta_j(j, k):
    """
    方向因子 o_j (权利要求3 / 图3)。
      k=0 (初始)          -> o_j = 1, ∀j
      j=1 (正前方)        -> o_1 = 1, ∀k      （重力方向永不受取向影响）
      k=1 (偏右)          -> o_j = (-k)^j = (-1)^j   （左侧 j=3,5,7 变负）
      k=-1 (偏左)         -> o_j = k^(j+1) = (-1)^(j+1)（右侧 j=2,4,6 变负）
    """
    if k == 0 or j == 1:
        return 1
    if k == 1:
        return (-1) ** j
    return (-1) ** (j + 1)          # k == -1


def _q_decision(ink, r, c, g, k):
    """
    计算 Q_i = max_j(z_j·g_j·o_j) 与胜出的邻点 j。

    ✅ 语义（专利图4~图12）：
      · max 只在"白像素(z_j=1)"之间进行；
      · 若 8 邻点全黑（无任何白像素）→ Q = 0（触发熔断），j = None；
      · 若有白像素且其 g_j·o_j 全为负（只在对侧白）→ Q < 0（触发回流）；
      · 若有白像素的 g_j·o_j 为正 → Q 为其中最大者（决定 滴落/对角/滑动/浅坑）。
    这样 Q=0 与 Q<0 能被区分——黑像素的 z=0 并不参与 "谁最大" 的竞争。
    """
    nb = _neighbors(g)
    best_j, best_q = None, None
    for j in range(1, 8):
        dr, dc = nb[j]
        if not is_open(ink, r + dr, c + dc):
            continue                     # 黑像素 z=0，跳过（不参与 max）
        q = _G7[j] * _theta_j(j, k)
        if best_q is None or q > best_q:
            best_q, best_j = q, j
    if best_q is None:
        return None, 0.0                 # 无任何白像素 -> 全黑
    return best_j, best_q


# ----------------------------------------------------------------------
# 飞溅状态机 (S103, 图4~图12)
# ----------------------------------------------------------------------
# s 含义 (图3 页脚 4.1)：
#   0 等待飞溅   1 已飞溅1px   2 水平滚动反向1次   3 飞溅1px+反向1次   4 反向2次   5 飞溅1px+反向2次
# Q 值 → 动作 + s 转移：
#   Q=7 (j=1)     正前方滴落                      s -> 0
#   Q=6 (j=2)     前右对角滴落   s ∈{0,4,5}->s; {1,3}->s-1; {2}->0
#   Q=5 (j=3)     前左对角滴落   同上
#   Q=4 (j=4)     右侧滑动       s ∈{0,1,2,3}->s; {4,5}->0(且改为前跳)
#   Q=3 (j=5)     左侧滑动       同上
#   Q=2/1 (j=6/7) 浅坑：(0,2)->splash(s+1, 跳向后对角); (1,3)->reflow(s+2, k=-k); (4,5)->0(前跳/熔断)
#   Q=0          全黑 -> 熔断(前穿1px)  s->0
#   Q<0          仅对侧白 -> 回流(原位, s+2, k=-k)
def _step_patent(ink, r, c, g, k, s):
    """返回三种动作之一：
       ('move', nr, nc, k, s)
       ('reflow', r, c, -k, s+2)          # 原位回流
       ('melt', nr, nc, k, 0)             # 前穿熔断
    """
    j, Q = _q_decision(ink, r, c, g, k)
    nb = _neighbors(g)

    if Q == 0:                                        # 全黑包围 -> 熔断
        return ('melt', r + g[0], c + g[1], k, 0)
    if Q < 0:                                         # 仅对侧白 -> 回流
        return ('reflow', r, c, -k, s + 2)

    # Q ∈ {7,6,5,4,3,2,1}，j 已确定
    if j == 1:                                        # 正前方滴落
        return ('move', r + g[0], c + g[1], k, 0)
    if j in (2, 3):                                   # 前对角滴落 (Q=6/5)
        dr, dc = nb[j]
        if s in (1, 3):
            s2 = s - 1
        elif s == 2:
            s2 = 0
        else:
            s2 = s
        return ('move', r + dr, c + dc, k, s2)
    if j in (4, 5):                                   # 水平滑动 (Q=4/3)
        if s in (4, 5):
            s2 = 0
            return ('move', r + g[0], c + g[1], k, s2)   # 改为前跳
        dr, dc = nb[j]
        return ('move', r + dr, c + dc, k, s)
    # j ∈ {6,7}：浅坑 (Q=2/1)
    if s in (0, 2):                                   # 飞溅：跳向后(-g)对角
        dr, dc = nb[j]
        return ('move', r + dr, c + dc, k, s + 1)
    if s in (1, 3):                                   # 回流
        return ('reflow', r, c, -k, s + 2)
    # s ∈ {4,5}：放弃，前穿熔断
    return ('melt', r + g[0], c + g[1], k, 0)


def drop_improved(ink, r0, c0, g, max_steps=None, terminate_at=None, rng=None):
    """
    按专利规则生成一条滴水路径。

    参数
    ----
    ink          : HxW 布尔阵, True=黑(墨迹)
    r0, c0       : 初始滴点 (专利记作 x°=r0, y°=c0)
    g            : 重力方向 (dr,dc)；如 (1,0) 竖直向下、(0,1) 水平向右
    max_steps    : 最大步数
    terminate_at : 可选格点集，水滴步入即停（用于 l2 与 l1 交汇）
    rng          : np.random.Generator / RandomState，遇阻随机取向用；None 时保持 k 不随机

    返回 dict：path, melt(d=指标A), offsets(v=指标C), start, end, stopped_by
    """
    H, W = ink.shape
    if max_steps is None:
        max_steps = 8 * (H + W) + 2000

    r, c = r0, c0
    k = 0                       # 方向位：0 初始, 1 偏右(+p), -1 偏左(-p)
    s = 0                       # 飞溅状态
    oriented = False            # 是否已随机取向
    path = [(r, c)]
    melt = 0
    offsets = 0
    visited = {(r, c)}
    reason = 'boundary'

    def _record(nr, nc, is_melt):
        nonlocal r, c, melt, offsets
        if (nr - r, nc - c) != g:
            offsets += 1
        r, c = nr, nc
        if is_melt:
            melt += 1

    for step_i in range(max_steps):
        if terminate_at is not None and (r, c) in terminate_at and step_i > 0:
            reason = 'terminate_at'
            break

        # 遇阻随机取向（S102）：首次遇到浅坑/死路（Q<=0 或胜出邻点为后向 j∈{6,7}）
        # 时才定 k；之前的正常滑行不定取向——与专利图13~15"落点遇阻才取向"一致
        if not oriented:
            j, Q = _q_decision(ink, r, c, g, k)
            if Q == 0 or Q < 0 or j in (6, 7):
                if rng is not None:
                    k = int(rng.choice([-1, 1]))         # 对称随机取向；可复现靠外部固定种子
                oriented = True

        act = _step_patent(ink, r, c, g, k, s)

        if act[0] == 'reflow':
            # 原位回流：位置不动，k=-k，s+=2。s 到 4/5 不在这里抢先熔断，
            # 交给 _step_patent 的状态机下一步按图4~图12 消化
            # （再遇浅坑→熔断；侧滑→前跳归零；正前白→滴落归零）。
            nk, ns = act[3], act[4]
            if ns > 5:      # 专利状态表未定义 s>5：回流预算已耗尽，保底熔断
                _record(r + g[0], c + g[1], True); s = 0; k = nk
            else:
                k = nk; s = ns
        elif act[0] == 'melt':
            nr, nc, k, s = act[1], act[2], act[3], act[4]
            _record(nr, nc, True)
        else:  # 'move'
            nr, nc, k, s = act[1], act[2], act[3], act[4]
            if (nr, nc) == (r, c) or (nr, nc) in visited:
                # 兜底：防止原地死循环，强制前穿熔断
                _record(r + g[0], c + g[1], True); s = 0
            else:
                _record(nr, nc, False)

        path.append((r, c))
        visited.add((r, c))

        if r < 0 or r >= H or c < 0 or c >= W:
            reason = 'boundary'
            break
    else:
        reason = 'max_steps'

    return {
        'path': path,
        'melt': melt,
        'offsets': offsets,
        'start': (r0, c0),
        'end': (r, c),
        'stopped_by': reason,
    }


# ----------------------------------------------------------------------
# 四种优化指标（权利要求5）
# ----------------------------------------------------------------------
def metric_B(res, g):
    """
    指标 B = |x* − x°|：初始滴点与终点在"垂直重力方向"上的偏移。
    对横向水流 g=(0,1) 取行漂移 |r1−r0|；对纵向水流 g=(1,0) 取列漂移 |c1−c0|。
    """
    (r0, c0), (r1, c1) = res['start'], res['end']
    p = perp_of(g)
    return abs((r1 - r0) * p[0] + (c1 - c0) * p[1])


def path_metrics(res, g):
    """
    指标 A/B/C/D（权利要求5）：
      A = d        : 熔断像素数（最小化）           -> res['melt']
      B = |x*−x°|  : 垂直重力方向上的始末偏移（最小化） -> metric_B
      C = v        : 累计偏移次数（最小化）           -> res['offsets']
      D = d + B + v: 三指标融合（论文/专利结论最优）
    """
    d_A = res['melt']
    B = metric_B(res, g)
    C = res['offsets']
    return {'A': d_A, 'B': B, 'C': C, 'D': d_A + B + C}
