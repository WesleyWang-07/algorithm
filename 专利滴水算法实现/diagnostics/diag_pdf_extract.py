# -*- coding: utf-8 -*-
"""
高清导出论文关键页：p47/p48（图3-22 / 图3-23 / 图3-25），并抽取页内嵌入图。
目的：量准 0.524 的度量口径。
"""
import os
import pymupdf

PDF = os.path.join(os.path.dirname(__file__), '..', '..', '文献', 'HUNNUThesis.pdf')
OUT = os.path.join(os.path.dirname(__file__), 'out', 'thesis')


def main():
    os.makedirs(OUT, exist_ok=True)
    doc = pymupdf.open(PDF)

    for pno in (37, 46, 47, 48):
        page = doc[pno]
        # 整页高清渲染
        pix = page.get_pixmap(matrix=pymupdf.Matrix(2.5, 2.5))
        p = os.path.join(OUT, f'page_{pno:02d}.png')
        pix.save(p)
        print(f'p{pno}: 渲染 -> {p}  ({pix.width}x{pix.height})')

        # 页内嵌入图
        imgs = page.get_images(full=True)
        print(f'  嵌入图 {len(imgs)} 张:')
        for i, im in enumerate(imgs):
            xref = im[0]
            try:
                info = doc.extract_image(xref)
                ext = info['ext']
                data = info['image']
                w, h = info.get('width'), info.get('height')
                fn = os.path.join(OUT, f'p{pno:02d}_img{i}_{w}x{h}.{ext}')
                with open(fn, 'wb') as f:
                    f.write(data)
                print(f'    img{i}: xref={xref} {w}x{h} {ext} -> {fn}')
            except Exception as e:
                print(f'    img{i}: 提取失败 {e}')

        # 页内文本（含图注）
        t = page.get_text()
        keep = [ln.strip() for ln in t.split('\n')
                if '图3-2' in ln or '表3-' in ln or 'x' in ln and '=' in ln]
        print(f'  相关文本行: {keep[:15]}')
        print()


if __name__ == '__main__':
    main()
