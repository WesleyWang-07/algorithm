function p = perp_of(g)
% 重力方向 g 的垂直右侧方向（专利 y 轴，相对于重力右侧）。
% 对应 Python: improved_droplet.py 的 perp_of。
p = [g(2), g(1)];
end
