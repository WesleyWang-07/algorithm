% 按专利 图4~图12 逐格校验改进水滴核心（Q值→动作 + 飞溅状态机）。
% 对应 Python 版 test_patent.py；运行: test_patent
%
% 期望输出：10 项断言全部 PASS。

G = [1, 0];        % 竖直向下
R0 = 2; C0 = 2;    % 当前滴点（0 基；5x5 窗口中心，数组下标 +1 后为 (3,3)）

% 图4  Q=7：仅正前方(n1)开 -> 前跳
a = action(make5([1]), 0, 0);
ok(a.act == "move" && a.r == 3 && a.c == 2, 'Q=7 正前方开 -> 向下滴落(前进)', 'move 到 (3,2)');

% 图5  Q=6 (k=1)：前n1黑、前右n2开 -> 前右对角
a = action(make5([2]), 1, 0);
ok(a.act == "move" && a.r == 3 && a.c == 3, 'Q=6 k=1 前右开 -> 右下对角', 'move 到 (3,3)');

% 图6  Q=5 (k=-1)：前n1黑、前左n3开 -> 前左对角
a = action(make5([3]), -1, 0);
ok(a.act == "move" && a.r == 3 && a.c == 1, 'Q=5 k=-1 前左开 -> 左下对角', 'move 到 (3,1)');

% 图7  Q=4 (k=1)：前n1、前右n2黑，右n4开 -> 右侧滑动
a = action(make5([4]), 1, 0);
ok(a.act == "move" && a.r == 2 && a.c == 3, 'Q=4 k=1 右开 -> 向右滑动', 'move 到 (2,3)');

% 图8  Q=3 (k=-1)：前n1、前左n3黑，左n5开 -> 左侧滑动
a = action(make5([5]), -1, 0);
ok(a.act == "move" && a.r == 2 && a.c == 1, 'Q=3 k=-1 左开 -> 向左滑动', 'move 到 (2,1)');

% 图9/图10 Q=2/1 浅坑 - 飞溅 (k=1, 上右n6开, s=0) -> s+1 跳到上右
a = action(make5([6, 7]), 1, 0);
ok(a.act == "move" && a.r == 1 && a.c == 3 && a.s == 1, ...
    'Q=2 浅坑 s=0 -> 上右飞溅 s=1', 'move 到 (1,3), s=1');

% 浅坑 - 回流 (s=1, k=1) -> s=3, k=-k, 原位
a = action(make5([6, 7]), 1, 1);
ok(a.act == "reflow" && a.k == -1 && a.s == 3, 'Q=2 浅坑 s=1 -> 回流 k=-1 s=3', 'reflow, k=-k, s=3');

% 浅坑 - 放弃 (s=4) -> 前穿熔断
a = action(make5([6, 7]), 1, 4);
ok(a.act == "melt", 'Q=2 浅坑 s=4 -> 熔断', 'melt');

% 图11 Q=0：全黑 -> 熔断
[j, Q] = q_decision(make5([]), R0, C0, G, 0);
a = step_patent(make5([]), R0, C0, G, 0, 0);
ok(Q == 0 && a.act == "melt" && a.r == 3 && a.c == 2, 'Q=0 全黑 -> 熔断(向下穿)', 'melt 到 (3,2)');

% 图12 Q<0 (k=1)：仅左侧白 -> 回流 k=-k
a = action(make5([5, 3, 7]), 1, 0);
ok(a.act == "reflow" && a.k == -1, 'Q<0 k=1 仅左开 -> 回流 k=-1', 'reflow k=-1');

fprintf('\n校验完成。\n');

function a = action(ink, k, s)
% 与 Python test_patent.py 的 action 等价。
a = step_patent(ink, 2, 2, [1, 0], k, s);
end

function ink = make5(open_cells)
% 构造 5x5 墨迹窗口：仅 open_cells 集合中的邻点为白(可走)，其余 7 个邻点为黑。
ink = false(5, 5);
NB = [3, 2; 3, 3; 3, 1; 2, 3; 2, 1; 1, 3; 1, 1];   % j=1..7 的 0 基邻点坐标
for j = 1:7
    if ~ismember(j, open_cells)
        ink(NB(j, 1) + 1, NB(j, 2) + 1) = true;
    end
end
end

function ok(cond, label, want)
if cond
    fprintf('  PASS  %s\n', label);
else
    fprintf('  FAIL  %s\n', label);
    fprintf('       期望: %s\n', want);
end
end
