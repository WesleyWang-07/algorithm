function ink = build_synthetic_character(H, W, connect_top)
% 构造"仿古琴泛音谱字"的二值图：左上部件 + 右上部件 + 下部部件。
% connect_top=true 让左上/右上之间有一条细"笔画粘连"竖线（考验 l2 的熔断能力）。
% 与 segment.py 的 build_synthetic_character 坐标逐一对应（0 基，下标 +1 写入）。
arguments
    H (1,1) double = 160
    W (1,1) double = 220
    connect_top logical = true
end
ink = false(H, W);

% 左上部件：Python blob(20, 58, 22, 90) -> 行 20..57、列 22..89
ink(21:58, 23:90) = true;
% 右上部件：Python blob(20, 58, 132, 198) -> 行 20..57、列 132..197
ink(21:58, 133:198) = true;
% 下部部件：Python blob(92, 138, 28, 192) -> 行 92..137、列 28..191
ink(93:138, 29:192) = true;

if connect_top
    % 左上与右上之间的"粘连"竖线：Python ink[24:58, 108:114] -> 行 24..57、列 108..113
    ink(25:58, 109:114) = true;
end
end
