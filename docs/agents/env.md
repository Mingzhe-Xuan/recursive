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

以上三个服务器环境尚未创建。原因是当前本地目录没有 Git 元数据，服务器也没有对应工作树；按照服务器源码只能经 Git 同步的规范，需先取得正确 remote URL。
