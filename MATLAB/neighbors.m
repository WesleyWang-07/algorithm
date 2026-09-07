function nb = neighbors(g)
% 在"重力-垂线"基 (g,p) 下返回 7 个邻点的相对位移矩阵，第 j 行 = 邻点 j 的 [dr, dc]：
%   j=1: +g（正前方/正下方）    j=2: +g+p（前右对角）  j=3: +g-p（前左对角）
%   j=4: +p（右侧）            j=5: -p（左侧）        j=6: -g+p（后右对角）
%   j=7: -g-p（后左对角）
% 对应 Python: improved_droplet.py 的 _neighbors。
p = perp_of(g);
nb = [ g(1),     g(2);        % 1
       g(1)+p(1), g(2)+p(2);  % 2
       g(1)-p(1), g(2)-p(2);  % 3
       p(1),      p(2);       % 4
      -p(1),     -p(2);       % 5
      -g(1)+p(1), -g(2)+p(2); % 6
      -g(1)-p(1), -g(2)-p(2)];% 7
end
