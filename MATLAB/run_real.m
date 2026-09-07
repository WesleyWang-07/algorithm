% 真实谱字验证：用论文《HUNNUThesis》里的真实手写减字谱字"谱字A(=大/七/勾)"
% 跑双向切分，并与论文公开的"切分结果"（图3-24 的三个部件：大、七、勾）做 IoU 校验。
% 对应 Python 版 run_real.py；运行: run_real
% 注意：依赖 ../文献/glyphs/ 下提取的嵌入图，结论详见 ../专利滴水算法实现/验证报告.md。

GLYPHS = fullfile('..', '文献', 'glyphs');
OUT = 'output_real';
if ~exist(OUT, 'dir')
    mkdir(OUT);
end

full = load_ink(fullfile(GLYPHS, 'p49_img4.png'));    % 完整谱字A（剔除红线）
[H, W] = size(full);
fprintf('[真实谱字A] 尺寸 %dx%d  ink占比 %.3f\n', W, H, mean(full(:)));
imwrite(uint8(double(~full) * 255), fullfile(OUT, 'real_char_clean.png'));

res = bidirectional_segment(full, 'D');
l1 = res.l1_path; l2 = res.l2_path;
xi = res.intersect(1); yi = res.intersect(2);
fprintf('  最优初始滴点 l1=(%d, 0) l2=(0, %d)\n', res.start1(1), res.start2(2));
fprintf('  指标 l1(A/B/C/D): %d/%d/%d/%d\n', ...
    res.metrics1.A, res.metrics1.B, res.metrics1.C, res.metrics1.D);
fprintf('  指标 l2(A/B/C/D): %d/%d/%d/%d\n', ...
    res.metrics2.A, res.metrics2.B, res.metrics2.C, res.metrics2.D);
fprintf('  两路径交点(切分锚点) = (r=%d, c=%d)  l1长%d l2长%d\n', ...
    xi, yi, size(l1, 1), size(l2, 1));

% 叠加可视化（红 l1 / 绿 l2）
img8 = double(~full) * 255;
f = figure('Visible', 'off');
imagesc(img8); colormap(gray); axis image; axis off; hold on;
plot(l1(:, 2) + 1, l1(:, 1) + 1, 'r-', 'LineWidth', 3);
plot(l2(:, 2) + 1, l2(:, 1) + 1, 'g-', 'LineWidth', 3);
print(gcf, fullfile(OUT, 'real_overlay'), '-dpng');
close(f);
imwrite(uint8(double(~res.crops.left_top) * 255), fullfile(OUT, 'real_crop_left_top.png'));
imwrite(uint8(double(~res.crops.right_top) * 255), fullfile(OUT, 'real_crop_right_top.png'));
imwrite(uint8(double(~res.crops.bottom) * 255), fullfile(OUT, 'real_crop_bottom.png'));

% ---- 用论文公开的三个部件(大/七/勾)做 IoU 校验 ----
true_parts = struct('bian10', load_ink(fullfile(GLYPHS, 'p49_img1.png')), ...
    'da', load_ink(fullfile(GLYPHS, 'p49_img2.png')), ...
    'qi', load_ink(fullfile(GLYPHS, 'p49_img3.png')));
true_names = {'大', '七', '勾'};
true_inks = {true_parts.da, true_parts.qi, true_parts.bian10};

got = struct('left_top', res.crops.left_top, ...
    'right_top', res.crops.right_top, ...
    'bottom', res.crops.bottom);

fprintf('\n=== IoU 校验（裁剪块 vs 论文真值 大/七/勾） ===\n');
sil_true = cellfun(@norm_sil, true_inks, 'UniformOutput', false);
sil_got = structfun(@norm_sil, got, 'UniformOutput', false);

fprintf('  %-12s', '');
for i = 1:numel(true_names)
    fprintf('%10s', true_names{i});
end
fprintf('\n');

got_names = fieldnames(got);
expect = {'大', '七', '勾'};
ok_all = true;
for i = 1:numel(got_names)
    row = zeros(1, 3);
    for j = 1:3
        row(j) = iou(sil_got.(got_names{i}), sil_true{j});
    end
    [best, best_j] = max(row);
    fprintf('  %-12s', got_names{i});
    fprintf('%10.3f', row);
    fprintf('   -> 匹配 %s\n', true_names{best_j});
    ok = strcmp(true_names{best_j}, expect{i});
    ok_all = ok_all && ok;
    fprintf('  %12s 期望=%s  实际=%s  IoU=%.3f  %s\n', ...
        got_names{i}, expect{i}, true_names{best_j}, best, ...
        tern(ok, 'OK', 'NO'));
end
if ok_all
    fprintf('\n判定：三块子图与真实部件(大/七/勾)一一对应 -> 校验通过 OK\n');
else
    fprintf('\n判定：三块子图与真实部件(大/七/勾)一一对应 -> 部分不匹配 NO\n');
end

function ink = load_ink(path, thresh)
% 读图 -> 逻辑 ink（true=暗色墨迹）。红线因 R 高自然被排除。
% 对应 run_real.py 的 load_ink：PIL 的 convert('RGB') 会把灰度图补成 3 通道，这里等价处理。
if nargin < 2
    thresh = 128;
end
a = double(imread(path));
if ndims(a) == 2
    a = repmat(a, [1, 1, 3]);          % 灰度图 -> 三通道（R=G=B）
elseif size(a, 3) > 3
    a = a(:, :, 1:3);                  % 如有透明通道则丢弃
end
ink = (a(:, :, 1) < thresh) & (a(:, :, 2) < thresh) & (a(:, :, 3) < thresh);
end

function sil = norm_sil(ink, sz)
% 包围盒裁剪 + 最近邻缩放（不含纵横比信息，仅用于粗对齐），对应 run_real.py 的 norm_sil
if nargin < 2
    sz = [48, 48];
end
[ys, xs] = find(ink);
if isempty(ys)
    sil = false(1, 1);
    return;
end
bbox = ink(min(ys):max(ys), min(xs):max(xs));
sil = imresize(double(bbox) * 255, sz, 'nearest') > 127;
end

function v = iou(a, b)
% 交并比。
inter = sum(a(:) & b(:));
union = sum(a(:) | b(:));
if union == 0
    v = 0;
else
    v = inter / union;
end
end

function s = tern(cond, iftrue, iffalse)
if cond
    s = iftrue;
else
    s = iffalse;
end
end
