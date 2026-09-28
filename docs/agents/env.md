# 环境记录

## 本地轻量测试环境

- 用途：通用递归逻辑和 fake-backbone 单元测试，不运行真实模型推理。
- Python：当前工作区解释器（要求 Python 3.10 或更高）。
- 项目依赖：`torch>=2.1`；开发依赖为 `pytest>=8`、`ruff>=0.6`。
- 可复现入口：`python -m pytest -q` 和 `python -m compileall -q src tests scripts`。

## 服务器 MatterSim 环境（待创建）

- 路径：项目根目录 `.venv-mattersim`。
- Python：3.10 或 3.11。
- 项目安装：editable install，extra 为 `mattersim`，锁定 `mattersim==1.2.5`。
- 所有真实推理均由 `scripts/slurm/mattersim_k01.sbatch` 提交。

## 服务器 MACE 环境（待创建）

- 路径：项目根目录 `.venv-mace`。
- Python：3.10 或 3.11。
- 项目安装：editable install，extra 为 `mace`，锁定 `mace-torch==0.3.16`。
- 所有真实推理均由 `scripts/slurm/mace_k01.sbatch` 提交。

## 服务器 DPA-2 / OpenLAM 环境（待创建）

- 路径：项目根目录 `.venv-dpa2`。
- Python：以 DeePMD-kit `2024Q1` 分支支持的版本为准，优先 3.10。
- DeePMD-kit 必须从官方仓库的精确 ref `2024Q1` 安装；不能用当前 PyPI 版本替代，因为 Repformer 私有 ABI 已发生变化（本实现需要 `_cal_h2g2`）。
- 官方 2024Q1 使用说明锁定 `torch==2.0.0`、`torchvision==0.15.1`、`torchaudio==2.0.1`，随后安装 `git+https://github.com/deepmodeling/deepmd-kit@2024Q1`；服务器创建环境时使用与驱动兼容的官方 CUDA wheel，并在本节追加实际索引、完整命令与 `python -m pip freeze` 摘要。
- checkpoint 为 `OpenLAM_2.1.0_27heads_2024Q1.pt`，验证 head 为 `Domains_SSE-PBE`。
- 所有真实推理均由 `scripts/slurm/dpa2_k01.sbatch` 提交。

以上三个服务器环境尚未创建。Git 同步条件已经满足；当前需先解决服务器根分区剩余空间不足的问题，再选择安全的任务存储路径。

## 服务器基础环境实测（2026-09-28）

- 工作树：`/home/xmz/recursive`，已同步到 `b41299f`；
- 系统 Python：3.10.12，路径 `/usr/bin/python3`；
- GPU：NVIDIA GeForce RTX 5090，32607 MiB，驱动 570.211.01；
- Slurm GPU 分区：`compute`；
- `/` 当前仅余约 2.6 GiB，因此尚未创建任何虚拟环境。需先找到容量足够的任务存储位置，再追加真实环境路径、安装命令和版本清单。

## Slurm 运行时目录决策（2026-09-28）

- 轻量探针作业 `489` 在 `node221` 验证 `/dev/shm` 可写，容量约 126 GiB；
- 统一运行时根目录定为 `/dev/shm/xmz-recursive`，环境放在 `envs/{mattersim,mace,dpa2}`，缓存放在 `cache/`，checkpoint 放在 `checkpoints/`；
- 该目录是节点本地 tmpfs，不视为持久存储。环境和 checkpoint 必须可由文档中的命令重建；小型 JSON/日志结果仍写回项目 `results/` 并由 scp 拉回本地；
- sbatch 允许通过 `RECURSIVE_RUNTIME_ROOT` 覆盖默认值，但提交前必须验证目标计算节点可见同一路径。
