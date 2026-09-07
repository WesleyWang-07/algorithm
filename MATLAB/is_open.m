function ok = is_open(ink, r, c)
% 坐标 (r,c) 是否"白色可走"。越界按白处理（允许水滴贴边逃逸）。
% 对应 Python: improved_droplet.py 的 is_open。
% 注意：r、c 均为 0 基坐标（与 Python 版一致，见 docs/adr/0001），
% 数组下标换算 +1 只发生在本函数内。
[H, W] = size(ink);
if r < 0 || c < 0 || r >= H || c >= W
    ok = true;
    return;
end
ok = ~ink(r + 1, c + 1);
end
