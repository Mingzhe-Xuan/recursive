# 环境记录

## 本地轻量测试环境

- 用途：通用递归逻辑和 fake-backbone 单元测试，不运行真实模型推理。
- Python：当前工作区解释器（要求 Python 3.10 或更高）。
- 项目依赖：`torch>=2.1`；开发依赖为 `pytest>=8`、`ruff>=0.6`。
- 可复现入口：`python -m pytest -q` 和 `python -m compileall -q src tests scripts`。

## 服务器 MatterSim 环境（待创建）

- 路径：项目根目录 `.venv-mattersim`。
- Python：3.10 或 3.11。
- 项目安装：editable install，extra 为 `mattersim`，锁定 PyPI 可安装版本 `mattersim==1.2.3`。官方 GitHub 虽已有 v1.2.4/v1.2.5 tag，但 PyPI 当前只发布至 1.2.3；v1.2.3 的 M3GNet `atom_embedding`、`edge_encoder`、`graph_conv`、`final` 和 `normalizer` API 已与包装器逐项核对。
- 所有真实推理均由 `scripts/slurm/mattersim_k01.sbatch` 提交。

## 服务器 MACE 环境（待创建）

- 路径：项目根目录 `.venv-mace`。
- Python：3.10 或 3.11。
- 项目安装：editable install，extra 为 `mace`，锁定 `mace-torch==0.3.16`。
- 所有真实推理均由 `scripts/slurm/mace_k01.sbatch` 提交。

本地离线解析结果：Linux x86_64 / CPython 3.10 闭包为 49 个 wheel（637.90 MiB），核心版本含 `mace-torch==0.3.16`、`e3nn==0.4.4`、`torch==2.14.0`、`numpy==2.2.6`。`python-hostlist==2.3.0` 在 PyPI 仅有 sdist；审计确认无本地扩展后单独构建 `py3-none-any` wheel，sdist SHA-256 为 `e1a0b18e525a5fca573cb9862799f11b3f2bd3ba7aec70c4ecd8b95341bb71ea`，wheel SHA-256 为 `88710a4a83c8ea58a81e5526897b1415427c634c75a6a6253d1e163ec6f4ebb9`。48 个官方 wheel 与 PyPI 哈希匹配，完整清单 49/49 通过；服务器环境必须完全离线安装该固定闭包。

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

MatterSim 环境由 `scripts/slurm/setup_mattersim_env.sbatch` 创建。在线模式显式设置 `RECURSIVE_PROXY_PORT`，先通过 SOCKS curl 验证计算节点网络路径；离线模式显式设置 `RECURSIVE_WHEELHOUSE=/dev/shm/xmz-recursive/wheelhouse/mattersim`，并通过 `PIP_NO_INDEX=1`、`--no-index --find-links` 禁止访问索引。正式安装使用离线模式和 `RECURSIVE_RECREATE_ENV=1`，以 `venv --clear` 重建任务专用环境；wheelhouse 必须包含 MatterSim 依赖闭包、`PySocks==1.7.1`、`setuptools>=69` 和 `wheel`。安装成功后将完整 `pip freeze` 写入 `/dev/shm/xmz-recursive/manifests/mattersim-freeze.txt`。

MatterSim 1M checkpoint 由 `scripts/slurm/download_mattersim_checkpoint.sbatch` 在目标计算节点下载到 `${RECURSIVE_RUNTIME_ROOT}/checkpoints/mattersim/mattersim-v1.0.0-1M.pth`；脚本使用 `.partial` 断点续传并在成功后原子改名，随后输出文件大小和 SHA-256。不得给真实验收脚本传官方别名，因为 MatterSim 1.2.3 会把别名下载硬编码到 `~/.local/mattersim/pretrained_models`。`mattersim_k01.sbatch` 默认读取上述任务路径，也可用 `MATTERSIM_CHECKPOINT` 显式覆盖。

本地解析结果：以 Linux x86_64、CPython 3.10、ABI `cp310` 和 binary-only 约束解析出 144 个 wheel（772,031,965 bytes）。核心选择包括 `mattersim==1.2.3`、`torch==2.14.0`、`e3nn==0.6.0`、`numpy==2.2.6`、`setuptools==84.0.0`、`wheel==0.48.0` 和 `PySocks==1.7.1`；完整版本以后续服务器生成的 `mattersim-freeze.txt` 为准。本地 `--no-index` dry-run 与 `SHA256SUMS` 144/144 校验均通过。
