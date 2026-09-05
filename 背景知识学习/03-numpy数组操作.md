# 第 3 课 · numpy 数组操作：四招就够

numpy 让你把"整张图"当单个东西操作，不用写双重循环。项目里用到的就四招：

```python
import numpy as np

# ① 造一张 160行×220列 的全白空图（dtype=bool：每格只有 True/False）
ink = np.zeros((160, 220), dtype=bool)

# ② 切片赋值：把一块矩形区域整体涂成墨迹（segment.py 的 build_synthetic_character 就这么造演示图）
ink[20:58, 22:90] = True

# ③ 切片取子图：按切分点 (xi, yi) 裁出"左上"子图（segment.py 的 crops）
top_left = ink[0:xi, 0:yi]

# ④ 按条件二选一：True→0(黑)，False→255(白)，为了存成图片（demo 的 ink_to_image）
gray = np.where(ink, 0, 255)
```

区间写法 `[20:58, ...]` 含头不含尾：取第 20 行到第 57 行。

## 附送一行：IoU（交并比）

`run_real.py` 用它衡量"切出来的块"和"论文真值部件"形状有多重合：

```python
iou = (a & b).sum() / (a | b).sum()    # 都为黑的格数 ÷ 合起来为黑的格数
```

1 = 完全重合，0 = 完全不搭。

---

## 动手

```python
import numpy as np
ink = np.zeros((6, 6), dtype=bool)
ink[1:4, 1:4] = True          # 中间涂一个 3×3 墨块
print(ink.shape)              # (6, 6)
print(ink[0:2, 0:2])          # 左上角 2×2 子图：全 False
print(np.where(ink, 0, 255))  # 看看"图"长什么样
print(ink.sum())              # 9 —— 墨迹像素个数
```

会了这四招 + IoU 那一行，读 `segment.py` 就没有语法障碍了。
