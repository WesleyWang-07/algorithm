# -*- coding: utf-8 -*-
"""
健壮性测试：改进滴水算法在任意二值图上应有限、有界、不越界、不死循环。
运行：python test.py
"""
import numpy as np
from improved_droplet import drop_improved, path_metrics
from segment import build_synthetic_character, bidirectional_segment


def test_random(trials=400, seed=7):
    rng = np.random.default_rng(seed)
    for t in range(trials):
        H = rng.integers(8, 90)
        W = rng.integers(8, 90)
        ink = rng.random((H, W)) < rng.uniform(0.1, 0.7)
        for g in ((1, 0), (0, 1)):
            # 从图像内若干白点出发
            for _ in range(6):
                rr = int(rng.integers(0, H)); cc = int(rng.integers(0, W))
                if ink[rr, cc]:
                    continue
                res = drop_improved(ink, rr, cc, g)
                # 断言：熔断、偏移有限且不超过最大步数
                assert res['melt'] + res['offsets'] < 10000, (t, res)
                # 断言：轨迹上每个点都不越界（除终点外的路径点均在界内）
                for (r, c) in res['path'][:-1]:
                    assert 0 <= r < H and 0 <= c < W, (t, (r, c), (H, W))
        if (t + 1) % 100 == 0:
            print(f"  ... 随机测试 {t+1}/{trials}")
    print(f"  OK: {trials} 组随机图全部通过（无死循环/越界/指数爆炸）")


def test_demo_and_hard():
    # 合成谱字（粘连/无粘连）双向切分
    for connect in (True, False):
        ink = build_synthetic_character(connect_top=connect)
        res = bidirectional_segment(ink, metric='D')
        assert res['intersect'][0] > 0
        print(f"  合成谱字(粘连={connect}): 交点={res['intersect']} "
              f"l1熔断={res['metrics1']['A']} l2熔断={res['metrics2']['A']}")

    # 严苛：上下墨迹完全相连
    ink = np.zeros((100, 60), dtype=bool)
    ink[10:45, 10:50] = True
    ink[55:90, 10:50] = True
    ink[45:55, 29:31] = True
    left = drop_improved(ink, 47, 0, (0, 1))
    assert left['melt'] > 0
    print(f"  严苛粘连(横向): 熔断={left['melt']} 偏移={left['offsets']} "
          f"end={left['end']} -> 能切过粘连线")


if __name__ == '__main__':
    print("=== 1) 随机模糊测试 ===")
    test_random()
    print("=== 2) 演示 & 严苛用例 ===")
    test_demo_and_hard()
    print("\n全部通过。")
