# -*- coding: utf-8 -*-
"""
方向变量 k 的实际作用力（S102）—— 它在本项目主流程里到底生效了没有？
==========================================================================
背景：`segment.py` 的 `bidirectional_segment` 默认 `seed=None`，此时
      `make_rng()` 返回 None，而 `improved_droplet.drop_improved` 里
      只有 `rng is not None` 才给 k 赋随机值 → **k 在整个枚举过程中恒为 0**。

      k=0 ⇒ o_j ≡ 1（`_theta_j` 第 76 行）⇒ **方向门控完全关闭**，
      即 2025 CCC 摘要所说的 "direction variable" 机制未被启用。

本脚本对照：seed=None（k≡0） vs seed=1..N（开启随机取向），
比较同一谱字的双向切分结果（交点 / 路径长 / 四指标）。

只读。输出纯 ASCII，便于判定。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from PIL import Image

from segment import bidirectional_segment

HERE = os.path.dirname(os.path.abspath(__file__))
G = os.path.join(HERE, '..', '..', '文献', 'glyphs', 'p49_img4.png')

# ⚠️ 输入口径（2026-09-18 修正，**重要**）：p49_img4.png 内烤着**论文自己的红线标注**
#    —— 247 个纯红像素 (255,0,0)，分布在 rows 94–184。
#    原先这里用 convert('L')，而纯红的 L = 0.299·255 ≈ 76 < 128 ⇒ **红线被判成墨迹**
#    ⇒ l1 贴着论文红线走（r0=92），与本项目正式入口 run_real.py 的 RGB 口径不一致
#    （后者 r0=95）。历史上文档里流传的 "l1=92 / 长149 / 指标 5-0-2-7" 全部源自此处。
#    现统一为 RGB 逐通道判定。
_a = np.array(Image.open(G).convert('RGB')).astype(int)
ink = (_a[..., 0] < 128) & (_a[..., 1] < 128) & (_a[..., 2] < 128)
H, W = ink.shape
print('IMG %d x %d (H x W)' % (H, W))

results = []
for seed in [None] + list(range(1, 21)):
    r = bidirectional_segment(ink, metric='D', metric2='B', seed=seed)
    xi, yi = r['intersect']
    m1, m2 = r['metrics1'], r['metrics2']
    results.append((seed, r['start1'], r['start2'], (xi, yi),
                    len(r['l1_path']), len(r['l2_path']),
                    tuple(m1[k] for k in 'ABCD'), tuple(m2[k] for k in 'ABCD')))
    print('seed=%-5s l1_start=%-9s l2_start=%-9s intersect=%-10s len1=%-4d len2=%-4d m1=%s m2=%s'
          % (seed, str(r['start1']), str(r['start2']), str((xi, yi)),
             len(r['l1_path']), len(r['l2_path']),
             tuple(m1[k] for k in 'ABCD'), tuple(m2[k] for k in 'ABCD')))

base = results[0]
same_intersect = sum(1 for x in results[1:] if x[3] == base[3])
same_start2 = sum(1 for x in results[1:] if x[2] == base[2])
same_m2 = sum(1 for x in results[1:] if x[7] == base[7])
n = len(results) - 1
print('---')
print('baseline(seed=None): l1_start=%s l2_start=%s intersect=%s m1=%s m2=%s'
      % (base[1], base[2], base[3], base[6], base[7]))
print('seeded runs: %d' % n)
print('SAME_intersect = %d/%d' % (same_intersect, n))
print('SAME_l2_start  = %d/%d' % (same_start2, n))
print('SAME_m2        = %d/%d' % (same_m2, n))
uniq_i = sorted(set(x[3] for x in results))
uniq_s2 = sorted(set(x[2] for x in results))
print('distinct intersects: %s' % (uniq_i,))
print('distinct l2 starts:  %s' % (uniq_s2,))
print('DONE')
