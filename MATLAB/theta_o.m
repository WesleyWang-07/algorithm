function o = theta_o(j, k)
% 方向因子 o_j（专利权利要求 3 / 图3）。
%   k=0（初始）或 j=1（正前方）-> o_j = 1
%   k=1（偏右）-> o_j = (-1)^j（左侧 j=3,5,7 变负）
%   k=-1（偏左）-> o_j = (-1)^(j+1)（右侧 j=2,4,6 变负）
% 对应 Python: improved_droplet.py 的 _theta_j。
if k == 0 || j == 1
    o = 1;
elseif k == 1
    o = (-1) ^ j;
else
    o = (-1) ^ (j + 1);   % k == -1
end
end
