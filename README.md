# logic-folding-geometry

几何思想实验：量化 2D 逻辑布局折叠为双 Die 3D 堆叠后的线长收益。

## 核心思路

N 个全互连的标准单元（完全图 K_N），按最优空间密铺排列。比较 2D 网格 vs 双 Die 3D 堆叠下的曼哈顿线长变化。

- **2D**：标准单元挤在尽可能"方"的矩形里
- **3D**：双 Die 堆叠（a×b×2），每层 ⌈N/2⌉ 个单元各自最优密铺
- 距离度量：曼哈顿距离（层间间距 = 1）
- 完全图有 N(N−1)/2 条边，总和即为总 HPWL

## 快速开始

```bash
pip install -r requirements.txt
python experiment.py
```

## 用法

```
python experiment.py              # 运行 N=1..100，弹出交互式图表
python experiment.py --no-plot    # 仅文本输出
python experiment.py --csv        # 同时导出 output/results.csv
python experiment.py --n=500      # 自定义 N 上限
```

## 核心发现（N = 1..100）

| N | 2D 网格 | 3D 堆叠 | 比值 (3D/2D) | 收益 |
|---|---------|---------|-------------|------|
| 7 | 2×4 | 2×2×2 | 0.900 | 10.0% |
| 8 | 2×4 | 2×2×2 | 0.857 | 14.3% |
| 18 | 3×6 | 3×3×2 | 0.804 | 19.6% |
| 50 | 5×10 | 5×5×2 | 0.755 | 24.5% |
| 100 | 10×10 | 5×10×2 | 0.818 | 18.2% |

- **1..100 平均收益：17.4%**
- **峰值收益：24.8%（N=91）**
- N ≤ 6：双 Die 优势尚未显现（层间距离抵消了平面紧凑性的提升）
- N ≥ 7 起收益转正，随 N 增大整体呈上升趋势

## 工程启示

**分簇阈值 N=7**：在 3D 分区/分割器中，小于 7 个标准单元的簇做 2D→3D 折叠几乎没有线长收益。分割器可以将此作为剪枝阈值，跳过小簇，节省算力。

## 输出

- 控制台：格式化表格 + 汇总统计
- `output/plot.png`：四合一线长对比图
- `output/results.csv`：全量原始数据
- `output/thought_experiment.ipynb`：Jupyter Notebook（逐步拆解 + 交互滑块）

## 文件结构

```
logic-folding-geometry/
├── experiment.py               # 单文件：密铺算法 + 线长计算 + CLI + 可视化
├── requirements.txt            # matplotlib
├── output/
│   ├── plot.png                # 生成的对比图
│   ├── results.csv             # 原始数据
│   └── thought_experiment.ipynb # 交互式 Notebook
└── README.md
```
