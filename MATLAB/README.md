# 专利滴水算法 —— MATLAB 实现

依据发明专利《**基于水滴双向飞溅的滴水路径优化**》（申请号 20241016-发明）与湖南师大硕士论文
《基于深度学习的古琴减字谱泛音段机器识读方法研究》第三章，把 Python 版
（`../专利滴水算法实现/`）**逐行等价移植**到 MATLAB：坐标约定（0 基）、决策表（图4~图12）、
四指标、双向切分流程全部一致，合成图结果与 Python 版**逐位相同**。

> 0 基坐标是刻意的（详见 `docs/adr/0001`），勿"顺手"改成 1 基。
> 术语表见 `CONTEXT.md`。

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
| `test_patent` | 对照专利图4~图12 逐格断言决策表，期望 10 项全 PASS |
| `test` | 400 组随机图 + 严苛粘连用例（有界/不越界属性断言） |

## 结果对比（MATLAB vs Python）

| 用例 | Python 版 | 本 MATLAB 版 |
| --- | --- | --- |
| 合成谱字交点 / 熔断 | (64,90) / 0,0（两用例） | 逐位相同（`demo_segment` 可再次核对） |
| 专利逐格校验 | 10/10 PASS | 10 项全 PASS |
| 严苛粘连 | 熔断 2、偏移 7、end(54,60) | 相同（性质断言） |
| 真实谱字A | l1 行 95、交点 (96,33)（修复后） | 行为等价；**数值允许有差异**：两语言的随机数发生器序列不同，S102 遇阻随机取向选出的 k 可能不同；各自固定种子、各自可复现。整体结论（红线正确、竖切受粘连影响）不变 |

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
