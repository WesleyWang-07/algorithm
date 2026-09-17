# 专利滴水算法 —— MATLAB 实现

依据发明专利《**基于水滴双向飞溅的滴水路径优化**》（申请号 20241016-发明）与湖南师大硕士论文
《基于深度学习的古琴减字谱泛音段机器识读方法研究》第三章，把 Python 版
（`../专利滴水算法实现/`）**逐行等价移植**到 MATLAB：坐标约定（0 基）、决策表（图4~图12）、
四指标、双向切分流程全部一致，合成图结果与 Python 版**逐位相同**。

> 0 基坐标是刻意的（详见 `docs/adr/0001`），勿"顺手"改成 1 基。
> 术语表见 `CONTEXT.md`。

## ⚠️ 与 Python 版的两处已知差异（2026-09-17）

**代码层面：无差异。** `bidirectional_segment.m` 的签名与默认值已与 Python 版一致
（`metric='D'` / `metric2='B'` / `seed=[]`），`make_rng(pos)` 的独立种子结构也一致。

**文档与结论层面：有一处差异需知道。** Python 版在 2026-09-17 完成了一轮"目标证伪"研究
（`../专利滴水算法实现/验证报告.md` 4.7 节），结论是**"复现论文图3-23 的 0.524"这个目标
本身不成立**——论文那条 l₂ 不是"改进滴水算法在 δ₂ 带内枚举选优"的产物。
因此：

- 下方"结果对比"表中"真实谱字A"一行的 **Python 侧数字已更正为锚点 `(92,46)`**
  （此前文档写 96 是错的），MATLAB 侧若仍打印 96 或别的行号，请以 Python 侧新口径为准核对；
- MATLAB 侧 `run_real.m` 的控制台输出**尚未按新口径复核**，如需对齐请重跑一次
  `matlab -batch "run_real"` 并比对。

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
| `test_patent` | 对照专利图4~图12 逐格断言决策表，期望 10 项全 PASS |
| `test` | 400 组随机图 + 严苛粘连用例（有界/不越界属性断言） |

## 结果对比（MATLAB vs Python）

| 用例 | Python 版 | 本 MATLAB 版 |
| --- | --- | --- |
| 合成谱字交点 / 熔断 | (64,90) / 0,0（两用例） | 逐位相同 |
| 专利逐格校验（图4~图12） | 11/11 PASS | 11 项全 PASS |
| 严苛粘连 | 熔断 2、偏移 7、end(54,60) | 相同 |
| 真实谱字A | l1=(92,0) 长149、l2=(0,46) 长98、锚点 **(92,46)**、l2 指标 12/0/10/22 | 代码同构，**输出由 `res.intersect` 动态打印**，应与 Python 一致（此前记录的 `96`/`l1长150`/`l2长102` 是 Python 侧旧口径，已更正为 92/149/98） |

> 上表"真实谱字A"一行：Python 侧 2026-09-17 三次复核已把锚点行号从 `96` 更正为 `92`
> （96 既不是带 `terminate_at` 的 92、也不是不带终止条件的 185）。
> MATLAB 侧 `run_real.m` 第 25 行是从 `res.intersect` 取值打印的、没有写死数字，
> 故重跑 `matlab -batch "run_real"` 应输出 92；**若输出的是 96，说明 MATLAB 侧的
> `drop_improved.m` 终止逻辑与 Python 有实质差异，那是真问题，需要排查**（不属本次文档更正范围）。

> 枚举默认确定性（`seed` 留空即关闭 S102 随机取向），两版结果逐位一致、可互相校验；
> 只有显式传入 `seed` 启用随机取向时，两语言各自的随机数序列才可能带来差异。
> 真实谱字 A 的结论（红线正确、竖切锚点尚未到达论文真值）详见
> `../专利滴水算法实现/验证报告.md` 的"阶段三更新"一节。

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
