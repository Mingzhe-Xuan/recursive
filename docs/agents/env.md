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

## 2026-11-02T01:09+08:00：CGCNN seed 123 专用环境（创建计划）

- 实测基础 Python 3.10.12；用户只读包包含 torch 2.8.0+cu128、numpy 2.2.6、pymatgen 2025.10.7、matplotlib 3.10.3，GPU 为 RTX 5090、驱动 570.211.01。
- 任务 venv 拟建于 /home/xmz/recursive/outputs/self_evolution/runtime/cgcnn-seed123/venv，先执行 python3 -m venv --system-site-packages；继承已安装 torch 以避免重复下载 CUDA 闭包，但不修改用户目录包。
- 仅在 venv 内安装覆盖：numpy==1.26.4、pymatgen==2024.5.1、matplotlib==3.9.4、pytest==8.3.5。若缺少 PySocks，先通过 curl 获取官方 1.7.1 wheel，SHA-256 2725bd0a9925919b9b51739eea5f9e2bae91e83288108a9ad338b2e3a4435ee5，离线引导。
- scripts/slurm/self_evolution/setup.sbatch 在 Slurm 中创建环境、安装、记录有效 sys.path/用户包继承状态、完整 pip freeze、CUDA 短检查及测试。正式计算只使用该 venv；pip 配置要求处于 venv，源码 editable install 使用 --no-deps，避免改动共享 torch。
- 工作目录 outputs/self_evolution/jarvis2021-seed123，完整模型链与缓存存于持久根盘，不只保存在 /dev/shm。实际安装与网络结果在后续记录，不把计划记作成功。

- 2026-11-02T01:19+08:00：setup 878 的在线网络探针失败，未产生 SETUP_COMPLETE。新增 CGCNN_WHEELHOUSE 完全离线安装分支，传输目录为任务 runtime/cgcnn-bootstrap，10 项 wheel 包括原固定 NumPy/pymatgen/matplotlib 及 pytest 的 Python3.10 补充依赖；不替换已共享 torch，不降低固定版本或验收要求。

- 2026-11-02T01:24+08:00：正式训练前修订最终环境协议，使用服务器已安装的 numpy==2.2.6、pymatgen==2025.10.7、matplotlib==3.10.3，torch==2.8.0+cu128 仍只读继承；专用 venv 仅补 pytest==8.3.5 及必要纯 Python依赖。原因是 32 MB SCP 也被跳板中断，而上述材料库组合本已存在，CGCNN 无旧版本硬约束。新版环境必须通过相同 GPU、原生数值和缓存链测试，不能以继承成功替代验收。精简离线目录改为 runtime/cgcnn-inherited-bootstrap（6 wheel/466,401 bytes），旧部分传输目录保留未使用。

- 2026-11-02T01:33+08:00：Slurm879环境GPU与8项集成测试通过；实际材料库精确版本已核实。发现venv默认旧setuptools将editable元数据记为UNKNOWN，新增任务venv内setuptools==70.2.0/wheel==0.45.1覆盖，并新增项目metadata 0.1.0断言。离线bootstrap现8个wheel；此修复不更改模型、数据或训练预算。

- 2026-11-02T02:12+08:00：888最终环境真实验收成功：Python3.10.12、torch2.8.0+cu128、CUDA12.8/RTX5090、numpy2.2.6、pymatgen2025.10.7、matplotlib3.10.3、pytest8.3.5、setuptools70.2.0、wheel0.45.1，项目metadata recursive-atomistic-backbones0.1.0，12项测试通过。正式work_root=/home/xmz/recursive/outputs/self_evolution/jarvis2021-seed123-final；完整图数据hash85da743bbe3ef70e6c429af2b7d026b20a375dac665a8d0485a4725e282ec376，891之前的实际pilot为890。

- 2026-11-02T23:37:27+08:00：本次独立残差验证复用现有/home/xmz/recursive/outputs/self_evolution/runtime/cgcnn-seed123/venv，不创建新环境、不安装/更改依赖。服务器Python3.10.12/Torch2.8.0+cu128/numpy2.2.6/pymatgen2025.10.7/matplotlib3.10.3/pytest8.3.5，以Slurm环境检查为准；src通过入口sys.path访问新包。本地Python3.12/Torch2.11 CPU仅做回归，不能替代真实CUDA验收。

## 2026-11-03T10:45:30+08:00 iComformer环境复用审计

服务器基础环境已实测：Python3.10.12、torch2.8.0+cu128、torch-geometric2.6.1、torch-scatter2.1.2+pt28cu128、jarvis-tools2026.4.2、numpy2.2.6、scipy1.15.3、pymatgen2025.10.7、matplotlib3.10.3。现有/home/xmz/recursive/outputs/self_evolution/runtime/cgcnn-seed123/venv先前已由python3 -m venv --system-site-packages创建并安装pytest8.3.5等，完整旧创建/安装记录见上文；本任务只读复用它，不安装/升级任何依赖，也不改变系统或旧venv。

iComformer AST源加载仅执行不变分支，所需PyG/scatter/Jarvis均已存在，未用的eComformer e3nn/torch_sparse和旧pydantic settings依赖不参与加载。正式Slurm check会强制核对核心版本、真实导入ABI、原生CPU单元，并保存pip freeze；后续GPU验收仍必须通过，不能凭metadata认定CUDA可用。本地真实单元环境为Python3.12/Torch2.11 CPU、PyG2.7、scatter2.1.2+pt211cpu、Jarvis2025.5.30，与服务器不同，不能替代服务器验收。

官方README的Jarvis2022.9.16/PyTorch CUDA11.6环境与本次现代固定运行时不同，差异显式保留；目标是官方不变模型与周期几何在统一研究协议下的递归比较，不宣称逐字论文环境/划分/训练配置复现。

## 2026-11-03T10:58:28+08:00 iComformer独立venv修订（配置前计划）

Slurm907发现metadata jarvis-tools2026.4.2存在，但实际jarvis/__init__.py来自同名旧Python2包，import失败；908被afterok门禁阻止，没有构图。不能只凭distribution metadata复用环境。调整为先python3 -m venv --system-site-packages /home/xmz/recursive/outputs/icomformer_scaling/runtime/seed123/venv，再在该venv安装独立jarvis-tools2026.4.2（遮蔽错误namespace）与pytest8.3.5/setuptools70.2.0/wheel0.45.1及纯Python必要bootstrap依赖。共享Torch2.8.0+cu128/PyG2.6.1/scatter2.1.2+pt28cu128/numpy2.2.6只读继承，不修改旧venv或用户site包。

包通过官方PyPI精确wheel URL/SHA清单下载到新runtime/wheelhouse，网络下载仅登录节点显式SOCKS；安装由Slurm CPU check使用--no-index --no-deps离线安装，禁止resolver替换共享Torch。完整pip freeze、实际jarvis模块路径与版本均记录，模块路径必须位于新venv内。未用e3nn/torch_sparse不安装。下载/创建venv是轻量许可，测试/所有构图/模型负载仍Slurm。

- 2026-11-03T12:04:38+08:00：911实际环境：独立venv Torch2.8.0+cu128/PyG2.6.1/scatter2.1.2+pt28cu128/Jarvis2026.4.2，RTX5090总显存33,679,736,832bytes。最大图批64 OOM；批32（2782原子、155898边）float32原生/投影前后向和Adam通过，最高reserved27,216,838,656bytes/allocated25,239,337,984bytes。锁定batch32，保守并发1。
