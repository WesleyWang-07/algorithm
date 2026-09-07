% 演示：改进滴水算法的双向切分 + 四指标初始滴点优化
% 对应 Python 版 demo_segment.py；运行: demo_segment
%
% 输出到 ./output/：
%   overlay_无粘连.png / overlay_粘连.png   原始图 + 红色 l1(上下切分) + 绿色 l2(左右切分)
%   crop_left_top_*.png / crop_right_top_*.png / crop_bottom_*.png   三张子图
%   并在终端打印四指标与最优初始滴点。

out = 'output';
if ~exist(out, 'dir')
    mkdir(out);
end

fprintf('%s\n', repmat('=', 1, 70));
fprintf('改进滴水算法 —— 双向切分 + 四指标优化（专利：基于水滴双向飞溅的滴水路径优化）\n');
fprintf('%s\n', repmat('=', 1, 70));

for connect = [true, false]
    if connect
        tag = '粘连';
    else
        tag = '无粘连';
    end
    ink = build_synthetic_character(160, 220, connect);
    [H, W] = size(ink);
    fprintf('\n%s\n[合成谱字] H=%d W=%d  粘连: %s\n', repmat('-', 1, 70), H, W, tag);

    res = bidirectional_segment(ink, 'D');
    l1 = res.l1_path; l2 = res.l2_path;
    xi = res.intersect(1); yi = res.intersect(2);

    fprintf('  最优初始滴点 l1(横向/红色): (%d, 0)   l2(纵向/绿色): (0, %d)\n', ...
        res.start1(1), res.start2(2));
    fprintf('  l1 指标(A/B/C/D): %d/%d/%d/%d\n', ...
        res.metrics1.A, res.metrics1.B, res.metrics1.C, res.metrics1.D);
    fprintf('  l2 指标(A/B/C/D): %d/%d/%d/%d\n', ...
        res.metrics2.A, res.metrics2.B, res.metrics2.C, res.metrics2.D);
    fprintf('  两路径交点(分割锚点): (r=%d, c=%d)   横长 %d 竖长 %d\n', ...
        xi, yi, size(l1, 1), size(l2, 1));

    % ---- 叠加可视化：红 l1 / 绿 l2 ----
    img8 = double(~ink) * 255;          % 墨迹=0(黑), 空白=255(白)
    f = figure('Visible', 'off');
    imagesc(img8); colormap(gray); axis image; axis off; hold on;
    plot(l1(:, 2) + 1, l1(:, 1) + 1, 'r-', 'LineWidth', 3);   % plot(x=列, y=行)；0 基 +1
    plot(l2(:, 2) + 1, l2(:, 1) + 1, 'g-', 'LineWidth', 3);
    print(gcf, fullfile(out, ['overlay_' tag]), '-dpng');
    close(f);

    % ---- 三张子图 ----
    save_crop(@(name, arr) imwrite(uint8(double(arr) * 255), ...
        fullfile(out, ['crop_' name '_' tag '.png'])), res.crops, tag);

    fprintf('  已保存: output/overlay_%s.png 及 3 张 crop_*_%s.png\n', tag, tag);
end

fprintf('\n%s\n完成。可视化请查看 output/ 下的 PNG。\n', repmat('=', 1, 70));

function save_crop(saver, crops, tag) %#ok<DEFNU>
% 把三张子图按 Python 版命名写出：crop_left_top_*.png 等。
names = fieldnames(crops);
for i = 1:numel(names)
    saver(names{i}, crops.(names{i}));
end
end
