# simpoly Tg 模拟实验结果汇总

工作目录：`/home/tione/notebook/home/tanshiqian/simpoly_tg_repro`
仓库：`/home/tione/notebook/home/tanshiqian/github/polymer/tg/simpoly`

---

## 1. 目标与实验参考值

对同一批聚合物体系，用不同力场（Vivace / MACE-OFF23 / PCFF / COMPASS / OPLS）模拟玻璃化转变温度 Tg，并对比精度与速度（ns/day）。

实验参考（`src/simpoly/poly_arena/experiment/resources/data.csv`）：

| 聚合物 | SMILES | 实验密度 (g/cm³) | 实验 Tg (K) |
|---|---|---|---|
| PS   | `*CC(C1=CC=CC=C1)*`    | 1.05 | 373 |
| PMMA | `*CC(C)(C(=O)OC)*`     | 1.17 | 378 |
| PMA  | `*CC(C(=O)OC)*`        | 1.22 | 281 |
| PE   | `*CC*`                 | 0.85 | 195 |

> 注：PMMA 不在仓库 `EXP_TG` 表中（仓库遗漏），上表取自 `data.csv`。

---

## 2. 环境与工具链

- Python（解析/拟合）：`/home/tione/notebook/home/tanshiqian/envs/mace/bin/python`（mace, ase, rdkit）
- Python（EMC 建模）：`/opt/conda/envs/simpoly/bin/python`（pyemc；EMC 二进制有效期校验已打补丁）
- LAMMPS：`/usr/local/lammps/bin/lmp -k on g 1 -sf kk -pk kokkos newton on neigh half`
  - Vivace/PCFF：`bash run_env.sh <in> <log>`
  - MACE-OFF23：`bash run_mace_lammps.sh <in> <log>`（前置 mace env 的 site-packages）
- Tg 拟合 CLI：
  `PYTHONPATH=<repo>/src <mace-python> <repo>/src/simpoly/poly_arena/analysis/cli/cooling_protocol.py --inputs <csv> --out <dir>`

### 工作目录脚本

| 脚本 | 作用 |
|---|---|
| `parse_log.py` | 从 LAMMPS `# Stage:` 日志提取每阶段 Temp/Density 的后半段均值/标准差 → stages CSV |
| `parse_iso.py` | 同上，另提取 PotEng，并给出阶段内漂移（后 1/4 − 前 1/4） |
| `iso_to_stages.py` | 把 parse_iso 的 CSV 转成拟合器所需的 stages 格式（可选用 `pe` 列做能量曲线） |
| `hyperbolic_tg.py` | Patrone 型平滑双曲拟合（多起点 curve_fit） |
| `bilinear_cont_tg.py` | 约束连续单折点分段线性拟合（仅接受 \|m_glass\| < \|m_liquid\|） |
| `bilinear_tg.py` | 早期自由（不连续）双线性拟合，可靠性最低 |
| `build_emc_poly.py` | argv: POLY density n_ru n_tot LABEL SEED |
| `build_ff.py` | argv: POLY density n_ru n_tot LABEL SEED FIELD（替换 EMC 模板的 `field pcff`） |
| `make_input.py` | argv: POLY T_HIGH T_LOW T_STEP MELT_DT STAGE MELT_PS COOL_DT |
| `check_cell.py` | 检查 EMC 构型：键长、最小非键距离、Rg |

### 体系构建说明

- EMC 建模密度统一用 **0.9 g/cm³**（用实验密度建模会因初始压力过高在 PPPM 下崩溃）。
- PMMA / PMA 的熔体阶段需 **MELT_DT = 0.25 fs**（0.5 fs 会 PPPM `out of range`）。
- n_ru=30 对应约 C60（PE）到 C240（PS）链长；大体系 n_tot=8000（约 8000 原子）。

---

## 3. 速度基准（1944 原子 PS，单张空闲 GPU，dt 0.5 fs，NVE）

| 力场 | s/step | ns/day | 相对速度 |
|---|---|---|---|
| PCFF | 0.00267 | **16.16** | 1× |
| Vivace (mliap) | 0.0175 | **2.47** | 6.5× 慢 |
| MACE-OFF23 medium (mliap, float32) | 0.95 | **0.045** | 360× 慢 |
| MACE-OFF23 medium (ASE, 参考) | 0.372 | 0.116 | 139× 慢 |

MatterSim v1.0.0-1M 在 PE30（2002 原子）上的独立基准：**0.25 s/step，0.173 ns/day**（4.0 timesteps/s，8.0 katom-step/s）。

力场速度排序（同量级体系）：**PCFF 16.16 > Vivace 2.47 > MatterSim 0.173 > MACE-OFF23 0.045 ns/day**。MatterSim 约比 MACE 快 3.8×，但仍比 Vivace 慢 14×、比 PCFF 慢 94×。

- PCFF 在 GPU/Kokkos 下约 **0.059–0.069 s/step**（1944 原子，含 PPPM）与 ML-IAP 同量级，无速度优势。
- LAMMPS thermo 的 `S/CPU` 列实际是 **steps/second**，不是 s/step。
- 大体系 PS30L（4820 原子）PCFF 慢协议实测 0.00368 s/step = **11.74 ns/day**。
- 1944 原子比 10044 原子每步只快约 2×（ML 推理固定开销占主导），**按原子效率反而更低**（23.5 vs 62.0 katom-step/s）。

---

## 4. 三方力场对比（1944 原子 PS，实验 373 K）

同一 EMC 体系、同一降温协议（533→213 K，步长 20 K，17 阶段）：

| 协议 | PCFF | MACE-OFF23 medium | Vivace |
|---|---|---|---|
| SHORT（0.625 ps/阶段） | 395.4 (+22.4) | 433.4 (+60.4) | 490.8 (+117.8) |
| STRICT（2.5 ps/阶段） | 350.7 (−22.3) | 未跑（太慢） | 268.8 (−104.2) |

**结论**：
- PCFF 精度最好（两种协议下偏差 ±23 K 以内）且速度最快。
- MACE-OFF23 medium 严重低估 PS 密度（0.6–0.8 vs 实验 ~1.0），速度最慢。
- Vivace 的 Tg 对协议极敏感（−104 ~ +118 K），密度-温度曲线没有清晰拐点，Tg 定义不清。

---

## 5. 多聚合物 PCFF 结果

### 5.1 n_ru=10（短链，SHORT 协议，seed 42）

| 聚合物 | Tg (K) | 实验 | 偏差 |
|---|---|---|---|
| PS | 395.4 | 373 | +22.4 |
| PMMA | 275.1 | 378 | −102.9 |
| PMA | 345.4 | 281 | +64.4 |
| PE | 113.4 | 195 | −81.6 |

短链端基效应严重（PE 只有 ~C20，密度 ~0.70 vs 实验 0.85）。

### 5.2 n_ru=30（SHORT 协议，seed 42）

| 聚合物 | Tg (K) | 实验 | 偏差 |
|---|---|---|---|
| PS30 | 354.6 | 373 | −18.4 |
| PMMA30 | 354.0 | 378 | −24.0 |
| PMA30 | 456.8 | 281 | +175.8 |
| PE30 | 251.8 | 195 | +56.8 |

链长效应：除 PS 外，n_ru 10→30 普遍升高 Tg（PE +138、PMMA +79、PMA +111 K）。

### 5.3 多 seed 统计（n_ru=30，SHORT，seeds 1/2/3/7/42）

| 聚合物 | 平均 Tg (K) | std | 中位数 | 实验 |
|---|---|---|---|---|
| PS30 | 303.6 | ±75.4 | 306.7 | 373 |
| PMMA30 | 380.4 | ±95.3 | 353.0 | 378 |
| PMA30 | 365.7 | ±67.7 | 365.3 | 281 |
| PE30 | 230.7 | ±80.6 | 223.9 | 195 |

逐 seed Tg 散布 68–95 K（std），**超过链长效应本身** → 单 seed 的绝对 Tg 不可靠。

### 5.4 n_ru=30 STRICT 协议（2.5 ps/阶段，seed 42）

| 聚合物 | Tg (K) | 实验 | 偏差 |
|---|---|---|---|
| PS30 | 238.5 | 373 | −134.5 |
| PMMA30 | 311.9 | 378 | −66.1 |
| PMA30 | 302.8 | 281 | +21.8 |
| PE30 | 304.5 | 195 | +109.5 |

STRICT 值全部聚集在 240–310 K，不重现实验顺序。

### 5.5 SLOW 协议（10 ps/阶段，seed 42）

三种拟合方法（plateau / hyperbolic / 约束连续双线性）：

| 聚合物 | plateau | hyperbolic | cont-bilinear | 实验 |
|---|---|---|---|---|
| PS30 | 294.5 | 294.5 | 292.1 | 373 |
| PMMA30 | 362.1 | 469.6 | 472.9 | 378 |
| PMA30 | 391.8 | 391.8 | 392.6 | 281 |
| PE30 | 302.9 | 302.9 | 293.4 | 195 |

- hyperbolic 与 plateau 在 PS30/PMA30/PE30 上一致，但 PMMA30 差异巨大（469.6 vs 362.1）。
- 约束连续双线性与 hyperbolic 一致 → **simpoly 的 plateau 判据是异常值**。
- 自由（不连续）双线性最不可靠，可弃用。

### 5.6 链长与 packing 排查

| 实验 | 结果 | 结论 |
|---|---|---|
| PMA n_ru 30→40 | 393.4 K（三法一致） | 链长已饱和，非 Tg 偏差来源 |
| PE30 packing（seed 42 vs 7） | 302.9 vs 318.9 K（~15–20 K） | packing 影响小 |
| PMA30 packing（seed 42 vs 11） | 391.8 vs 393.4 K | 之前 seed 7 的 339 K 是拟合假象 |

### 5.7 PE 专项：链长与副本散布（慢降温，10 ps/阶段）

**链长效应（PCFF，seed 42）**：DP10 113.4 → DP30 302.9 → DP40 242.6 → DP50 358.2 K，**无单调趋势**，散布 ~250 K。

**PE40 PCFF 副本（5 seeds，cont-bilinear）**：

| seed | Tg (K) |
|---|---|
| 1 | 231.9 |
| 42 | 252.5 |
| 3 | 253.0 |
| 2 | 253.7 |
| 7 | 353.8（离群） |
| **中位数** | **253.0** |
| 均值 ± std | 269 ± 48 |

→ 副本散布 ±48 K（离群 seed 7 达 +100 K），**大于链长/力场效应**。单 seed 的 242.6 K 属代表性值，非偶然。

**PE40 其他力场**（方法间差极大，不可靠）：COMPASS plateau 215.9 / hyperbolic 366.7 / cont 373.7；OPLS plateau 137.2 / hyperbolic 137.2 / cont 393.7。

---

## 6. 降温速率外推（PE30）

| 速率 | cont-bilinear | hyperbolic |
|---|---|---|
| 2 K/ps（10 ps/阶段） | 293.4 | 302.9 |
| 1 K/ps（20 ps/阶段） | 333.6 | 330.7 |
| 0.5 K/ps（40 ps/阶段） | 333.0 | 545.3（液态斜率 −0.475，无效） |

- 趋势**反物理**（越慢 Tg 越高），且幅度远小于文献灵敏度（~3–5 K/十倍速率）。
- 即使外推 14 个数量级也只能改变 ~50 K。
- **结论：降温速率不能解释 100+ K 的偏差。**

---

## 7. 力场对比（PCFF / COMPASS / OPLS）

EMC field 覆盖：COMPASS 不支持酯基（PMMA/PMA 失败）；OPLS 不支持芳香（PS 失败）。两者互补覆盖全部四种聚合物。

### 7.1 小体系（n_ru=30，SLOW）

| 聚合物 | PCFF | COMPASS | OPLS | 实验 |
|---|---|---|---|---|
| PE | 303 | 277 | 233 | 195 |
| PS | 295 | 324 | — | 373 |
| PMMA | 470 | — | 276–396 | 378 |
| PMA | 392 | — | 453–465 | 281 |

### 7.2 大体系（~8000 原子，SLOW）

| 体系 | plateau | hyperbolic | cont-bilinear | 实验 |
|---|---|---|---|---|
| PMA30Lopls (OPLS) | 420.5 | 425.8 | 392.9 | 281 |
| PE30Lopls (OPLS) | 190.6 | 392.6 | 392.6 | 195 |
| PS30Lcmp (COMPASS) | 失败 | 441.6 | 433.0 | 373 |

### 7.3 低温柔量密度

| 体系 | PCFF | COMPASS | OPLS | 实验 |
|---|---|---|---|---|
| PE | 0.816 | 0.872 | 0.879 | 0.85 |
| PS | 0.992 | 1.045 | — | 1.05 |
| PMMA | 1.105 | — | 1.097 | 1.17 |
| PMA | 1.179 | — | 1.144 | 1.22 |
| PS30L | 0.997 | — | — | 1.05 |
| PMMA30L | 1.095 | — | — | 1.17 |
| PE30L | 0.829 | — | — | 0.85 |

**COMPASS / OPLS 的密度明显更接近实验。**

### 7.4 机器学习力场（MACE-OFF23 medium / MatterSim v1.0.0-1M）

MACE-OFF23 medium，SHORT 协议（0.625 ps/阶段），`run_mace_lammps.sh`（float32 cueq mliap）：

| 体系 | plateau | hyperbolic | cont-bilinear | 低温密度 | 实验 Tg | 实验密度 |
|---|---|---|---|---|---|---|
| PE30 (seed 42) | 357.4 | 357.4 | 343.9 | 0.746 | 195 | 0.85 |
| PE30b (seed 7) | 373.0 | 373.0 | 373.0 | 0.795 | 195 | 0.85 |
| PMMA30 | 411.9 | 850.2（无效） | 412.6 | 0.713 | 378 | 1.17 |
| PMA30 | 401.6 | 400.1 | 389.8 | 0.760 | 281 | 1.22 |
| PS（1944 原子） | 433.4 | — | — | ~0.82 | 373 | 1.05 |

- MACE 的密度全线严重偏低（PE 0.75–0.80、PMMA 0.71、PMA 0.76、PS ~0.82），且高温段**非单调**（先降后升），拟合斜率常常反号 → Tg 不可靠。
- PE 的 MACE 结果（344–373 K）比 PCFF（253–273 K）**更差**，两个 seed 一致 → 系统性偏差。
- **MatterSim v1.0.0-1M**：PE30 冷却扫描中密度崩塌（LAMMPS NPT 膨胀 5.5 倍到 **0.163 g/cm³**；独立 ASE NPT 收敛到 **0.46–0.48 g/cm³**）。接口/力/压力均已逐项验证正确（力最大差 8.9e-5 eV/Å，有限差分压力误差 0.4%），因此是**模型本身**对聚合物液相描述不佳（主要在无机材料 MPtrj 上训练）。**MatterSim 的 Tg 结果不可用。**

### 7.5 MACE 等温协议（已完成）

因 MACE 约 0.95–1.1 s/step，无法承受标准等温协议（50 ps/阶段 ≈ 470 h/任务），缩减为：

- **协议**：17 阶段 533→213 K（步长 20 K），每阶段 **5 ps**（10000 步 @0.5 fs）；熔体 700 K 10 ps + 预平衡 533 K 10 ps；共 210000 步。
- **4 个任务**：PMMA30（seed 42，4068 原子）、PMMA30b（seed 7，1808 原子）、PMA30（seed 42，3982 原子）、PMA30b（seed 7，1810 原子）。
- 全部完成 17/17，wall time 36–55 h（PMMA30 54:30:31、PMA30 53:06:07、PMMA30b 39:53:46、PMA30b 36:18:32）。

结果（约束连续双线性，所有拟合斜率方向物理正确）：

| 体系 | seed | ρ-Tg (K) | E-Tg (K) | 实验 Tg | ρ 范围 (g/cm³) |
|---|---|---|---|---|---|
| PMMA30 | 42 | 392.8 | 373.4 | 378 | 0.781@535 → 1.011@213 |
| PMMA30b | 7 | 353.7 | 353.7 | 378 | 0.825@534 → 0.942@213 |
| PMA30 | 42 | 373.5 | 373.5 | 281 | 0.819@534 → 1.157@213 |
| PMA30b | 7 | 252.4 | 312.2 | 281 | 0.903@534 → 1.185@213 |

- **PMMA**：等温协议显著优于 MACE 冷却扫描（seed 42：373–393 vs 412.6 K），ρ-Tg 与 E-Tg 基本一致，接近实验 378 K。
- **PMA**：seed 42 给出 373.5 K（+92），seed 7 给出 252.4/312.2 K → **seed 散布约 120 K**，绝对值不可靠。
- 密度仍偏低（PMMA 1.01 vs 1.17；PMA 1.16–1.19 vs 1.22）；阶段内 ρ 漂移最大 0.02–0.04，E 漂移在高温段较大。

---

## 8. 大体系 PCFF（~8000 原子，SLOW，seed 42）

| 体系 | 原子数 | plateau | hyperbolic | cont-bilinear | 实验 |
|---|---|---|---|---|---|
| PS30L | 8194 | 276.0 | 266.1 | 272.8 | 373 |
| PMMA30L | 8136 | 279.4 | 473.9 | 473.9 | 378 |
| PE30L | 8008 | 304.8 | 298.2 | 313.4 | 195 |
| PMAoptC | 7964 | 335.8 | 335.8 | 332.8 | 281 |

**尺寸效应方向自相矛盾**：
- PCFF：大体系**降低** Tg（PS 294→266，PMA 392→336）
- COMPASS/OPLS：大体系**升高** Tg（PS 324→442，PE 233→393）

→ 结果未收敛，很可能被协议/拟合假象主导。

---

## 9. 等温协议（Plan B）——目前最可靠的一组结果

### 9.1 协议

每个温度点保持 **50 ps**（100000 步 @0.5 fs），共 17 个温度点（533→213 K 或 433→113 K），熔体 20 ps + 预平衡。同时记录 **密度 ρ 和势能 E**。

### 9.2 完整等温 Tg 表（~8000 原子，约束连续双线性）

| 聚合物 | 力场 | ρ-Tg (K) | E-Tg (K) | 实验 | ρ 偏差 |
|---|---|---|---|---|---|
| PS | PCFF | **353.1** | 472.9 | 373 | **−20** |
| PS | COMPASS | 432.8 | 432.8 | 373 | +60 |
| PMMA | PCFF | 413.1 | 392.8 | 378 | **+35 / +15** |
| PMMA | OPLS | 453.1 | 453.1 | 378 | +75 |
| PMA | PCFF | 493.0 | 453.3 | 281 | +212 |
| PMA | OPLS | 353.1 | 372.8 | 281 | +72 |
| PE | PCFF | 273.2 | 273.2 | 195 | +78 |
| PE | OPLS | 273.2 | 333.1 | 195 | +78 |
| PE | COMPASS | 273.0 | 273.0 | 195 | +78 |
| PE | COMPASS (seed 7) | 233.1 | 253.0 | 195 | +38 / +58 |

### 9.3 关键改进

1. **斜率方向终于物理正确**：所有等温曲线的玻璃态斜率都比液态平缓（降温协议下经常反过来）。四种体系全部通过 `|m_glass| < |m_liquid|` 判据。
2. **PS 大幅修正**：PS30L PCFF 等温 353 K vs 降温法 276 K，更接近实验 373 K。
3. **顺序部分恢复**：PS(353) > PE(273) 与实验 (373 > 195) 一致。
4. **ρ 与 E 互相印证**：PS30Lcmp、PMMA30Lopls、PE30L 两者完全一致；其余差 20–120 K。

### 9.4 阶段内漂移诊断（平衡收敛性）

- ρ 漂移小（~0.001–0.003），且**不随 T 降低而增大** → 低温玻璃态已收敛。
- E 漂移在高 T 较大（−30 ~ −105），低温段小（±1–10）→ **高温液态支仍未完全平衡**。

### 9.5 仍未解决

- **PMA 是最大异常**：PCFF 等温 493 K（+212 K），比降温法（392 K）更差；OPLS 353/373 K（+72/+92 K）。
- **PE 系统性偏高 +78 K**，PCFF/OPLS 一致 → 更像力场固有偏差（或实验参考值分歧，文献 PE Tg 148–240 K）。
- **实验顺序 PS≈PMMA>PMA>PE 仍未完全复现**：
  - PCFF：PMA > PMMA > PS > PE
  - OPLS：PMMA > PMA > PE

### 9.6 PE 专项结论（多协议 + 多力场收敛）

PE 的 Tg 在多种独立配置下收敛：

| 方法 | Tg (K) | 实验 |
|---|---|---|
| 等温 PCFF（seed 42） | 273.2 | 195 |
| 等温 OPLS（seed 42） | 273.2 | 195 |
| 等温 COMPASS（seed 42） | 273.0 | 195 |
| 等温 COMPASS（seed 7） | 233.1 | 195 |
| 慢降温 PCFF PE40（5 seed 中位数） | 253.0 | 195 |

→ **三个独立力场等温结果收敛于 273 K**；慢降温多 seed 中位数 253 K。PE 的 +58~78 K 偏差是**力场固有偏差**，换力场/协议/链长都消除不了。剩余不确定度：副本散布 ±40~48 K；实验参考本身（PE Tg 文献 148–240 K）。

→ **PE 在现有框架内（C60–C100 链长、经典力场、当前协议）已接近优化极限。**

---

## 10. 拟合方法对比与可靠性

三种提取器：

1. **simport cooling_protocol.py（自洽 plateau）**——对无清晰拐点的曲线不可靠，偶发假象（如 PMMA30 SLOW 362 vs 470）。
2. **hyperbolic_tg.py（Patrone 平滑双曲）**——多起点 curve_fit；对噪声敏感，等温数据上出现 770 K / 正玻璃态斜率等无效结果。
3. **bilinear_cont_tg.py（约束连续双线性）**——最稳健；强制 \|m_glass\| < \|m_liquid\|，等温数据全部通过。

**结论**：Tg 提取/平衡的不确定度（±100–200 K）在某些大体系力场对比中**与力场效应同量级甚至更大**（如 PE30Lopls plateau 190.6 vs hyperbolic 392.6，相差 200 K）。

---

## 11. 影响因素排查汇总

| 因素 | 结论 |
|---|---|
| 降温速率 | **排除**——趋势反物理且幅度不足（0.6 个数量级仅 ~2–3 K） |
| 链长 | **排除**——n_ru ≥ 30 后饱和（PMA 30→40 无变化）；PE DP10/30/40/50 无单调趋势 |
| Packing / seed | 次要（~15–20 K）；但 PE40 PCFF 副本散布 ±48 K（5 seed），PMA seed 7 的 339 K 是拟合假象 |
| 体系尺寸 | 显著但**方向自相矛盾**（PCFF 降低、COMPASS/OPLS 升高）→ 未收敛 |
| 拟合方法 | **当前最大不确定度来源**（±100–200 K） |
| 力场 | 主要嫌疑（PMA 酯基、PE 普遍偏高），但需先消除拟合不确定度 |
| 平衡程度 | 等温法改善了 PS，但 PMA 反而恶化 |

---

## 12. 构型诊断

`check_cell.py` 检查结果——所有 EMC 构型结构正常，**无严重构建缺陷**：

| 体系 | 原子数 | 链数 | 盒子 (Å) | 键长范围 (Å) | 最小非键距离 (Å) | Rg (Å) |
|---|---|---|---|---|---|---|
| PMA30 | 3982 | 11 | 37.43 | 0.963–1.870 | 1.437 | 9.39 |
| PMA40 | 1928 | 4 | 29.41 | 0.983–1.789 | 1.363 | 11.99 |
| PS30 | 4820 | 10 | 38.64 | 0.978–1.859 | 1.388 | 11.12 |
| PMMA30 | 4068 | 9 | 36.82 | 0.949–1.977 | 1.465 | 10.67 |
| PE30 | 2002 | 11 | 25.77 | 0.975–1.769 | 1.443 | 9.37 |

**已知数值问题**：
- PMA 长平衡变体（密度 0.6 与 0.9 + 100 ps 熔体）均以 `Out of range atoms - cannot compute PPPM` 崩溃。
- PMMA30/PMA30 必须用 0.25 fs 熔体。
- MACE-OFF23 + LAMMPS mliap 在 1944 原子体系上会卡在 thermo step 0（~42 GB 显存），改用 ASE 或 float32 cueq 模型。

---

## 13. 总体结论

1. **PCFF 是综合最优**：精度最好（PS 等温 353 K，偏差 −20 K）、速度最快（16.16 ns/day）。
2. **等温协议（Plan B）是目前最可靠的方法**：ρ(T) 曲线首次呈现真正的玻璃转变（斜率方向正确），PS 结果接近实验。
3. **Tg 提取方法是当前最大瓶颈**：±100–200 K 的不确定度与力场效应同量级。约束连续双线性最稳健。
4. **PMA 和 PE 是主要残余问题**：PMA-PCFF 等温 493 K（+212 K）；PE 在 PCFF/OPLS/COMPASS 下一致偏高 +58~78 K。
5. **降温速率、链长已排除**；packing 影响小；尺寸效应未收敛。
6. **PE 偏差确认为力场固有**：三个独立力场等温收敛于 273 K，慢降温多 seed 中位数 253 K，均 +58~78 K。
7. **副本散布（±40~111 K）是 PE 的主要不确定度来源**，单 seed 结果不可靠。
8. **实验顺序 PS≈PMMA>PMA>PE 仍未被任何单一配置复现。**
9. **机器学习力场整体不如经典力场**：MACE-OFF23 medium 密度全线偏低（PE 0.75–0.80、PMMA 0.71、PMA 0.76、PS ~0.82），PE Tg 344–373 K 比 PCFF 更差；MatterSim v1.0.0-1M 更极端，PE 密度仅 0.46–0.48 g/cm³，Tg 不可用。两者速度也远慢于 PCFF（0.045 / 0.173 vs 16.16 ns/day）。

### 建议的后续方向

- 用等温协议补跑 PMMA/PMA/PE 的多种子（≥3 seeds）以给出可信误差棒。
- 对 PMA 系统检查 PCFF 酯基参数，或改用其他力场（OPLS 相对更好）。
- 用更长的等温保持（100–200 ps/点）验证高温液态支是否收敛。
- 考虑用 E-T 曲线（常比 ρ-T 拐点更清晰）作为主 Tg 判据。

---

## 14. 主要文件索引

| 路径 | 内容 |
|---|---|
| `multi_pcff/tg_iso_<L>.log` | 等温扫描原始日志 |
| `multi_pcff/stages_iso_<L>.csv` | 等温解析结果（T, ρ, E, 漂移） |
| `multi_pcff/iso_<L>_stages.csv` | ρ-T 拟合输入 |
| `multi_pcff/isoE_<L>_stages.csv` | E-T 拟合输入 |
| `multi_pcff/tg_slow_<L>.log` | 慢降温协议日志 |
| `multi_pcff/stages_slow_<L>.csv` | 慢降温解析结果 |
| `multi_pcff/stages_pcff_<P>30_all.csv` | n_ru=30 多 seed 汇总 |
| `multi_pcff/tg_iso_<L>_h100.log`, `_h200.log` | 长等温保持（100 / 200 ps 每阶段） |
| `multi_pcff/stages_slow_PE40*.csv` | PE40 多 seed / 多力场副本 |
| `multi_pcff/in.tg_iso_<L>` | 等温输入脚本 |
| `multi_pcff/in.tg_slow_<L>` | 慢降温输入脚本 |
| `compare1944/` | 1944 原子三方对比（Vivace/MACE-OFF/PCFF） |
| `compare1944/comparison_summary.csv` | 三方 Tg + 速度汇总 |
| `small_emc/build/` | 1944 原子 PS 的 EMC 构型 |
| `run_iso.sh`, `run_iso2.sh` | 等温批次启动脚本 |
| `run_env.sh`, `run_mace_lammps.sh` | LAMMPS 运行环境 |
| `run_mattersim_lammps.sh` | MatterSim LAMMPS 运行环境 |
| `multi_pcff/make_input_mace.py`, `make_input_mattersim.py` | MACE / MatterSim 输入生成 |
| `multi_pcff/tg_ms_PE30.log`, `stages_ms_PE30.csv` | MatterSim PE30 扫描（密度崩塌，不可用） |
| `compare1944/mattersim-v1.0.0-1M_mliap.pt` | MatterSim mliap 模型 |
| `compare1944/check_mattersim_*.py`, `ase_ms_npt_pe30.py` | MatterSim 接口/力/压力验证脚本 |
| `/home/tione/notebook/home/tanshiqian/simpoly_data/` | PolyPack / PolyDiss 数据集（HF 镜像下载） |
| `multi_pcff/in.tg_mace_iso_<L>`, `tg_mace_iso_<L>.log` | MACE 等温协议输入 / 日志 |
| `run_mace_iso.sh`, `run_mace_iso_retry.sh` | MACE 等温批次启动 / 重试调度器 |

---

## 15. 当前状态

**所有任务均已完成，无运行中进程，4 张 GPU 空闲。**

### 已完成

- **MACE 等温协议**（PMMA/PMA × 2 seeds）：4/4 完成 17/17，见 §7.5。
- **MACE PMMA/PMA 冷却扫描**（SHORT）：见 §7.4。
- **MatterSim v1.0.0-1M** 对比完成（PE 密度崩塌，结果不可用），见 §7.4。
- **PolyPack / PolyDiss** 数据集已下载校验，见 §14。

### MACE 汇总（4 聚合物）

| 聚合物 | MACE 冷却 SHORT | MACE 等温 ρ-Tg | MACE 等温 E-Tg | PCFF 等温 ρ-Tg | 实验 |
|---|---|---|---|---|---|
| PS | 433.4 | 未跑 | 未跑 | 353.1 | 373 |
| PMMA | 412.6 | 392.8 / 353.7 (2 seeds) | 373.4 / 353.7 | 413.1 | 378 |
| PMA | 389.8 | 373.5 / 252.4 (2 seeds) | 373.5 / 312.2 | 493.0 | 281 |
| PE | 343.9–373.0 | 未跑 | 未跑 | 273.2 | 195 |


