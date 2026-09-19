# -*- coding: utf-8 -*-
"""
抽取论文表3-3 / 表3-4 的示例谱字与四指标切分结果（只读 PDF，写到文献/glyphs/table33_34/）
=====================================================================================

为什么需要这个
--------------
`文献/论文.md` 是**精简转写版**：3.4.1~3.4.5 正文、表3-1、表3-3、表3-4 全部没收录。
论文真正的实验规模与逐字结果只存在于 PDF 里，必须直读。

已核实的版面（`pymupdf`，密码 'stt'）
------------------------------------
每行 5 格，x 固定为 145.2 / 212.5 / 286.8 / 360.7 / 435.0：

    第1格 = 谱字图像（干净字形，无彩线）      ← 可作算法输入
    第2~5格 = 指标 A / B / C / D 的切分结果    ← 只能用来【读参考线】，不能当输入

    PDF页(0基)  书页  行数  归属
      54         55    8    表3-3 编号 1~8
      55         56    3    表3-3 编号 9~10（前两行）+ 表3-4 编号 1（第三行）
      56         57    4    表3-4 编号 2~5
    → 表3-3 共 10 字、表3-4 共 5 字，合计 15 字 / 75 格。

⚠️ 输入污染红线
--------------
第2~5格上画着论文自己的切分线（红/绿）。实测绿线覆盖了 16% 的压墨像素，
**在列方向把墨迹挖出缺口**（`p48_img0` 比 `p49_img4` 在 col 62–64/76–78 少 2–7 个墨迹像素），
足以把本实现的锚点从 col 46 撬到 col 76。**这些格子永远不能当算法输入。**
第1格（谱字图像）是干净字形，本脚本会逐格断言其中**不含彩色像素**。

运行：cd 专利滴水算法实现/diagnostics && python diag_extract_tables.py
输出：../../文献/glyphs/table33_34/{tab33_r01_glyph.png, tab33_r01_A.png, ...}
"""
import os
import numpy as np
import pymupdf
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
PDF = os.path.join(ROOT, '文献', 'HUNNUThesis.pdf')
OUT = os.path.join(ROOT, '文献', 'glyphs', 'table33_34')
PASSWORD = 'stt'
DPI = 300

# 论文中每张表在 PDF 里的行（(页 0基, 行号 y 容差) -> 表名+编号）
PAGES = {
    54: [('tab33', 1), ('tab33', 2), ('tab33', 3), ('tab33', 4),
         ('tab33', 5), ('tab33', 6), ('tab33', 7), ('tab33', 8)],
    55: [('tab33', 9), ('tab33', 10), ('tab34', 1)],
    56: [('tab34', 2), ('tab34', 3), ('tab34', 4), ('tab34', 5)],
}
COLS = ['glyph', 'A', 'B', 'C', 'D']


def cluster(vals, tol=12.0):
    """把近似相等的坐标聚成一类，返回聚类中心（升序）。同行的各格 y 会差几个点。"""
    out = []
    for v in sorted(vals):
        if out and abs(v - out[-1][-1]) <= tol:
            out[-1].append(v)
        else:
            out.append([v])
    return [sum(g) / len(g) for g in out]


def cell_bboxes(page):
    """把该页的图片按 (行 y, 列 x) 归位，返回 [[bbox×5], ...]（每行 5 格）。"""
    infos = page.get_image_info(xrefs=True)
    xs = cluster([inf['bbox'][0] for inf in infos], tol=20.0)
    ys = cluster([inf['bbox'][1] for inf in infos])
    grid = [[None] * len(xs) for _ in ys]
    for inf in infos:
        b = inf['bbox']
        ci = min(range(len(xs)), key=lambda i: abs(xs[i] - b[0]))
        ri = min(range(len(ys)), key=lambda i: abs(ys[i] - b[1]))
        assert grid[ri][ci] is None, f'格子冲突 r{ri} c{ci}'
        grid[ri][ci] = b
    return [row for row in grid if all(row)]


def render(page, bbox):
    pix = page.get_pixmap(clip=pymupdf.Rect(*bbox), dpi=DPI)
    return np.frombuffer(pix.samples, dtype=np.uint8).reshape(
        pix.height, pix.width, pix.n)[:, :, :3].copy()


def main():
    os.makedirs(OUT, exist_ok=True)
    doc = pymupdf.open(PDF)
    auth = doc.authenticate(PASSWORD)
    print(f'[pdf] {os.path.basename(PDF)}  {doc.page_count} 页  auth={auth} '
          f'(2=owner/1=user/0=失败)')
    assert auth, 'PDF 密码错误'

    n_written = 0
    dirty = []
    for pi, rows in PAGES.items():
        page = doc[pi]
        grid = cell_bboxes(page)
        assert len(grid) == len(rows), \
            f'页 {pi} 期望 {len(rows)} 行，实测 {len(grid)} 行'
        print(f'\n[page {pi}] 书页 {pi + 1}  {len(grid)} 行 × 5 列')
        for (tbl, idx), row in zip(rows, grid):
            for col, bbox in zip(COLS, row):
                arr = render(page, bbox)
                name = f'{tbl}_r{idx:02d}_{col}.png'
                Image.fromarray(arr).save(os.path.join(OUT, name))
                n_written += 1
                if col == 'glyph':
                    # 断言：干净字形里不应有彩色像素（红/绿/蓝标注）
                    a = arr.astype(int)
                    mx, mn = a.max(axis=2), a.min(axis=2)
                    chroma = int(((mx - mn) > 60).sum())
                    if chroma:
                        dirty.append((name, chroma))
                    print(f'   {tbl} #{idx:<2d} glyph {arr.shape[1]}x{arr.shape[0]} '
                          f'彩色像素={chroma} {"✓" if chroma == 0 else "✗ 不干净!"}')

    print(f'\n[OK] 写出 {n_written} 个 PNG -> {OUT}')
    if dirty:
        print('[!!] 以下"干净字形"格含彩色像素，不能直接当输入：')
        for n, c in dirty:
            print(f'     {n}  彩色像素={c}')
    else:
        print('[OK] 15 个谱字图像格全部无彩色像素，可作算法输入。')


if __name__ == '__main__':
    main()
