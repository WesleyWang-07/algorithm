function out = step_patent(ink, r, c, g, k, s)
% 单步滴水规则（专利图4~图12 的决策表）：Q 值 -> 动作 + 飞溅状态机。
% 对应 Python: improved_droplet.py 的 _step_patent。
% 返回 out: act ∈ {'move','reflow','melt'}; r,c（0 基，reflow 时坐标不变）;
%          k,s（下一次决策使用的状态）。
[j, Q] = q_decision(ink, r, c, g, k);
nb = neighbors(g);

if Q == 0                                  % 全黑包围 -> 熔断
    out = struct('act','melt', 'r', r+g(1), 'c', c+g(2), 'k', k, 's', 0);
    return;
end
if Q < 0                                   % 仅对侧白 -> 回流
    out = struct('act','reflow', 'r', r, 'c', c, 'k', -k, 's', s+2);
    return;
end

if j == 1                                  % Q=7 正前方滴落
    out = struct('act','move', 'r', r+g(1), 'c', c+g(2), 'k', k, 's', 0);
elseif j == 2 || j == 3                    % Q=6/5 前对角滴落
    if s == 1 || s == 3
        s2 = s - 1;
    elseif s == 2
        s2 = 0;
    else
        s2 = s;
    end
    out = struct('act','move', 'r', r+nb(j,1), 'c', c+nb(j,2), 'k', k, 's', s2);
elseif j == 4 || j == 5                    % Q=4/3 水平滑动
    if s == 4 || s == 5                    % 状态机超时：改为前跳（图7a/图8a）
        out = struct('act','move', 'r', r+g(1), 'c', c+g(2), 'k', k, 's', 0);
    else
        out = struct('act','move', 'r', r+nb(j,1), 'c', c+nb(j,2), 'k', k, 's', s);
    end
else                                       % j∈{6,7}：浅坑 Q=2/1
    if s == 0 || s == 2                    % 飞溅：跳向后(-g)对角
        out = struct('act','move', 'r', r+nb(j,1), 'c', c+nb(j,2), 'k', k, 's', s+1);
    elseif s == 1 || s == 3                % 回流
        out = struct('act','reflow', 'r', r, 'c', c, 'k', -k, 's', s+2);
    else                                   % s∈{4,5}：放弃，前穿熔断
        out = struct('act','melt', 'r', r+g(1), 'c', c+g(2), 'k', k, 's', 0);
    end
end
end
