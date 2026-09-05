import numpy as np
ink = np.zeros((6, 6), dtype=bool)
ink[1:4, 1:4] = True          # 中间涂一个 3×3 墨块
print(ink.shape)              # (6, 6)
print(ink[0:2, 0:2])          # 左上角 2×2 子图：全 False
print(np.where(ink, 0, 255))  # 看看"图"长什么样
print(ink.sum())              # 9 —— 墨迹像素个数