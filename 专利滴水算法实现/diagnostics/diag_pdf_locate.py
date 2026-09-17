# -*- coding: utf-8 -*-
"""
从 HUNNUThesis.pdf 提取 图3-23 所在页，高清渲染 + 列出页内嵌入图，
以便量准 0.524 的度量口径（分子分母取什么基准）。
"""
import os
import pymupdf

PDF = os.path.join(os.path.dirname(__file__), '..', '..', '文献', 'HUNNUThesis.pdf')
OUT = os.path.join(os.path.dirname(__file__), 'out', 'thesis')


def main():
    os.makedirs(OUT, exist_ok=True)
    doc = pymupdf.open(PDF)
    print(f'总页数 = {doc.page_count}')

    # 搜索"图3-23" / "图3‑23"（注意可能用不同连字符）
    for kw in ['图3-23', '图3‑23', '图3–23', '图 3-23', '图3-25', '表3-1']:
        hits = []
        for i in range(doc.page_count):
            txt = doc[i].get_text()
            if kw in txt:
                hits.append(i)
        print(f'  搜索 "{kw}" -> 页 {hits}')

    # 输出每页的第一行文本，快速定位章节
    print('\n各页开头文本（用于定位第3章）：')
    for i in range(doc.page_count):
        t = doc[i].get_text().strip().replace('\n', ' | ')
        if not t:
            continue
        head = t[:100]
        print(f'  p{i:>3}: {head}')


if __name__ == '__main__':
    main()
