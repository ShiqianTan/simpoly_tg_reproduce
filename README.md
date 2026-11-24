# simpoly_tg_reproduce

使用 [simpoly](https://github.com/) 的多聚合物体系复现 **玻璃化转变温度 (Tg)** 的模拟工作区。对比了经典力场（PCFF / COMPASS / OPLS）与机器学习力场（MACE-OFF23、MatterSim、Vivace），并系统排查了降温协议、链长、体系尺寸、packing/seed、拟合方法和平衡程度对 Tg 的影响。

完整实验报告见 [`docs/results.md`](docs/results.md)。

## 关键结论

- **PCFF 综合最优**：PS 等温 Tg 353 K（实验 373 K，偏差 −20 K），速度约 16 ns/day。
- **等温协议（Plan B）最可靠**：ρ(T) 曲线首次呈现斜率方向正确的玻璃转变；降温扫描法不确定度很大。
- **Tg 提取方法是当前最大瓶颈**：plateau / hyperbolic / 约束连续双线性三种方法差异可达 100–200 K，其中 `bilinear_cont_tg.py`（约束连续双线性）最稳健。
- **PMA 与 PE 是主要残余问题**：PMA-PCFF 等温 Tg 493 K（+212 K）；PE 在 PCFF/OPLS/COMPASS 下一致偏高 +58~78 K（力场固有偏差）。
- **降温速率、链长已排除**；packing/seed 次要；尺寸效应未收敛。

## 目录结构

```
.
├── README.md
├── docs/
│   ├── results.md        # 完整实验报告（目标、环境、全部结果与结论）
│   ├── REPRODUCE.md      # 环境、建模、运行与拟合的复现步骤
│   └── FILE_MAP.tsv      # 原始文件到新路径的完整映射
├── code/
│   ├── root/             # 1944 原子 PS 基准、Tg 拟合/解析、顶层运行脚本
│   ├── multi_pcff/       # 多聚合物建模 (EMC)、输入生成、全部 LAMMPS in.* 文件
│   ├── compare1944/      # PCFF / Vivace / MACE / MatterSim 对比脚本与输入
│   └── small_emc/        # 早期小体系 EMC 建模与输入
├── data/
│   ├── structures/       # PDB、LAMMPS data、EMC packing 输入
│   └── emc/              # EMC 构建输入 (build.emc / build.esh / system.params / system.in)
└── results/
    ├── root/             # 顶层日志、基准结果、拟合 CSV
    ├── multi_pcff/       # 多聚合物 LAMMPS 日志、stages CSV、tg_fit 输出
    ├── compare1944/      # 力场对比日志与拟合结果
    ├── small_emc/        # 小体系日志
    ├── dump/             # 降温过程代表性轨迹快照
    └── tg_fit_fast/      # 早期快速拟合结果
```

`archive_not_tracked/` 保存了未纳入 git 的大文件（EMC 重建中间产物、模型权重、restart、重复的 `*.log.out`），已被 `.gitignore` 忽略；其原始相对路径被保留。

## 快速开始

环境依赖与原始工作路径（LAMMPS/Kokkos、Python env、simpoly、pyemc、mace/ase）见 [`docs/REPRODUCE.md`](docs/REPRODUCE.md)。主要入口：

```bash
# 1) 从日志提取每阶段 T/rho 均值 -> stages CSV
python code/root/parse_log.py --log results/multi_pcff/tg_slow_PE30.log --out /tmp/stages.csv

# 2) 等温日志解析（含势能）
python code/root/parse_iso.py --log results/multi_pcff/tg_iso_PE30L.log --out /tmp/iso.csv

# 3) 约束连续双线性 Tg 拟合（推荐）
python code/root/bilinear_cont_tg.py --input /tmp/stages.csv --out /tmp/tg_fit

# 4) 重建 EMC 体系（需要 simpoly + pyemc 环境）
python code/multi_pcff/build_emc_poly.py PE 0.9 30 4000 PE30
```

> 注意：脚本中保留了原始机器的绝对路径（如 `/home/tione/.../simpoly_tg_repro` 与 conda/mace 环境路径）。复现前请按 `docs/REPRODUCE.md` 调整 `run_env.sh`、`run_mace_lammps.sh` 和 `PYTHONPATH` 等路径。LAMMPS `in.*` 文件中的 `read_data` / `include` 也指向原始 `multi_pcff/<体系>/system.data`，需先按相同布局重建体系。

## 数据说明

- 每个 `results/multi_pcff/tg_*_fit_*/stages_*/` 目录包含 `tg_results.csv`（汇总）与 `tg_per_seed.csv`（逐 seed）。
- `results/**/stages_*.csv` 是拟合器的输入曲线（每阶段平均 T、ρ、势能）。
- 原始 `*.log` 为 LAMMPS 输出；`*.log.out` 为同一次运行的重复 stdout，未提交。
- 体系构建脚本与参数已保留在 `data/emc/`，可按需重新生成 `system.data`。
