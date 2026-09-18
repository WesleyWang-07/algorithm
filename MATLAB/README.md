# 专利滴水算法 —— MATLAB 实现

依据发明专利《**基于水滴双向飞溅的滴水路径优化**》（申请号 20241016-发明）与湖南师大硕士论文
《基于深度学习的古琴减字谱泛音段机器识读方法研究》第三章，把 Python 版
（`../专利滴水算法实现/`）**逐行等价移植**到 MATLAB：坐标约定（0 基）、决策表（图4~图12）、
四指标、双向切分流程全部一致，合成图结果与 Python 版**逐位相同**。

> 0 基坐标是刻意的（详见 `docs/adr/0001`），勿"顺手"改成 1 基。
> 术语表见 `CONTEXT.md`。

## ✅ 与 Python 版的差异：**零**（2026-09-18 已实跑结案）

| 核对项 | Python（`../专利滴水算法实现/`） | MATLAB（本目录） | 结论 |
|---|---|---|---|
| 函数签名 | `bidirectional_segment(ink, metric='D', metric2='B', seed=None)` | 同（`seed=[]`） | 一致 |
| 默认指标 | `metric='D'` / `metric2='B'` | 同 | 一致 |
| 随机源结构 | `make_rng(pos)` 每个候选独立种子 | 同 | 一致 |
| 规则层对照 | `drop_improved` | `drop_improved.m` 自述"逐行等价" | 一致 |
| **真实谱字A 实跑** | `l1=(95,0) 长150`、`l2=(0,46) 长102`、**锚点 (96,46)**、`m1=5/1/3/9`、`m2=12/0/10/22` | **完全相同** | **逐位一致 ✅** |

> **历史沿革（存误，勿再翻案）**：2026-09-17 曾把锚点行号从 `96` "更正"为 `92`——**方向搞反了**。
> `92` 系列数字的唯一来源是**读图口径错误**：`convert('L') < 128` 会把 `p49_img4.png`
> **图内烤着的论文红线**（纯红 `(255,0,0)`，`L≈76 < 128`）当成墨迹，使 l₁ 贴到 row 92。
> 正确口径是 **RGB 逐通道 `< 128`**（Python `run_real.load_ink` / MATLAB `run_real.m` 的 `load_ink`），
> l₁ 落在 rows 94–96、起点 `(95,0)`。**`96/150/102` 才是对的，`92/149/98` 是错的。**
> 详见 `../专利滴水算法实现/diagnostics/README.md` 的「输入口径陷阱」一节。

> 保留 MATLAB 这份**独立实现**是有意的：两套独立代码对同一算法给出相同的数字，
> 才能证明移植没写错。所以**不要为了"跟上 Python"而改动算法行为**——
> 若将来 Python 侧真的改了算法，应先在 MATLAB 侧还原旧行为并记录，再同步。

## 文件清单（Python ↔ MATLAB 对照表）

| 概念 | Python（`../专利滴水算法实现/`） | MATLAB（本目录） |
| --- | --- | --- |
| 白色可走判定 | `improved_droplet.py` `is_open` | `is_open.m` |
| 垂直右侧方向 | `improved_droplet.py` `perp_of` | `perp_of.m` |
| 方向因子 `o_j` | `improved_droplet.py` `_theta_j` | `theta_o.m` |
| 7 邻点位移表 | `improved_droplet.py` `_neighbors` | `neighbors.m` |
| 势能 `Q_i=max(z·g·o)` | `improved_droplet.py` `_q_decision` | `q_decision.m` |
| 单步决策状态机(+k,+s) | `improved_droplet.py` `_step_patent` | `step_patent.m` |
| 滴水主循环 | `improved_droplet.py` `drop_improved` | `drop_improved.m` |
| 指标 B | `improved_droplet.py` `metric_B` | `metric_B.m` |
| 指标 A/B/C/D | `improved_droplet.py` `path_metrics` | `path_metrics.m` |
| 合成谱字 | `segment.py` `build_synthetic_character` | `build_synthetic_character.m` |
| 双向切分 | `segment.py` `bidirectional_segment` | `bidirectional_segment.m` |
| 演示（红/绿叠加+三子图） | `demo_segment.py` | `demo_segment.m` |
| 真实谱字 IoU 校验 | `run_real.py` | `run_real.m` |
| 专利图4~12 逐格校验 | `test_patent.py` | `test_patent.m` |
| 健壮性测试 | `test.py` | `test.m` |

## 快速运行

交互式：MATLAB 中 `cd` 到本目录，直接输入脚本名回车，例如 `demo_segment`。

命令行批量（脚本名不带 `.m`）：

```bash
"D:\Downloads\MATLAB R2024b\bin\matlab.exe" -batch "cd('D:/Study/算法学习/MATLAB'); test_patent; test; demo_segment; run_real"
```

| 脚本 | 作用 |
| --- | --- |
| `demo_segment` | 合成谱字（粘连/无粘连）双向切分，输出 `output/overlay_*.png` 与三张子图 |
| `run_real` | 论文真实谱字A 校验，输出 `output_real/`，结论见 `../专利滴水算法实现/验证报告.md` |
| `test_patent` | 对照专利图4~图12 逐格断言决策表，期望 11 项全 PASS |
| `test` | 400 组随机图 + 严苛粘连用例（有界/不越界属性断言） |

## 结果对比（MATLAB vs Python）

| 用例 | Python 版 | 本 MATLAB 版 |
| --- | --- | --- |
| 合成谱字交点 / 熔断 | (64,90) / 0,0（两用例） | 逐位相同 |
| 专利逐格校验（图4~图12） | 11/11 PASS | 11 项全 PASS |
| 严苛粘连 | 熔断 2、偏移 7、end(54,60) | 相同 |
| 真实谱字A | l1=(95,0) 长150、l2=(0,46) 长102、锚点 **(96,46)**、m1=5/1/3/9、m2=12/0/10/22 | **实跑逐位一致**：`l1s=95,0 l2s=0,46 m1=5/1/3/9 m2=12/0/10/22 anchor=96,46 l1len=150 l2len=102` |

> 上表"真实谱字A"一行已于 2026-09-18 用 `matlab -batch` 实跑结案，两版**逐位相同**，
> 不存在"终止逻辑差异"。MATLAB 侧 `run_real.m:25` 从 `res.intersect` 动态取值、没有写死数字，
> 所以这个一致是**算出来的**，不是抄来的。
> （该次实跑同时复跑 `test_patent`→11 项全 PASS、`test`→400/400 通过、
> 合成交点 `(64,90)` 熔断 0、严苛粘连 `熔断2/偏移7/end(54,60)`，与 Python 侧一致。）

> 枚举默认确定性（`seed` 留空即关闭 S102 随机取向），两版结果逐位一致、可互相校验；
> 只有显式传入 `seed` 启用随机取向时，两语言各自的随机数序列才可能带来差异。
> 真实谱字 A 的结论（锚点 `(96,46)`；它与论文图3-23 的列 77 不对齐是**预期行为**、
> 不是缺陷）详见 `../专利滴水算法实现/docs/adr/0001-drop-fig3-23-reproduction-goal.md`。

## MATLAB 新手速览

1. **`.m` 文件规则**：一个文件一个主函数，**文件名 = 主函数名**（如 `drop_improved.m` 里第一个
   `function` 就叫 `drop_improved`）；其余同文件函数叫局部函数，只能被本文件调用。脚本文件（如
   `demo_segment.m`）没有主函数，直接就能运行，里面的函数放在文件末尾。
2. **逻辑矩阵**：`true=墨迹、false=空白`（`~ink` 反色、`ink & mask` 取交集）。MATLAB 下标从 1 起，
   本项目为与 Python 结果逐位对齐使用 **0 基坐标**，只有 `is_open.m` 里做 `+1` 换算。
3. **结构体**：`res.path`、`res.metrics1.A`，与 Python 的 `res['path']`、`res['metrics1']['A']` 一一对应。
4. **读/写图**：`imread` / `imwrite`；显示用 `imagesc(x); colormap(gray); axis image off;`（或工具箱 `imshow`）。
5. **批量运行**：`matlab -batch "脚本名"` 不打开桌面窗口；脚本内 `fprintf('%d', x)` 打印数值，
   `disp(...)` 打印文本——`run_real` 的 IoU 校验输出格式与 Python 版逐行对齐。

---

对应任务的背景、算法原理与已知局限，请优先阅读 `../专利滴水算法实现/README.md` 与
`../专利滴水算法实现/验证报告.md`（中文、更详细）。
