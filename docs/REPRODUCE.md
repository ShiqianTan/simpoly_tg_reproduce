# 复现步骤

本文档记录原始运行环境、体系构建、LAMMPS 运行与 Tg 拟合流程。完整结果与讨论见 [`results.md`](results.md)。

## 1. 原始环境

- Python（解析/拟合/ASE/rdkit/MACE）：`/home/tione/notebook/home/tanshiqian/envs/mace/bin/python`
- Python（EMC 建模，pyemc）：`/opt/conda/envs/simpoly/bin/python`
- LAMMPS：`/usr/local/lammps/bin/lmp -k on g 1 -sf kk -pk kokkos newton on neigh half`
  - Vivace / PCFF：`bash code/root/run_env.sh <in> <log>`
  - MACE-OFF23：`bash code/root/run_mace_lammps.sh <in> <log>`（前置 mace env 的 site-packages）
- simpoly 源码：`/home/tione/notebook/home/tanshiqian/github/polymer/tg/simpoly`（`PYTHONPATH=<repo>/src`）

> 仓库中的 run/环境脚本保留了上述绝对路径。换机器时请修改 `run_env.sh`、`run_mace_lammps.sh`、`aggregate_seeds.py` 以及各 `build_*.py` 中的 `PYTHONPATH` / 工作目录。

## 2. 体系构建（EMC）

多聚合物体系由 `code/multi_pcff/build_emc_poly.py` 生成（默认 PCFF）：

```bash
PY=/opt/conda/envs/simpoly/bin/python
# argv: POLY density n_ru n_tot LABEL [SEED]
$PY code/multi_pcff/build_emc_poly.py PE  0.9 30 4000 PE30
$PY code/multi_pcff/build_emc_poly.py PS  0.9 30 4800 PS30
$PY code/multi_pcff/build_emc_poly.py PMMA 0.9 30 4000 PMMA30
$PY code/multi_pcff/build_emc_poly.py PMA 0.9 30 4000 PMA30
```

其他力场用 `build_ff.py`（第 7 个参数为 EMC field，如 `compass` / `opls`）：

```bash
$PY code/multi_pcff/build_ff.py PE 0.9 30 4000 PE30opls 42 opls
```

脚本会在自身所在目录下创建 `LABEL/` 并写入 `build.emc`、`build.esh`、`system.data`、`system.params`、`data.lmps`。仓库中仅保留体积较小的 `build.emc` / `build.esh` / `system.params` / `system.in`（位于 `data/emc/`），大文件需重新生成。

构建注意：

- 建模密度统一用 **0.9 g/cm³**（用实验密度会因初始压力过高在 PPPM 下崩溃）。
- PMMA / PMA 熔体阶段 `MELT_DT = 0.25 fs`；PE / PS 用 0.5 fs。
- n_ru=30 对应约 C60（PE）到 C240（PS）；大体系 n_tot≈8000（约 8000 原子）。
- 构型检查：`python code/multi_pcff/check_cell.py`（键长、最小非键距离、Rg）。

## 3. 生成 LAMMPS 输入

`code/multi_pcff/make_input.py` 根据体系目录下的 `system.data` / `system.params` 生成降温扫描输入：

```bash
# argv: POLY T_HIGH T_LOW T_STEP MELT_DT STAGE MELT_PS COOL_DT [OUT_LABEL]
$PY code/multi_pcff/make_input.py PE30 433 113 20 0.5 20000 20
```

等温（Plan B）与 MACE / MatterSim 输入分别由 `make_input` 的变体（在仓库历史中对应 `in.tg_iso_*`、`in.tg_mace_*`、`in.tg_ms_*`）生成。生成的 `in.*` 位于 `code/multi_pcff/`。

> `make_input.py` 以脚本所在目录为 `WORK`，因此需要把重建出的 `LABEL/` 放在与脚本相同的目录（或修改 `WORK`）。原 `in.*` 中的 `read_data` / `include` 使用原始绝对路径，迁移后需替换为新布局路径。

## 4. LAMMPS 运行

```bash
GPU=0 bash code/root/run_env.sh     code/multi_pcff/in.tg_slow_PE30 results/multi_pcff/tg_slow_PE30.log
GPU=1 bash code/root/run_mace_lammps.sh code/multi_pcff/in.tg_mace_PE30 results/multi_pcff/tg_mace_PE30.log
```

- 降温协议分三档：SHORT 0.625 ps/阶段、STRICT 2.5 ps/阶段、SLOW 10 ps/阶段。
- 等温协议：每温度点 50 ps（100000 步 @0.5 fs），17 个温度点（533→213 K 或 433→113 K），熔体 20 ps + 预平衡。
- 大体系约 8000 原子；小体系 n_ru=30 约 2000–4800 原子。

## 5. 解析与 Tg 拟合

```bash
PY=/home/tione/notebook/home/tanshiqian/envs/mace/bin/python

# 降温扫描：每阶段后一半的 Temp/Density 均值 -> stages CSV
$PY code/root/parse_log.py --log results/multi_pcff/tg_slow_PE30.log --out results/multi_pcff/stages_slow_PE30.csv

# 等温扫描：额外提取 PotEng 与阶段内漂移
$PY code/root/parse_iso.py --log results/multi_pcff/tg_iso_PE30L.log --out results/multi_pcff/iso_PE30L_stages.csv

# 转为 simpoly cooling_protocol 所需格式（可选 pe 列）
$PY code/root/iso_to_stages.py --in results/multi_pcff/iso_PE30L_stages.csv --out /tmp/stages.csv

# 三种 Tg 提取器
$PY code/root/hyperbolic_tg.py       --input /tmp/stages.csv --out /tmp/tg_hyp
$PY code/root/bilinear_cont_tg.py    --input /tmp/stages.csv --out /tmp/tg_cont
$PY code/root/bilinear_tg.py         --input /tmp/stages.csv --out /tmp/tg_bilin
```

- `bilinear_cont_tg.py`：约束连续单折点分段线性，强制 `|m_glass| < |m_liquid|`，推荐。
- `hyperbolic_tg.py`：Patrone 型平滑双曲拟合，多起点 `curve_fit`，对噪声敏感。
- `bilinear_tg.py`：早期不连续双线性，可靠性最低。

多 seed 汇总示例：`code/multi_pcff/aggregate_seeds.py`（内部路径需按新布局调整）。

## 6. 结果位置约定

| 类型 | 位置 |
|---|---|
| LAMMPS 原始日志 | `results/<子项目>/*.log` |
| 阶段曲线 CSV | `results/**/stages_*.csv`、`results/**/iso*_stages.csv` |
| 逐 seed / 汇总 Tg | `results/**/tg_*_fit_*/stages_*/tg_per_seed.csv`、`tg_results.csv` |
| 轨迹快照 | `results/dump/*.lammpstrj.*` |
| 完整报告 | `docs/results.md` |

## 7. 未提交文件

`archive_not_tracked/`（被 `.gitignore` 忽略）保留以下内容，原始相对路径不变：

- `*.log.out`：与同名 `*.log` 同一次运行的重复 stdout；
- `*.pt`：MACE-OFF23 / MatterSim 的 LAMMPS mliap 模型权重；
- `*.restart`：降温过程的 restart 检查点；
- `multi_pcff/*/system.data`、`multi_pcff/*/data.lmps`、`small_emc/build/system.data`：EMC 构建产物。

如本地需要继续运行，可直接引用 `archive_not_tracked/` 中的大文件，或用 `code/multi_pcff/build_emc_poly.py` 重新生成。

文件级移动记录见 [`FILE_MAP.tsv`](FILE_MAP.tsv)。
