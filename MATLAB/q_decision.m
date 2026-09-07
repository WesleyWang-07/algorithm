function [best_j, best_q] = q_decision(ink, r, c, g, k)
% 计算 Q_i = max_j(z_j·g_j·o_j) 与胜出的邻点 j（专利权利要求 2/3、图1~图3）。
% 对应 Python: improved_droplet.py 的 _q_decision。
%
% 语义（专利图4~图12）：
%   · max 只在"白像素(z_j=1)"之间进行；
%   · 8 邻点全黑（无任何白像素）-> Q=0（熔断），best_j=0 表示未胜出；
%   · 有白像素但乘积全为负（仅对侧白）-> Q<0（回流）。
% 权值 g_j = 8-j；黑像素 z=0 不参与比较。
nb = neighbors(g);
g7 = 8 - (1:7);
best_j = 0;
best_q = -Inf;
for j = 1:7
    if ~is_open(ink, r + nb(j, 1), c + nb(j, 2))
        continue;                  % 黑像素 z=0，跳过
    end
    q = g7(j) * theta_o(j, k);
    if q > best_q
        best_q = q;
        best_j = j;
    end
end
if best_j == 0
    best_q = 0;                    % 无任何白像素 -> 全黑（熔断）
end
end
