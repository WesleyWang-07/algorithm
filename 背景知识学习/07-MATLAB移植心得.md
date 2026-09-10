# 07-MATLAB 移植心得 —— 同一个算法，两种语言

> 配套：`../MATLAB/`（全部函数与 `../专利滴水算法实现/` 一一对应，已用本机 R2024b 验证）
> 前提：已学完 01~06（Python 侧）；本课时长约 40 分钟
> 学习方式：左手 Python 文件、右手 MATLAB 文件，并排对照；每节都有一个"对照点"。

## 1. 先记住总图：文件名=函数名，一一对应

| 概念 | Python | MATLAB |
|---|---|---|
| 白色可走 | `improved_droplet.py` `is_open` | `is_open.m` |
| 势能 `Q_i=max(z·g·o)` | `_q_decision` | `q_decision.m` |
| 单步状态机 (+k, +s) | `_step_patent` | `step_patent.m` |
| 滴水主循环 | `drop_improved` | `drop_improved.m` |
| 四指标 | `path_metrics` | `path_metrics.m` |
| 双向切分 | `segment.py` | `bidirectional_segment.m` |

MATLAB 的一个硬规则：**文件里第一个 `function` 的名字 = 文件名**（`drop_improved.m`
的主函数必须叫 `drop_improved`）。所以 Python 的"一个模块装多个函数"在 MATLAB 里
变成了"一个函数一个文件"。也正因为如此，**不需要 import**——同一文件夹里的函数互相可见。

## 2. 与 Python 的七个差异（本课核心）

### 2.1 下标：0 基 vs 1 基（本项目选 0 基，是刻意的）

MATLAB 惯例是 1 基：`ink(1,1)` 是左上角。但移植版**内部一律 0 基**，只有
`is_open.m` 一处做 `ink(r+1, c+1)` 换算（见 `docs/adr/0001`，别"顺手修"）。

为什么？专利用 `x°=0` 定义左缘起点，Python 测试全部 0 基，交点 `(64,90)`、`row≈95`
这些数字两边必须逐位一致才好对照。**移植第一课：坐标约定先定死一处，全程序统一。**

### 2.2 函数文件 vs 脚本文件

- `drop_improved.m` 这类是**函数文件**：第一行 `function ... end`，靠返回值干活；
- `demo_segment.m` 这类是**脚本**：没有函数头，直接运行；脚本末尾可以放函数
  （R2016b 起支持，`run_real.m` 的 `load_ink` 就是这么放的）。

### 2.3 默认参数：`arguments` 块

```matlab
function res = drop_improved(ink, r0, c0, g, max_steps, terminate_at, rng)
    arguments
        ink logical
        r0 (1,1) double
        g (1,2) double
        max_steps = []      % 注意：不能写 (1,1) double = []，空值不能配尺寸校验
        terminate_at = []
        rng = []
    end
```

对照 Python 的 `max_steps=None`。**踩过的坑**：`(1,1) double = []` 直接报
"默认值无效。值必须为标量"——去掉尺寸校验、只留 `= []` 即可。

### 2.4 返回结构体 vs 元组/字典

```python
# Python
res['melt'];  ('move', nr, nc, k, s)
```
```matlab
% MATLAB
res.melt;     out.act; out.r; out.c; out.k; out.s
```

`_step_patent` 的三种返回动作在 MATLAB 里是同一个结构体 + `act` 字段标记
（`'move'/'reflow'/'melt'`），用 `strcmp(out.act, 'melt')` 判断。

### 2.5 随机数：机制相同，序列不同

```python
rng = np.random.default_rng(seed)      # Python
k = int(rng.choice([-1, 1]))
```
```matlab
rng(seed);                              % MATLAB
pick = @() 2 * randi([0 1]) - 1;
```

两边都是"固定种子 → 可复现"，但**序列不同**：真实谱字里 S102 选出的 k 可能不同，
所以 l2 路径长可能差几步（比如 102 vs 112），指标数值仍完全一致。
合成图不受影响——两刀走的是干净走廊，从不触发随机取向。

### 2.6 图像读写与显示

```matlab
img8 = double(~ink) * 255;                % 墨=0(黑) 空白=255(白)
imagesc(img8); colormap(gray); axis image; axis off;
plot(l1(:,2) + 1, l1(:,1) + 1, 'r-', 'LineWidth', 3);   % x=列, y=行；0 基 +1
print(gcf, fullfile(out, 'overlay'), '-dpng');          % 存 PNG（自动补扩展名）
imwrite(uint8(img8), 'xxx.png');                        % 直接存
```

- Python 用 `Image.save()`，MATLAB 用 `imwrite`/`print -dpng`；
- `imshow` 需要图像工具箱，改用 `imagesc + colormap(gray)` 也是标准做法；
- **灰度坑**：`imread` 读到灰度 PNG 只有 2D（无第 3 通道），`a(:,:,3)` 直接越界。
  Python 的 `convert('RGB')` 会自动补通道，MATLAB 要手动补（`run_real.m` 的 `load_ink`）。

### 2.7 中文与编码

- `.m` 文件统一加 **UTF-8 BOM**（防止中文 Windows 下按 GBK 误读注释）；
- MATLAB 控制台打印 `✓/✗` 会变成 `?`——换成 ASCII 的 `OK/NO`；
- 文件名里的中文没问题（`overlay_无粘连.png` 正常生成，Windows 文件系统存的是 Unicode）。

## 3. 动手清单（20 分钟）

```bash
# 一次性跑完全部校验（脚本名不加 .m）
"D:\Downloads\MATLAB R2024b\bin\matlab.exe" -batch "cd('D:/Study/算法学习/MATLAB'); test_patent; test; demo_segment; run_real"
```

1. **对图**：打开 `MATLAB/output/overlay_粘连.png`，数格子验证红线下移 64 格、绿线右移 90 格，
   与 Python 版交点 `(64,90)` 一致；
2. **对代码**：并排打开 `drop_improved.m` 与 `improved_droplet.py`，找到三处一一对应的逻辑：
   ① 遇阻随机取向段；② do_record vs `_record`（注意偏移判定 `[nr-r1, nc-c1] ~= g`）；
   ③ `visited` 兜底熔断段；
3. **做实验**：把 `theta_o.m` 里 `k==1` 分支的 `(-1)^j` 改成 `(-1)^(j+1)` 藏一个 bug，
   跑 `test_patent`——看哪几条 FAIL、为什么（体会"逐格校验"的价值），改回来。

## 4. 自查（先做，答案在文末）

- Q1：为什么 MATLAB 版交点打印还是 `(64,90)`，而不是 `(65,91)`？
- Q2：`test_patent.m` 里 `make5` 写格子时 `NB(j,1)+1`，但调用 `step_patent` 时滴点传
  `(2,2)` 不加 1——为什么两处不一样？（提示：`is_open` 内部做了什么？）
- Q3：把 `bidirectional_segment` 的 `seed` 改成别的数，合成图结果变不变？真实谱字呢？

---

**自查答案**：
1. 打印前所有坐标都是 0 基，0 基的 (64,90) 对应 MATLAB 数组下标 (65,91)——显示层就是
   0 基约定，全项目一致（ADR-0001）。
2. `make5` 直接写数组（真下标，必须 +1）；`step_patent`/`q_decision` 只做"逻辑坐标"
   判断，+1 换算统一收在 `is_open.m`——**换算只在一个地方，是这次移植最重要的设计**。
3. 合成图不变：两刀路径上没有任何浅坑，`k` 恒为 0，随机源根本没被用到；真实谱字变：
   l2 会选中不同的 `k`，路径和交点可能微变（各自固定种子仍可复现）。
