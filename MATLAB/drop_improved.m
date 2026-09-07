function res = drop_improved(ink, r0, c0, g, max_steps, terminate_at, rng)
% 按专利规则生成一条滴水路径（与 improved_droplet.py 的 drop_improved 逐行等价）。
%
%   ink          : HxW 逻辑矩阵，true=黑墨迹；坐标均用 0 基（数组下标 +1 见 is_open）
%   r0, c0       : 初始滴点（0 基）
%   g            : 重力方向 [dr, dc]；[1,0] 竖直向下、[0,1] 水平向右
%   max_steps    : 最大步数；缺省为 8*(H+W)+2000
%   terminate_at : 可选 Nx2 坐标矩阵（每行一个点），水滴步入即停（用于 l2 与 l1 交汇）
%   rng          : 可选无参函数句柄，返回 ±1（S102 遇阻随机取向）；缺省则 k 恒为 0
% 返回 res 结构体：path(Nx2, 0 基), melt, offsets, start(1x2), end(1x2), stopped_by
%   stopped_by ∈ {'terminate_at','boundary','max_steps'}
arguments
    ink logical
    r0 (1,1) double
    c0 (1,1) double
    g (1,2) double
    max_steps = []
    terminate_at = []
    rng = []
end
[H, W] = size(ink);
if isempty(max_steps)
    max_steps = 8 * (H + W) + 2000;
end

r = r0; c = c0;
k = 0;                  % 方向位：0 初始, 1 偏右(+p), -1 偏左(-p)
s = 0;                  % 飞溅状态
oriented = false;       % 是否已随机取向
path = [r, c];          % Nx2，每行一个点（reflow 时坐标不变也追加，同 Python）
melt = 0;
offsets = 0;
stopped_by = 'max_steps';

for step_i = 0:max_steps-1
    % terminate_at 判定（Python: step_i > 0，起点命中不终止）
    if ~isempty(terminate_at) && step_i > 0 && any(all(terminate_at == [r, c], 2))
        stopped_by = 'terminate_at';
        break;
    end

    % 遇阻随机取向（S102）：首次遇到浅坑/死路（Q<=0 或胜出邻点为后向 j∈{6,7}）
    % 时才定 k；正常滑行不定取向——与专利图13~15"落点遇阻才取向"一致
    if ~oriented
        [j, Q] = q_decision(ink, r, c, g, k);
        if Q == 0 || Q < 0 || j == 6 || j == 7
            if ~isempty(rng)
                k = rng();              % 对称随机取向 k=±1
            end
            oriented = true;
        end
    end

    out = step_patent(ink, r, c, g, k, s);

    if strcmp(out.act, 'reflow')
        % 原位回流：位置不动，k=-k，s+=2。s 到 4/5 不在这里抢先熔断，
        % 交给 step_patent 的状态机下一步按图4~图12 消化。
        if out.s > 5        % 专利状态表未定义 s>5：回流预算已耗尽，保底熔断
            [r, c, melt, offsets] = do_record(r, c, r+g(1), c+g(2), g, melt, offsets, true);
            s = 0; k = out.k;
        else
            k = out.k; s = out.s;
        end
    elseif strcmp(out.act, 'melt')
        [r, c, melt, offsets] = do_record(r, c, out.r, out.c, g, melt, offsets, true);
        k = out.k; s = out.s;
    else % 'move'
        nr = out.r; nc = out.c;
        if (nr == r && nc == c) || any(all(path == [nr, nc], 2))
            % 兜底：回到原位置或已访问点，强制前穿熔断
            [r, c, melt, offsets] = do_record(r, c, r+g(1), c+g(2), g, melt, offsets, true);
            s = 0;
        else
            [r, c, melt, offsets] = do_record(r, c, nr, nc, g, melt, offsets, false);
            k = out.k; s = out.s;
        end
    end

    path(end+1, :) = [r, c]; %#ok<AGROW>

    if r < 0 || r >= H || c < 0 || c >= W
        stopped_by = 'boundary';
        break;
    end
end

res = struct('path', path, 'melt', melt, 'offsets', offsets, ...
    'start', [r0, c0], 'end', [r, c], 'stopped_by', stopped_by);
end

function [r2, c2, m2, o2] = do_record(r1, c1, nr, nc, g, melt1, offsets1, is_melt)
% 同 Python 的 _record：非重力方向步计入偏移；消融（熔断）步计入熔断量。
if ~isequal([nr - r1, nc - c1], g)
    offsets1 = offsets1 + 1;
end
r2 = nr; c2 = nc;
m2 = melt1 + is_melt;
o2 = offsets1;
end
