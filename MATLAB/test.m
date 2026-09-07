% 健壮性测试：改进滴水算法在任意二值图上应有限、有界、不越界、不死循环。
% 对应 Python 版 test.py；运行: test
% 注意：MATLAB 与 Python 的随机数序列不同，本测试只断言"性质"（有界/不越界），不断言具体路径。

disp('=== 1) 随机模糊测试 ===');
rng(7); % 确定性会话（序列与 Python 不同，性质断言不受影响）
for t = 1:400
    H = randi([8, 90], 1, 1);
    W = randi([8, 90], 1, 1);
    ink = rand(H, W) < (0.1 + 0.6 * rand());
    for gi = 1:2
        if gi == 1
            g = [1, 0];
        else
            g = [0, 1];
        end
        for q = 1:6
            rr = randi([0, H - 1], 1, 1);
            cc = randi([0, W - 1], 1, 1);
            if ink(rr + 1, cc + 1)
                continue;
            end
            res = drop_improved(ink, rr, cc, g);
            % 断言：熔断、偏移有限且不超过最大步数
            assert(res.melt + res.offsets < 10000, '步数爆炸');
            % 断言：轨迹上每个点（除终点）都在界内
            for p = 1:size(res.path, 1) - 1
                rp = res.path(p, 1);
                cp = res.path(p, 2);
                assert(rp >= 0 && rp < H && cp >= 0 && cp < W, '路径越界');
            end
        end
    end
    if mod(t, 100) == 0
        fprintf('  ... 随机测试 %d/400\n', t);
    end
end
fprintf('  OK: 400 组随机图全部通过（无死循环/越界/指数爆炸）\n');

disp('=== 2) 演示 & 严苛用例 ===');
for connect = [true, false]
    ink = build_synthetic_character(160, 220, connect);
    res = bidirectional_segment(ink, 'D');
    assert(res.intersect(1) > 0);
    fprintf('  合成谱字(粘连=%d): 交点=(%d, %d) l1熔断=%d l2熔断=%d\n', ...
        connect, res.intersect(1), res.intersect(2), res.metrics1.A, res.metrics2.A);
end

% 严苛：上下墨迹完全相连（Python 版 ink[10:45,10:50]=[55:90,10:50] 及 1px 粘连线）
ink = false(100, 60);
ink(11:45, 11:50) = true;
ink(56:90, 11:50) = true;
ink(46:55, 30:31) = true;
left = drop_improved(ink, 47, 0, [0, 1]);
assert(left.melt > 0);
fprintf('  严苛粘连(横向): 熔断=%d 偏移=%d end=(%d, %d) -> 能切过粘连线\n', ...
    left.melt, left.offsets, left.end(1), left.end(2));

fprintf('\n全部通过。\n');
