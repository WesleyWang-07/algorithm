function m = path_metrics(res, g)
% 四种优化指标（权利要求 5）：
%   A = d         熔断像素数（最小化）           res.melt
%   B = |x*−x°|   垂直重力方向上的始末偏移（最小化） metric_B
%   C = v         累计偏移次数（最小化）          res.offsets
%   D = d + B + v 三指标融合（论文/专利结论最优）
% 对应 Python: improved_droplet.py 的 path_metrics。
m.A = res.melt;
m.B = metric_B(res, g);
m.C = res.offsets;
m.D = m.A + m.B + m.C;
end
