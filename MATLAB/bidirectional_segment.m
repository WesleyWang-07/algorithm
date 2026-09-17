function res = bidirectional_segment(ink, metric, metric2, seed)
% 双向切分（与 segment.py 的 bidirectional_segment 等价）：
%   1) l1 水平滴（红色，上下切分）：重力 g=[0,1]，初始滴点行在 δ1∈(2N/5,3N/5) 带内；
%   2) l2 竖直滴（绿色，左右切分）：重力 g=[1,0]，列在 δ2∈(2M/7,3M/5) 带内，碰到 l1 即停；
%   3) 以交点 (xi,yi) 为锚点裁剪出 左上/右上/下部 三张子图。
%
%   metric  : l1 的选优指标 'A'|'B'|'C'|'D'（默认 'D'）
%   metric2 : l2 的选优指标（默认 'B'；依据论文表3-1：粘连谱字只有 B 全部切分正确）
%   seed    : []（默认）-> 枚举确定性（关闭 S102 随机取向，候选之间可比、结果可复现）；
%             整数 -> 每候选独立固定种子（seed+起点坐标）启用随机取向
% 返回 res：l1_path, l2_path（Nx2 0 基坐标）, intersect(1x2), crops(left_top/right_top/
%   bottom), metrics1, metrics2（结构体 A/B/C/D）, start1, start2
arguments
    ink logical
    metric = 'D'
    metric2 = 'B'
    seed = []
end
metric = char(metric);
metric2 = char(metric2);
if ~ismember(metric, {'A', 'B', 'C', 'D'})
    error('metric 必须是 ''A''/''B''/''C''/''D'' 之一，收到 %s', metric);
end
if ~ismember(metric2, {'A', 'B', 'C', 'D'})
    error('metric2 必须是 ''A''/''B''/''C''/''D'' 之一，收到 %s', metric2);
end
use_rng = ~isempty(seed);
pick = @() 2 * randi([0 1], 1) - 1;      % 对称随机取向 k=±1（对应 Python rng.choice([-1,1])）
[H, W] = size(ink);

% ---- 第一次切分 l1：横向（上下切分），起点左缘、行在中间带 ----
% 论文: 上下切分初始滴点 δ1 ∈ (2/5 N, 3/5 N)  （range() 右开区间 -> MATLAB 终点 -1）
n1 = round(0.4 * H); n2 = round(0.6 * H);
r_span = max(1, n1) : (min(H - 1, n2) - 1);
g1 = [0, 1];
bestScore1 = Inf; bestRes1 = []; bestStart1 = [];
for r0 = r_span
    if ~is_open(ink, r0, 0)
        continue;
    end
    res = drop_improved(ink, r0, 0, g1, [], [], make_rng(r0));
    m = path_metrics(res, g1);
    score = m.(metric);
    if score < bestScore1
        bestScore1 = score; bestRes1 = res; bestStart1 = r0;
    end
end
if isempty(bestRes1)
    % 中间带入口全被墨迹挡住（黑边框/污渍）：回退带中点强制起步
    if isempty(r_span)
        r0_best = floor(H / 2);
    else
        r0_best = floor((r_span(1) + r_span(end)) / 2);
    end
    bestRes1 = drop_improved(ink, r0_best, 0, g1, [], [], make_rng(r0_best));
else
    r0_best = bestStart1;
end
l1_path = bestRes1.path;
m1 = path_metrics(bestRes1, g1);

% ---- 第二次切分 l2：纵向（左右切分），起点上缘、列在中间带 ----
% 论文: 左右切分初始滴点 δ2 ∈ (2/7 M, 3/5 M)
w1 = round(2 / 7 * W); w2 = round(3 / 5 * W);
c_span = max(1, w1) : (min(W - 1, w2) - 1);
g2 = [1, 0];
bestScore2 = Inf; bestRes2 = []; bestStart2 = [];
for c0 = c_span
    if ~is_open(ink, 0, c0)
        continue;
    end
    res = drop_improved(ink, 0, c0, g2, [], l1_path, make_rng(c0));
    m = path_metrics(res, g2);
    score = m.(metric2);
    if score < bestScore2
        bestScore2 = score; bestRes2 = res; bestStart2 = c0;
    end
end
if isempty(bestRes2)
    if isempty(c_span)
        c0_best = floor(W / 2);
    else
        c0_best = floor((c_span(1) + c_span(end)) / 2);
    end
    bestRes2 = drop_improved(ink, 0, c0_best, g2, [], l1_path, make_rng(c0_best));
else
    c0_best = bestStart2;
end
l2_path = bestRes2.path;
m2 = path_metrics(bestRes2, g2);

% ---- 依据交点裁剪三张子图 ----
if strcmp(bestRes2.stopped_by, 'terminate_at')
    xi = l2_path(end, 1); yi = l2_path(end, 2);
else
    % 没碰到 l1：用 l2 落到底部的那一点
    xi = bestRes2.end(1); yi = bestRes2.end(2);
end
xi = min(max(xi, 0), H - 1);
yi = min(max(yi, 0), W - 1);
crops.left_top = ink(1:xi, 1:yi);            % Python ink[0:xi, 0:yi]
crops.right_top = ink(1:xi, yi+1:W);         % Python ink[0:xi, yi:W]
crops.bottom = ink(xi+1:H, 1:W);             % Python ink[xi:H, 0:W]

res = struct('l1_path', l1_path, 'l2_path', l2_path, ...
    'intersect', [xi, yi], 'crops', crops, ...
    'metrics1', m1, 'metrics2', m2, ...
    'start1', [r0_best, 0], 'start2', [0, c0_best]);

    function p = make_rng(pos)
        % seed=[] -> 确定性枚举（不取向）；否则该候选的独立固定随机源
        if use_rng
            rng(seed + pos);
            p = pick;
        else
            p = [];
        end
    end
end
