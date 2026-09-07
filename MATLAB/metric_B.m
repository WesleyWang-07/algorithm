function B = metric_B(res, g)
% 指标 B = |x* − x°|：初始滴点与终点在"垂直重力方向"上的偏移（权利要求 5）。
% 对横向水流 g=[0,1] 取行漂移；对纵向水流 g=[1,0] 取列漂移。
% 对应 Python: improved_droplet.py 的 metric_B。
p = perp_of(g);
B = abs((res.end(1) - res.start(1)) * p(1) + (res.end(2) - res.start(2)) * p(2));
end
