# SimPoly 环境搭建与测试教程（TiOne / DinD 开发机）

本文记录在 **TiOne 开发机（Docker-in-Docker）** 上为 [SimPoly](.) 搭建独立运行环境、
构建镜像并跑通测试的完整流程，便于复现。

---

## 0. 结论速览

| 项目 | 结果 |
| --- | --- |
| 镜像 | `simpoly:tione`（约 **9.85 GB**） |
| Python | 3.12.14（conda env `simpoly`） |
| PyTorch | `2.11.0+cu130`（CUDA 13.0） |
| LAMMPS | `stable_22Jul2025_update4`，启用 `PKG_KOKKOS` / `ML-IAP` / `PYTHON` |
| Kokkos 架构 | `BLACKWELL120`（sm_120，适配 RTX PRO 5000） |
| CPU 测试 | **55 passed / 5 failed / 4 skipped / 10 deselected** |
| 失败原因 | 4 个为 **EMC 二进制授权过期**（外部软件）；1 个为 `torch.fx` deepcopy 兼容性问题 |
| GPU 测试 | 本机容器**无法使用 GPU**（见 §1），需在 TiOne 平台或带 NVIDIA Container Toolkit 的机器上运行 |

> 关键约束：**本机 Docker 是 DinD（daemon 在容器内），没有安装 NVIDIA Container
> Toolkit**。`--gpus all`、`--device`、`-v /dev/nvidia*` 全部被策略拒绝，容器内
> `torch.cuda.is_available()` 恒为 `False`。因此 GPU 用例必须在平台侧运行。

---

## 1. 环境与硬件

- **GPU**：4 × `NVIDIA RTX PRO 5000 72GB Blackwell`，compute capability `sm_120`。
- **驱动**：`580.126.20`（CUDA 13.0）。宿主机 `nvidia-smi -L` 正常。
- **Docker**：`24.0.9`，容器内运行（DinD），仅 `runc`，**无 NVIDIA runtime**。
  - `docker run --gpus all` 被接受但**不会**注入 `/dev/nvidia*` 和 `libcuda`。
  - `--device`、`-v /dev/nvidia*` 返回 `... is not allowed`。
  - 实测：即使 `--gpus all`，容器内 `torch.cuda.is_available() == False`。
- **持久化路径**：`/home/tione/notebook/home/tanshiqian`（及其子目录）。
- **构建方式**：必须用 `docker buildx build --builder default --network=host ...`；
  传统 `docker build` 在 RUN 阶段没有网络（DNS/apt/pip 全失败）。

---

## 2. 新增文件

只新增了一个文件，**未改动 SimPoly 源码**：

- `docker/Dockerfile.tione` —— 基于上游 `docker/Dockerfile` 的 TiOne 适配版。

与上游的主要差异：

1. **基础镜像**：`nvcr.io/nvidia/cuda:13.0.3-{devel,runtime}-ubuntu22.04`
   （Docker Hub 在本机不可达，NGC 可达）。
2. **软件源**：apt 用清华镜像；pip 用腾讯镜像
   `http://mirrors.tencentyun.com/pypi/simple`（trusted-host 同名）。
3. **PyTorch 两阶段安装**：先用 PyTorch 官方 index 安装
   `torch==2.11.0`（解析为 `+cu130` wheel），再根据 `importlib.metadata.requires('torch')`
   把非 torch 的运行时依赖（`cuda-toolkit[...]`、`nvidia-cudnn-cu13` 等大包）
   从腾讯镜像安装，避免走 `download.pytorch.org`（<1 MB/s）。
4. **Kokkos 架构**：默认 `KOKKOS_CUDA_ARCHS=BLACKWELL120`（上游默认 `AMPERE80`）。
5. **运行时增强**：安装 `openssh-server` / `tini` / RDMA 用户态库，并提供
   `/opt/dl/run` 启动脚本（JupyterLab，监听 `0.0.0.0:8888`，`EXPOSE 8888`），
   `ENTRYPOINT ["/usr/bin/tini","-g","--"]`。

---

## 3. 构建镜像

在 **仓库根目录** 执行（`--network=host` 必不可少）：

```bash
docker buildx build --builder default --network=host --progress=plain \
  -f docker/Dockerfile.tione \
  --build-arg KOKKOS_CUDA_ARCHS=BLACKWELL120 \
  -t simpoly:tione .
```

> 由于构建耗时较长，建议后台运行并写日志（本机 bash 超时会杀进程组）：
>
> ```bash
> setsid bash -c 'docker buildx build --builder default --network=host --progress=plain \
>   -f docker/Dockerfile.tione --build-arg KOKKOS_CUDA_ARCHS=BLACKWELL120 \
>   -t simpoly:tione . > /tmp/simpoly_build.log 2>&1; echo EXIT=$? >> /tmp/simpoly_build.log' \
>   < /dev/null > /dev/null 2>&1 & disown
> tail -f /tmp/simpoly_build.log
> ```

**实测耗时**：整轮约 **60 分钟**，其中 conda/pip 环境安装（步骤 `#15`）约 **57 分钟**
（主要是下载 `torch` CPU wheel 530 MB 及若干 CUDA 大包），LAMMPS 编译约 3 分钟。
BuildKit 会缓存分层，重复构建会快很多；**不要加 `--no-cache`**。

构建成功后验证：

```bash
docker images simpoly:tione
# simpoly:tione  <id>  9.85GB

docker run --rm --network=host simpoly:tione bash -lc \
  'python -c "import torch; print(torch.__version__, torch.version.cuda)"'
# 2.11.0+cu130 13.0
```

---

## 4. 运行测试（CPU / 无 GPU）

本机容器内没有 GPU，且 **`test_lammps_mliap.py` 只有 `lmp` 在 PATH 中就会执行**
（它会以 Kokkos GPU 模式启动 LAMMPS，需要 `libcuda.so.1`，在无 GPU 容器中会直接报错）。
因此 CPU 测试要同时 `-m "not gpu"` 并显式 deselect 该文件：

```bash
docker run --rm --network=host simpoly:tione \
  python -m pytest tests/ -m "not gpu" \
  --deselect tests/vivace/test_lammps_mliap.py -v
```

**实测结果**：

```
55 passed, 5 failed, 4 skipped, 10 deselected, 2 warnings in 14.70s
```

- **4 skipped**：2 个 `test_edge_mask.py`（CUDA required）+ 2 个
  `test_empty_equiv_mask.py`（cuequivariance requires CUDA）。
- **10 deselected**：8 个 `@pytest.mark.gpu` 用例 + 2 个 LAMMPS 参数化用例。
- GPU 用例由 `tests/vivace/conftest.py` 的 `pytest_collection_modifyitems`
  在 `torch.cuda.is_available() == False` 时自动跳过。

### 4.1 已知失败（5 个）

| 用例 | 根因 | 归属 |
| --- | --- | --- |
| `test_generation.py::test_simple[PP]` | EMC 二进制报 `Validity has run out` | 外部软件授权过期 |
| `test_generation.py::test_simple[PAN]` | 同上 | 外部软件授权过期 |
| `test_generation.py::test_simple[PCTFE]` | 同上 | 外部软件授权过期 |
| `test_generation.py::test_long_polymer` | 同上 | 外部软件授权过期 |
| `test_vivace.py::test_mliap_save_load` | `torch.fx` deepcopy 抛 `AssertionError: Expected args to be tuple, got immutable_list` | torch 2.11 兼容性 |

**EMC 授权过期**：`emc-pypi==2025.8.21` 内置的
`pyemc/emc/bin/emc_linux_x86_64` 已过期，任何 EMC 调用都会立即返回
`Validity has run out; please download a fresh version.`。这不是环境配置问题，
需要从 EMC 官网重新下载有授权的版本。可用如下命令确认：

```bash
docker run --rm --network=host simpoly:tione bash -lc \
  'B=$(python -c "import pyemc,os;print(os.path.join(os.path.dirname(pyemc.__file__),\"emc\",\"bin\",\"emc_linux_x86_64\"))"); "$B" --version'
# Error: main: Validity has run out; please download a fresh version.
```

**`test_mliap_save_load`**：该用例用 `pytest.importorskip("lammps")` 守护，
上游 CI 未安装 LAMMPS 所以被跳过；本镜像自带 LAMMPS，于是它真正执行。
失败点在 `vivace/deploy.py:69` 的 `copy.deepcopy(model)`，torch 2.11 在深拷贝
FX `GraphModule`（CPU 下 einsum fallback 会构建 FX 图）时触发
`immutable_list` 断言。属于 torch 版本层面的兼容性问题，**与镜像构建无关**，
需要上游修改部署代码或在 CI 中一并启用 LAMMPS 才能暴露。

---

## 5. 运行测试（GPU，需平台侧）

本机 DinD 没有 NVIDIA Container Toolkit，**容器内无法访问 GPU**。
在 TiOne 平台（或任何配置了 `nvidia-container-toolkit` 的机器）上，用同一镜像：

```bash
# 全量测试（含 GPU 与 LAMMPS）
docker run --gpus all --rm --network=host simpoly:tione \
  python -m pytest tests/ -v

# 只跑 GPU 端到端用例
docker run --gpus all --rm --network=host simpoly:tione \
  python -m pytest tests/vivace/ -m gpu -v

# LAMMPS ML-IAP 用例（单/多 GPU，Kokkos）
docker run --gpus all --rm --network=host simpoly:tione \
  python -m pytest tests/vivace/test_lammps_mliap.py -xvvvs
```

GPU 用例清单（8 个）：

- `tests/vivace/test_ase_interface.py::test_ase_calculator_matches_lammps_reference[274]`
- `tests/vivace/test_equivariance.py::test_se3_equivariance[0/1/2]`
- `tests/vivace/test_equivariance.py::test_translation_invariance`
- `tests/vivace/test_vivace.py::test_roundtrip_pickled`
- `tests/vivace/test_vivace.py::test_ase_calculator`
- `tests/vivace/test_vivace.py::test_mliap_save_load_cueq_to_cuda`

LAMMPS 用例（2 个参数）：`test_lammps_mliap[274]`、`test_lammps_mliap[7398]`。

> 注意：README 指出 Vivace 生产推理**必须有 NVIDIA GPU，cuequivariance 内核无
> CPU fallback**。CPU 容器里能通过的用例使用 `use_cuequivariance=False` 的 fallback
> 路径，仅用于冒烟/单元测试，不能代表完整功能。

---

## 6. 复现步骤汇总

```bash
# 0) 进入仓库
cd /home/tione/notebook/home/tanshiqian/github/polymer/tg/simpoly

# 1) 构建（约 1 小时，可复用缓存）
docker buildx build --builder default --network=host --progress=plain \
  -f docker/Dockerfile.tione \
  --build-arg KOKKOS_CUDA_ARCHS=BLACKWELL120 \
  -t simpoly:tione .

# 2) CPU 冒烟测试（预期 55 passed / 5 failed / 4 skipped / 10 deselected）
docker run --rm --network=host simpoly:tione \
  python -m pytest tests/ -m "not gpu" \
  --deselect tests/vivace/test_lammps_mliap.py -v

# 3) GPU / LAMMPS 测试：到 TiOne 平台执行
#    docker run --gpus all --rm --network=host simpoly:tione \
#      python -m pytest tests/ -v
```

### 镜像内关键组件版本

```
Python 3.12.14
torch 2.11.0+cu130        torch-geometric 2.8.0.post1
e3nn 0.6.0                cuequivariance 0.8.1
cuequivariance-torch 0.8.1
cuequivariance-ops-torch-cu13 0.8.1
numpy 2.5.3               ase 3.29.0
mpi4py 4.1.2              emc-pypi 2025.8.21
pytest 9.1.1              lmdb 2.3.0
```

---

## 7. 排错备忘

- **`pip config` 报 127 / 找不到 pip**：CUDA devel 基础镜像在装 miniforge 之前没有 pip，
  所有 `pip config`/`pip install` 必须放在 miniforge 安装之后。
- **构建阶段 RUN 无网络**：务必 `--network=host` 且用 `--builder default`
  （不要用 `docker-container` driver，本机不允许 privileged）。
- **torch 装成了 CPU 版**：`torch==2.11.0` 会同时匹配 `2.11.0`（镜像）和
  `2.11.0+cu130`；用 `--index-url https://download.pytorch.org/whl/cu130`
  配合 `--force-reinstall` 才能拿到 CUDA wheel，构建末尾有断言兜底。
- **`--gpus all` 无效**：本机 DinD 无 NVIDIA Container Toolkit，属平台限制，
  不是镜像问题。
- **`lmp` 报 `libcuda.so.1: cannot open shared object file`**：无 GPU 容器中正常现象；
  要么在 GPU 机器上跑，要么在 CPU 测试里 deselect LAMMPS 用例。
- **EMC `Validity has run out`**：EMC 免费二进制授权到期，需重新获取授权版本。
