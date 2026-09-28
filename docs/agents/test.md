# 检查记录

## 2026-09-28：远端关联与服务器连接记录（计划）

检查范围：确认 `origin` URL、远端默认分支、远端历史和本地工作区同步状态；检查本次只修改的进度文档路径、UTF-8 和 Git whitespace。预期结果：本地 `main` 跟踪 `origin/main` 且无实现差异，服务器连接用途在连接前完成记录。

实际结果：`origin` 为用户提供的 URL，远端默认分支为 `main`；修改前 `git status -sb` 为 `main...origin/main` 且工作区干净。`git diff --check` 无 whitespace 错误（仅提示 Windows 下未来可能转换 LF/CRLF），四份进度文档未发现 Unicode replacement character。检查通过。

## 2026-09-28：服务器首次同步检查（结果）

连接 `Guqq` 后第一项远端操作为 `git -C ~/recursive pull`；命令返回 `No such file or directory`，证明服务器尚无该工作树。未在本次连接执行其他命令或任何计算任务。后续按记录先重试 pull，再 clone。

## 2026-09-28：服务器 clone（结果）

再次连接后首先重试 `git pull`，随后启动从确认的 GitHub remote clone 到 `/home/xmz/recursive`；后续连接确认该目录未保留，因此只有 `Cloning into` 提示不足以证明 clone 成功，本条原结论撤回。未直接编辑服务器受 Git 管理源码，未在登录节点运行计算任务。

## 2026-09-28：更新后服务器同步与资源检查（计划）

检查范围：SSH 会话内 SOCKS 端口；工作树存在时先 pull、不存在时代理 clone；仓库根目录、HEAD、remote URL；Python、GPU、Slurm 和磁盘。预期所有检查均为登录节点轻量操作，不运行模型推理或编译。

提交前文档检查结果：`git diff --check` 无 whitespace 错误，仅有 Windows LF/CRLF 提示；`AGENTS.md` 包含 SOCKS URL、三个代理变量、计算节点网络边界和仓库不存在时 clone 的规则；未发现旧的 `sleep 180` 或“等待 3 分钟后再”流程。通过。

## 2026-09-28：更新后服务器同步与资源检查（结果）

- `git pull` 成功快进至 `b41299f63cdf092270dcbdb60ce2503b8523d677`；仓库根目录为 `/home/xmz/recursive`，origin 为确认的 GitHub URL；
- Python 为 3.10.12，GPU 为 NVIDIA GeForce RTX 5090（32607 MiB，驱动 570.211.01），Slurm 默认分区为 `compute`；
- home 所在根分区容量 1.8 TiB，但仅余约 2.6 GiB，暂不创建环境或下载 checkpoint；
- 全程仅执行 Git 同步和轻量只读检查，未在登录节点运行模型推理或编译。

后续存储检查连接在建立反向转发时返回 `remote port forwarding failed for listen port 1080`，远端命令未执行。本地未发现存活 `ssh` 进程；`ssh -G Guqq` 仍确认 `RemoteForward`、`ExitOnForwardFailure yes` 和 keepalive 配置生效。下一步以禁用新增转发的连接只读检查现有监听，不把本次计作存储检查成功。

禁用新增转发后的首次诊断连接仅返回 `Welcome to Vlab`，30 秒内没有 pull 或 `ss` 输出，未满足诊断预期；将其记录为第二次连续失败，下一次缩短 pull 超时以隔离问题。

## 2026-09-23：`docs/plan/plan_1.md` 数学定义修订

检查范围：Markdown 标题结构、LaTeX display delimiters、代码围栏、UTF-8 内容和已删除章节关键词。

实际结果：

- `\[` 与 `\]` 均为 58 个，数量一致；
- Markdown 代码围栏共 6 个，为偶数；
- 未发现 Unicode replacement character；
- 顶级章节编号连续；
- 未发现原第 10 节“分阶段执行”、原第 11 节“计算资源估算”或旧变量 `num_cycles`。

结论：文档结构检查通过。

## 2026-09-23：`docs/goal/goal_1.md` 创建

检查范围：章节编号、LaTeX display delimiters、代码围栏、UTF-8 内容和遗留变量。

实际结果：

- `\[` 与 `\]` 均为 31 个，数量一致；
- Markdown 代码围栏共 2 个，为偶数；
- 未发现 Unicode replacement character；
- 顶级章节从 1 到 11 连续，子章节编号与父章节一致；
- 未发现旧变量 `num_cycles` 或用户输入中的拼写错误 `adaptatioon`。

结论：目标文档结构检查通过。

## 2026-09-23：norm adaptation 改为输入范数对齐

检查范围：`goal_1.md` 与 `plan_1.md` 的公式配对、UTF-8 内容，以及旧训练集 mean/std adaptation 表述。

实际结果：

- `goal_1.md` 的 `\[` 与 `\]` 均为 32 个；
- `plan_1.md` 的 `\[` 与 `\]` 均为 60 个；
- 两个文件的代码围栏数量均为偶数，未发现 Unicode replacement character；
- 未发现旧的训练集输入/输出 mean/std normalization 公式或配置。

结论：两份文档已经一致改为 per-structure input-norm alignment，检查通过。

## 2026-09-28：Goal 1 范围收紧与论文任务对齐（计划）

检查范围：

- MatterSim、MACE 与 DPA-2 的论文/官方来源是否支持文档中的 checkpoint、任务、数据集、划分和指标描述；
- `goal_1.md` 是否只保留 norm alignment，并明确 backbone `eval()`、冻结语义、同一 irrep 的不同磁分量共享缩放；
- 递归深度是否定义为从小到大的扫描，并保存验证集最佳深度，而不是未定义的可训练控制器；
- 是否删除 equivariant linear adapter、结构自适应深度控制器及相关训练/交付要求；
- Markdown 标题、LaTeX 分隔符、代码围栏、UTF-8、链接和路径是否正确。

预期结果：任务清单均有可追溯的一手来源，文档内部不存在旧范围残留或互相矛盾的完成标准，结构检查全部通过。

实际结果：

- `goal_1.md` 的 `\[` 与 `\]` 均为 26 个，`\(` 与 `\)` 均为 69 个；
- 未发现 tab、Unicode replacement character 或未配对的代码围栏；
- 已删除旧的 equivariant linear adapter、可训练深度控制器和 `5^L` 搜索要求；
- 已明确 backbone eval/冻结语义、按状态类型和 irrep 类型计算 RMS、同一 irrep 的所有 `m` 共享缩放；
- 已明确至少扫描 `K=0,1,2,3,4`，随后由 depth patience、安全阈值和 hard max 停止，并返回所有已观察深度中的验证集最优 `K*`；
- MatterSim 任务与论文的 Matbench phonons 对齐；MACE 任务与论文关联的 97-material ffonons/PhononDB 对齐；DPA-2 任务与论文的 SSE-PBE-D 及 `Domains_SSE-PBE` branch 对齐；
- 官方来源链接均可访问；MatterSim PDF 已下载并用 Poppler 提取、渲染关键页核验；MACE/DPA-2 PDF 直连受本地 TLS/带宽影响，改用出版社 HTML、官方仓库和数据归档交叉核验；
- 本地 ffonons 克隆受网络阻塞未完成，未把残缺目录视为有效数据；正式下载已明确转移到服务器任务数据目录。

结论：Goal 文档内容和格式检查通过；数据下载尚属于下一实现阶段，需按 manifest 和 checksum 流程执行。

## 2026-09-28：通用递归核心实现（计划）

检查范围与预期结果：

- 状态规范能够表达多状态 component、irrep、multiplicity、mask 和边界兼容性；
- norm alignment 对每个结构、状态 component 和 irrep 类型分别计算 RMS，同一 irrep 的 multiplicity 与全部 `m` 共享一个缩放；
- mask/padding 不参与 RMS，零范数通过 epsilon 安全处理；
- 连续段执行器在 `K=0` 时只执行一次原生段，在 `K=1` 时执行一次接缝对齐和第二次原生段；
- 逐层执行器遵守每层独立重复次数；
- 冻结工具强制 `eval()`、关闭参数梯度并能检测参数或 buffer 变化；
- mock backbone 单元测试覆盖 K=0、K=1、多状态、多个 irrep、mask、shape/type 不兼容和序列化配置；
- 静态检查与全部单元测试通过后才进入 MatterSim 集成。

## 2026-09-28：MatterSim 原生推理与 K=1（计划）

检查范围与预期结果：

- 精确记录 MatterSim 版本和 `MatterSim-v1.0.0-1M` checkpoint；
- wrapper 的 K=0 在明确 `atol/rtol` 下复现官方推理；
- wrapper 能取得并回灌完整 atom/edge 动态状态；
- K=1 通过 irrep-level norm alignment 完成第二次计算段执行，输出 shape 正确且无 NaN/Inf；
- backbone 始终为 eval，参数、梯度和 buffer 均未变化；
- 真实推理只通过 Slurm 作业执行并保存作业号、日志、环境和结果摘要。

## 2026-09-28：通用核心与 MatterSim fake-model 集成（结果）

执行命令：`python -m pytest`

实际结果：10 项测试全部通过，用时 2.26 秒。

- 通用状态规范覆盖多 component、irrep layout、mask、batch membership 和不兼容边界；
- norm alignment 按结构、component 和 irrep 类型计算，共享整个 multiplicity/磁量子数打包块的缩放；
- 连续段 K=0/K=1 与逐层执行次数符合定义；
- 冻结、配置往返序列化和 depth early stopping 测试通过；
- MatterSim fake-M3GNet 的 K=0 wrapper 与独立原生 forward 在 `atol=0, rtol=0` 下逐位一致；
- MatterSim K=1 同时携带 atom/edge 状态，各自生成 per-structure scale，输出无 NaN/Inf。

静态检查：`python -m compileall -q src tests` 通过。`ruff` 尚未安装，因此未将其记为通过；真实 MatterSim checkpoint、CUDA、batch 对齐和冻结验收仍须由 Slurm 作业完成。

## 2026-09-28：MatterSim Slurm 验收入口（结果）

执行检查：`python -m pytest`、`python -m compileall -q src tests scripts`，并检查 sbatch 文件包含 GPU 资源请求、虚拟环境激活和 `srun python`。

实际结果：10 项测试全部通过，用时 2.04 秒；Python 编译检查和 Slurm 文件检查通过。真实 checkpoint 验收未在本地执行，等待仓库 Git 同步和服务器连接恢复后提交 Slurm。

## 2026-09-28：同类型 irrep 分组与 MACE wrapper（结果）

执行检查：`python -m pytest`、`python -m compileall -q src tests scripts`，以及 MatterSim/MACE sbatch GPU 资源声明检查。

实际结果：13 项测试全部通过，用时 1.78 秒；编译和 Slurm 文件检查通过。

- 新增不连续 packed 段属于同一 `(ell, parity)` 时联合计算 RMS、共享同一 gamma 的回归测试；
- MACE-MP-0 small L=0 wrapper 的 fake-model K=0 与独立原生前向在 `atol=0, rtol=0` 下逐位一致；
- MACE 全 interaction/product backbone 的 K=1 输出有限，且 node 状态只产生一个 `l=0,p=+1` gamma；
- 真实 MACE-MP-0 small checkpoint 验收脚本通过静态编译，实际 CUDA 运行仍等待 Git 同步后提交 Slurm。
# 2026-09-28：DPA-2 Repformer 递归封装（计划）

检查范围与预期结果：

- 以独立 fake Repformer 的原生前向为基准，`K=0` 必须逐位复现 `g1`、`g2`、`h2`、旋转矩阵和切换权重；
- `K=1` 必须完整重复全部 Repformer 层，且 `g1`、`g2`、`h2` 分别按 `l=0,p=+1`、`l=0,p=+1`、`l=1,p=-1` 对齐；
- padding 邻居不得参与 `g2`/`h2` 的 RMS 统计，输出不得出现 NaN/Inf；
- 临时安装递归前向只在上下文内生效，退出后恢复原生 `forward`；
- 真实 OpenLAM 验收脚本必须锁定 DeePMD-kit `2024Q1` ABI、`Domains_SSE-PBE` head，并检查 K=0 对齐、K=1 有限、eval/frozen 不变性；
- 执行全部单元测试、Python 编译检查以及 Slurm GPU 资源声明检查。

## 2026-09-28：DPA-2 Repformer 递归封装（结果）

执行命令：`python -m pytest -q`、`python -m compileall -q src tests scripts`，并使用 `rg` 检查 DPA-2 sbatch 的 GPU 请求、虚拟环境、checkpoint/head 参数和 `srun` 入口。

实际结果：16 项测试全部通过；Python 编译与 Slurm 声明检查通过。

- fake Repformer 的 `K=0` 对 `g1`、`g2`、`h2`、rotation matrix 和 switching weight 均在 `atol=0, rtol=0` 下逐位一致；
- `K=1` 输出全部有限，诊断分别包含 `g1: l=0,p=1`、`g2: l=0,p=1`、`h2: l=1,p=-1`；
- scoped install 退出后恢复原生 forward；
- 真实 OpenLAM 脚本已经静态编译，显式检查 `_cal_h2g2` 以拒绝错误 DeePMD ABI，并比较 energy/force 的 K=0、K=1、eval/frozen 状态；
- 真实 CUDA/checkpoint 结果仍须在 Git 同步后由 Slurm 作业生成，不能用本地 fake 结果替代。
# 2026-09-28：SSH 会话级反向 SOCKS 转发（计划）

检查范围与预期结果：

- `ssh -G Guqq` 展开配置包含 `RemoteForward 127.0.0.1:1080`、`ExitOnForwardFailure yes` 和 keepalive 设置；
- 建立 `ssh Guqq` 会话时，Guqq 的 `127.0.0.1:1080` 可用且 `curl --proxy socks5h://127.0.0.1:1080` 返回本地公网出口；
- 关闭该 SSH 会话后，相应反向转发随会话停止；
- 本次仅执行轻量网络与配置检查，不在登录节点运行计算负载。

## 2026-09-28：SSH 会话级反向 SOCKS 转发（结果）

- `ssh -G Guqq` 已展开为 `remoteforward [127.0.0.1]:1080 [socks]:0`，且 `exitonforwardfailure yes`、`serveraliveinterval 30`、`serveralivecountmax 3` 均生效；
- 本地 `curl https://api.ipify.org` 返回 `3.1.58.103`，Guqq 通过 `socks5h://127.0.0.1:1080` 返回相同 IP，出口一致性通过；
- 正常会话退出后，使用 `ClearAllForwardings=yes` 的独立检查连接访问 `127.0.0.1:1080` 获得 `Connection refused`，会话回收通过；
- 连接后均先尝试 `git -C ~/recursive pull`，但服务器返回 `/home/xmz/recursive` 不存在；该问题与流量转发无关。
# 2026-09-28：Guqq 代理流程文档修订（计划）

检查范围与预期结果：

- `AGENTS.md` 不再要求执行 `bash net.sh`、`sleep 180` 或固定等待 3 分钟；
- 文档明确本地 `ssh Guqq` 自动建立 `socks5h://127.0.0.1:1080`，且只在 SSH 会话存活期间有效；
- 需联网的 Guqq 登录节点命令有可复制的 `ALL_PROXY`/`HTTP_PROXY`/`HTTPS_PROXY` 用法，DNS 通过 `socks5h` 解析；
- 明确 Slurm 计算节点不能默认访问登录节点回环端口，需单独验证网络路径；
- 执行 Markdown 结构、关键文本、路径和 `git diff --check` 检查。

## 2026-09-28：Guqq 代理流程文档修订（结果）

- 关键文本检查通过：代理 URL、三个代理环境变量、`RemoteForward` 故障检查和 Slurm 计算节点边界均存在；
- 旧的“运行 `bash net.sh` 并等待 3 分钟”强制流程已删除，现明确规定不运行该脚本或固定等待；
- Markdown 代码块和段落结构已通过差异复核；`git diff --check` 通过，仅有现有 Windows 工作树的 LF/CRLF 转换警告，无空白错误。
# 2026-09-28：Guqq SSH 连接故障诊断（计划）

检查范围与预期结果：

- `ssh -G Guqq` 能展开主机、ProxyJump、密钥、RemoteForward 和转发失败策略；
- 用非交互、有限超时的 SSH 连接复现故障，日志能区分跳板机、Guqq 认证、远程命令和反向转发失败；
- 使用 `ClearAllForwardings=yes` 的对照连接判断是否由新增转发配置导致；
- 诊断期间不运行计算任务，不执行 `net.sh`。

## 2026-09-28：Guqq SSH 连接故障诊断（结果）

- `ssh -v` 确认 vlab ProxyJump 公钥认证成功，Guqq 的 `id_ed25519_codex` 公钥认证也成功；
- 连接在请求 `RemoteForward 127.0.0.1:1080` 后返回 `remote port forwarding failed for listen port 1080`，由 `ExitOnForwardFailure yes` 按配置中止；
- `ClearAllForwardings=yes` 对照连接成功，`ss` 显示 Guqq `127.0.0.1:1080` 已处于 `LISTEN`，证明是端口占用而非 SSH 主连接失败；
- 通过已占用的 SOCKS 执行 `curl` 在 15 秒后超时，说明该监听已不能正常代理；
- 本机 `Get-Process -Name ssh` 无输出，本机没有持有该转发的 `ssh.exe`；占用者可能是其他客户端会话或远端残留的 sshd 会话。
# 2026-09-28：Guqq 多连接共享 SOCKS（计划）

检查范围与预期结果：

- `ssh -G Guqq` 展开后保留 `remoteforward [127.0.0.1]:1080 [socks]:0`，且 `exitonforwardfailure no`；
- `AGENTS.md` 明确首个成功绑定 1080 的 SSH 会话持有代理，后续会话即使收到端口占用警告也可正常登录并使用已有代理；
- 文档明确持有代理的会话断开后，已有会话不会自动接管，需新建 `ssh Guqq` 连接恢复代理；
- 执行 SSH 配置展开、关键文本和 `git diff --check` 检查，不连接服务器。

## 2026-09-28：Guqq 多连接共享 SOCKS（结果）

- `ssh -G Guqq` 展开结果为 `exitonforwardfailure no`、`remoteforward [127.0.0.1]:1080 [socks]:0`，keepalive 仍为 30 秒/3 次；
- `AGENTS.md` 关键文本检查通过：首连接持有代理、后续连接继续登录并复用、旧会话不自动接管、新建连接恢复代理和 Slurm 计算节点边界均已记录；
- 本次按计划仅执行本地静态验证，未连接 Guqq。
- `git diff --check` 通过；仅有 Windows 工作树的 LF/CRLF 转换警告，无空白或补丁格式错误。
- 本轮重新读取后再次确认 `ssh -G Guqq` 为 `exitonforwardfailure no`、固定动态反向转发和 30 秒/3 次 keepalive；连续诊断失败的端口语义与成功判据已补充到 `docs/agents/lessons.md`。

## 2026-09-28：多连接继续执行与存储检查（结果）

- 新会话显示 1080 绑定警告后继续执行远端命令，验证 `ExitOnForwardFailure no` 生效；
- 代理 `git pull` 和公网 curl 在有限时间内均无结果，现有 1080 监听不可作为可用代理；
- `ss` 确认 1080 仍仅监听回环；未终止监听或未知会话；
- 唯一持久 ext4 根分区剩余约 2.7 GiB，`~/.cache` 占 152 GiB，`~/recursive` 约 808 KiB；未发现 `/data`、`/scratch`、`/public` 或 `/workspace` 可用挂载；
- 下一步以一次性回环 1081 代理恢复 Git，并通过 Slurm 轻量探针验证 `/dev/shm` 对计算作业的可见性与容量。

## 2026-09-28：Slurm tmpfs 运行时目录接入（计划）

检查范围与预期结果：

- 三个 sbatch 均从 `RECURSIVE_RUNTIME_ROOT` 下的独立环境激活，默认根目录为 `/dev/shm/xmz-recursive`；
- XDG、PyTorch 和 Hugging Face 缓存均指向任务运行时目录，不写入现有 `~/.cache`；
- `.gitignore` 忽略本地 `.venv-*`；
- shell 静态语法、GPU 资源声明、`srun python` 入口、全部 Python 测试和编译检查通过。

## 2026-09-28：Slurm tmpfs 运行时目录接入（结果）

- `python -m pytest -q`：16 项全部通过；pytest 因本地沙箱权限无法写 `.pytest_cache`，只产生 cache warning，不影响测试执行或断言；
- `python -m compileall -q src tests scripts`：通过；
- `bash -n` 检查三个 sbatch：通过；
- 静态检查确认三个作业均请求一张 GPU、使用可配置 runtime root、隔离环境与任务缓存，并通过 `srun python` 启动；
- `git diff --check` 无 whitespace 错误，仅有 Windows LF/CRLF 转换提示。检查通过。

MatterSim 环境首次创建尝试在 shell 解析阶段报 `syntax error near unexpected token mattersim.__version__`；由于 shell 在执行前即拒绝整行，没有创建环境或安装包。本次不计作环境成功，下一次以不含内联 Python 的命令重试。

第二次尝试成功执行 Git pull 和创建 venv，但 pip 报 `Missing dependencies for SOCKS support`，在解析/下载 MatterSim 之前停止。MatterSim 仍未安装；下一次先通过 curl 下载并离线安装纯 Python PySocks wheel，再继续验证。

第三次尝试已从官方 PyPI 文件地址下载并成功安装 `PySocks==1.7.1`；随后 SSH 命令在下载非必要的 pip 升级包时提前结束，未开始 MatterSim 安装。该尝试不计作环境成功；经验已记录到 `lessons.md`，下一次跳过安装器升级。

后续核对显示 pip 已升级到 26.2.1；其通过 SOCKS 解析 PyPI 时抛出 `PoolKey.__new__() got an unexpected keyword argument key_proxy_ssl_context`。MatterSim 仍未下载或安装。下一次对任务专用 tmpfs venv 使用 `venv --clear`，恢复 Python 3.10 自带 pip 22 并离线引导 PySocks。

## 2026-09-28：MatterSim 可安装版本校正（计划）

检查范围：核对官方 GitHub release、PyPI 可用版本和 v1.2.3 对包装器所依赖 M3GNet API；将 optional dependency 从 PyPI 不存在的 1.2.5 校正为 1.2.3；执行全部单元测试、Python 编译和依赖配置静态检查。预期不放宽为无上界版本，保持可复现的精确 pin。

## 2026-09-28：MatterSim 可安装版本校正（结果）

- 官方 v1.2.3 源码仍提供包装器依赖的 `atom_embedding`、`edge_encoder`、`graph_conv`、`final`、`normalizer` 以及相同 MainBlock 调用顺序；
- `pyproject.toml` 和环境文档均精确锁定 `mattersim==1.2.3`，未残留 1.2.5 安装 pin；
- `python -m pytest -q`：16 项通过，仅有本地 `.pytest_cache` 写权限 warning；
- `python -m compileall -q src tests scripts` 和 `git diff --check`：通过。

## 2026-09-28：MatterSim Slurm 环境安装器（计划）

检查范围与预期结果：新增专用 setup sbatch，在计算作业内先验证显式回环 SOCKS 路径，再引导 PySocks、binary-only 安装 MatterSim 1.2.3、editable 安装本项目并执行 `pip check`/导入检查；shell 语法、资源声明和全部本地测试通过。安装日志和 job ID 必须记录，不在登录节点继续运行长 pip 命令。

## 2026-09-28：MatterSim Slurm 环境安装器（结果）

- `python -m pytest -q`：16 项通过，仅有本地 pytest cache 权限 warning；
- Python 编译检查与 setup/inference 两个 sbatch 的 `bash -n`：通过；
- 静态检查确认 setup 作业要求显式代理端口、先执行计算节点公网探针、只安装 binary wheels，并在结束前执行 `pip check` 和版本导入检查；
- `git diff --check` 无 whitespace 错误，仅有 Windows LF/CRLF 提示。可以提交 Slurm 网络探针与环境安装作业。

首次 inline Slurm 网络探针因 `--wrap` 内容跨 Windows/SSH/远端 shell 后被拆分，`sbatch` 报参数缺失；探针和 setup 均未提交。新增 `probe_runtime.sbatch` 后将重新执行 shell 语法与资源检查，并改用固定输出路径验证结果。

固定探针检查结果：16 项单元测试通过（仅 pytest cache warning）；probe/setup 两个 sbatch 的 `bash -n` 通过；探针明确请求一张 GPU、验证 `/dev/shm` 可写、要求显式代理端口并对公网请求设置 15 秒上限；`git diff --check` 通过。可以按文件提交。

Slurm 实际结果：网络探针作业 `490` 在 `node221` 成功，输出显示 `/dev/shm` 可写、约 126 GiB，并经 1081 返回公网出口 `47.130.251.126`。探针通过后提交环境安装作业 `491`；其最终状态和日志待监控。

作业 `491` 结果：失败。日志显示 keeper 退出后 `wandb-0.30.0` wheel 实际 SHA-256 与 PyPI 声明不一致，pip 在安装前拒绝该文件；未把损坏包写入环境。集群 `sacct` storage 未启用，且当前 `squeue` 不接受自定义格式参数；后续使用普通 `squeue -j`、`scontrol show job` 和作业日志验收。

重试准备结果：当前工具持有 keeper 会话 55766；`pip cache remove wandb` 报无匹配项，确认损坏 wheel 未进入 task cache；网络复验作业 `492` 在 node221 再次成功，随后提交 setup 作业 `493`。最终结果待监控。

后续轮询发现 keeper 55766 被 Vlab 主动关闭；因此“纯 `ssh -N` + protocol keepalive”未满足长安装代理持久性要求。下一轮 keeper 增加 20 秒远端应用层心跳，并在启动后立即检查 493。

作业 `493` 结果：`FAILED (ExitCode=1:0)`，运行 1 分 50 秒；日志中的 atomate2 wheel 哈希不匹配发生在心跳 keeper 72062 启动之前，pip 未安装该损坏文件。72062 已连续输出应用层心跳，下一轮才是新 keeper 方案的有效验证。

心跳 keeper 实际重试：定向 cache 检查未发现 atomate2 残留；网络探针作业 `494` 在 node221 成功并返回预期公网出口，随后提交 setup 作业 `495`。最终状态待监控。

keeper 72062 后续仍被 Vlab `Connection reset`，应用层心跳未满足长依赖下载的稳定性要求。按 `lessons.md` 停止代理长下载；下一实现单元验证目标平台 wheelhouse 完整解析、仅含 wheels、哈希清单一致和 Slurm offline install。

作业 `495` 最终结果：`FAILED (ExitCode=1:0)`。代理 keeper 中断后，pip 下载的 torch 2.14.0（约 554.6 MiB）wheel 实际 SHA-256 与索引声明不一致，pip 在安装前拒绝该文件；未把损坏内容安装到环境。短时 keeper 已停止。

## 2026-09-28：MatterSim 离线 wheelhouse（计划）

检查范围与预期结果：

- setup sbatch 支持 `RECURSIVE_WHEELHOUSE`，离线分支强制 `--no-index --find-links`，不执行公网探针；
- 本地为 Linux x86_64 / CPython 3.10 解析 `mattersim==1.2.3` 的完整 binary-only 依赖闭包，并额外包含 PySocks、setuptools 和 wheel；
- wheelhouse 只包含 wheel 与 SHA-256 清单，清单在 scp 前后校验一致；
- Slurm 通过 `venv --clear` 重建任务专用环境，离线安装失败时立即退出，成功时执行 `pip check`、导入版本检查并保存 `pip freeze`；
- 任一 wheel 缺失、哈希不符或依赖不完整都必须使流程失败，不允许回退到源码构建或网络索引。

实际结果：

- `bash -n scripts/slurm/setup_mattersim_env.sbatch`：通过；
- `python -m pytest -q`：16 项通过，仅有现有 `.pytest_cache` 写权限 warning；
- `python -m compileall -q src tests scripts` 与 `git diff --check`：通过，后者仅提示 Windows LF/CRLF 转换；
- `uv run pytest -q` 在同步阶段按预期拒绝把三个隔离 extra 合并到同一环境：MatterSim 要求 `e3nn>=0.5.0`，固定的 MACE 0.3.16 要求 `e3nn==0.4.4`；因此正式验收继续使用三个隔离 venv，本地回归使用现有测试环境；
- `pip download` 为 Linux x86_64 / CPython 3.10 解析得到 144 个 wheel，共 772,031,965 bytes（736.27 MiB），目录中不存在 sdist；
- 使用相同目标平台参数执行 `pip install --dry-run --ignore-installed --no-index --find-links ... --only-binary=:all:` 成功，证明离线依赖闭包完整；
- `SHA256SUMS` 含 144 项，逐文件重新计算结果为 144/144 一致。

结论：本地 wheelhouse 和离线 setup 脚本通过提交前检查，可以进入 Git 同步、scp 与 Slurm 实装阶段。

MatterSim setup 完整性门控补充计划：离线分支在任何 venv 改动前要求 `SHA256SUMS` 存在，兼容 CRLF 并执行全清单 `sha256sum -c`；同时清除继承的大小写代理变量，继续强制 no-index/find-links。检查 Bash 语法、校验顺序、离线变量、16 项回归、编译和 whitespace。

实际结果：Bash 语法通过；静态行序确认 SHA 清单要求、代理清除、no-index 设置和 `sha256sum -c` 均位于 `venv --clear` 之前；16 项 pytest、Python 编译和 `git diff --check` 通过（仅现有 cache 与 LF/CRLF warning）。可以提交，待 144/144 下载完成后运行。

服务器传输首次结果：提交 `bf2c517` 已成功 pull，`/dev/shm` 仍约有 126 GiB 可用；整目录 scp 在约两分钟后返回 `Timeout, server ... not responding` 并关闭，只能视为部分传输，尚未执行服务器端完整 SHA-256 验收。下一次按清单核对后改用短连接分块传输，验收标准保持 144/144 不变。

## 2026-09-28：wheelhouse 断点续传脚本（计划）

检查范围与预期结果：脚本从 `PYPI_URLS` 读取官方 SHA-256、文件名和 URL，兼容 Windows CRLF；已完整 wheel 必须跳过，未完成内容写入 `.partial` 并用 `curl --continue-at -` 续传，仅在单文件哈希通过后原子改名；最终要求条目数为 144 且 `SHA256SUMS` 全部通过。使用本地伪 wheel、CRLF 清单和 `file://` URL 验证首次下载、完整文件跳过、残片续传/失败保护及最终计数，再执行 Bash 语法和 Git whitespace 检查。

实际结果：

- PyPI 官方 JSON 清单生成成功：144/144 文件名唯一匹配，本地 wheel SHA-256 与 PyPI 声明逐项一致；
- `bash -n scripts/download_wheelhouse.sh`：通过；
- 两文件 CRLF 伪清单测试：完整 `a.whl` 被跳过，`b.whl.partial` 从 5 bytes 断点续传并在哈希通过后改名，最终 2/2 校验通过；第二次运行没有下载输出，证明完整文件跳过；
- 无效 `file://` 的预期失败测试返回 curl 37，`.partial` 保留且没有生成最终 wheel，失败保护通过；
- 首次内联 SSH 循环因本地 PowerShell 提前展开远端变量而未执行有效下载，且 CRLF 使直接 `sha256sum -c` 读到带 `\r` 的文件名；该实现已弃用，固定脚本避免多层 quoting 并显式移除清单 CR。

提交前补充结果：`python -m pytest -q` 16 项通过，仅有现有 `.pytest_cache` 写权限 warning；脚本 Bash 语法与 `git diff --check` 通过，后者仅提示 Windows LF/CRLF 转换。

结论：断点续传脚本的本地行为和回归检查符合预期，可以提交并同步到服务器。

服务器首轮脚本实测已完成多个 wheel，并在 botocore 下载遇到 SSL EOF 后保留 `.partial`；原 curl 重试在失效连接上长时间无进展。调整计划：增加 15 秒连接超时、1 KiB/s 持续 30 秒的低速超时和 1 秒重试间隔；重新执行 Bash 语法、两文件 CRLF 续传/跳过测试和预期失败保护，确保只缩短死连接检测，不改变哈希门控。

调整结果：Bash 语法通过；完整两文件再次 2/2 校验且无下载输出；无效 URL 仍返回 curl 37、保留 `.partial` 且不产生最终 wheel；16 项 pytest 全部通过（仅现有 cache warning）；`git diff --check` 通过（仅 LF/CRLF 提示）。可以提交低速超时补丁。

## 2026-09-28：Slurm 直连 wheelhouse 下载（计划）

登录节点无代理 PyPI HEAD 已返回 HTTP/2 200 和 `accept-ranges: bytes`。新增固定 sbatch：要求显式 `RECURSIVE_WHEELHOUSE`，清除所有代理变量，从 `PYPI_URLS` 读取首个 URL 做计算节点直连 HEAD 探针，成功后调用断点续传脚本。检查 sbatch 的 Bash 语法、Slurm 资源、失败前置关系、目标路径参数和完整回归；真实作业固定提交到保存 tmpfs 的 `node221`，直连失败不得改动环境或进入 setup。

实际结果：两个 Bash 脚本语法通过；静态检查确认作业请求 `compute`、1 CPU/2 GiB/1 小时，要求显式 wheelhouse，清除大小写代理变量，直连 HEAD 成功后才调用下载器；16 项 pytest 通过（仅现有 cache warning）；`git diff --check` 通过（仅 LF/CRLF 提示）。可以提交并在 node221 运行真实探针/下载。

真实提交结果：服务器已先 pull 到 `f274bb0`，随后以 `--nodelist=node221` 和显式 wheelhouse 提交作业 `499`；提交成功，最终状态与日志待监控。本次进度文档提交前检查目标为 Markdown 路径/job ID 一致和 `git diff --check` 通过。

作业 `499` 实测约 4 分钟时 botocore 残片为 7,118,848 bytes，证明计算节点直连持续写入但吞吐只有几十 KiB/s；1 小时时限不足以完成 736.27 MiB。调整计划：将 sbatch 时限提高到 12 小时，执行 Bash 语法、资源声明和 whitespace 检查，再尝试用 `scontrol update` 原地延长 499，保留已有进度。

调整检查结果：sbatch Bash 语法通过，静态检查精确匹配 `#SBATCH --time=12:00:00`，`git diff --check` 通过（仅 LF/CRLF 提示）。可以提交并尝试原地延长。

原地延长实际结果：服务器先 pull 到 `c587e5d`，随后 `scontrol update` 返回 `Access/permission denied for job 499`；命令未修改作业。根据已通过的 `.partial` 失败保护/续传测试，下一步取消任务自有的 499 并以 12 小时配置重提；验收新作业必须固定 node221、`TimeLimit=12:00:00` 且复用现有残片。

重提结果：服务器先 pull 到 `0ca4346`，随后成功取消 499 并提交作业 `500`；未删除 wheelhouse 或 `.partial`。新作业的 node、实际时限和续传日志待下一次只读监控核验。

## 2026-09-28：MACE 离线 wheelhouse（计划）

在 MatterSim 作业 500 运行期间，本地为 Linux x86_64 / CPython 3.10 解析 `mace-torch==0.3.16` 的独立依赖闭包，额外包含 PySocks、setuptools 和 wheel；要求 `--only-binary=:all:`，不与 MatterSim 环境合并。预期目录只含 wheel，离线 `--no-index` dry-run 成功，并生成/复验逐文件 SHA-256；若依赖只提供 sdist，应明确失败并审计该依赖，而不是放宽为本地源码编译。

MatterSim 作业 500 验收结果：确认 `node221`、`TimeLimit=12:00:00` 且从 botocore 残片继续；随后在 35/144 的 h5py 下载中，连续四次触发原 1 KiB/s、30 秒低速阈值并失败，完整 wheel 与 h5py `.partial` 均保留。调整计划：生产默认改为 100 次重试、2 小时重试总时长、128 B/s 持续 120 秒的低速阈值；本地失败测试用环境变量缩短重试，继续验证最终文件不会提前生成。

重试调整检查结果：两个 Bash 脚本语法通过；完整两文件仍 2/2 校验且无下载；无效 URL 在测试覆盖为 1 次重试时返回 curl 37，保留 `.partial` 且不生成最终 wheel；16 项 pytest 通过（仅现有 cache warning）；`git diff --check` 通过（仅 LF/CRLF 提示）。可以提交并重提 Slurm 下载。

真实重提结果：短时独立 1081 会话先将服务器 pull 到 `58878e8` 并确认队列无重复下载作业；下一会话再次先 pull，随后成功提交 12 小时续传作业 `501` 到 node221。最终状态待监控。

作业 501 结果：`FAILED (ExitCode=28:0)`，运行 16 秒，日志只有前置 HEAD 的 15 秒连接超时；wheel 循环未启动，完整数仍为 35。调整计划：前置 HEAD 增加 20 次、总计最多 10 分钟的有限重试，每次连接 15 秒、请求 60 秒；保持探针成功才调用下载器。执行 Bash 语法、重试参数静态检查和完整本地回归后再重提。

调整检查结果：两个 Bash 脚本语法通过；静态检查精确确认探针 `--retry 20`、`--retry-max-time 600`、`--connect-timeout 15` 和 `--max-time 60`；16 项 pytest 通过（仅现有 cache warning）；`git diff --check` 通过（仅 LF/CRLF 提示）。可以提交并重提。

真实重提结果：短时独立 1081 会话先将服务器 pull 到 `f3f3d56`，随后成功提交 12 小时作业 `502` 到 node221；最终状态待监控。

MACE 实际结果：首次 binary-only 解析严格失败在没有 PyPI wheel 的 `python-hostlist`。官方 2.3.0 sdist SHA-256 为 `e1a0b18e525a5fca573cb9862799f11b3f2bd3ba7aec70c4ecd8b95341bb71ea`；内容审计仅发现 Python 模块、脚本、测试、manpage 和 setuptools 配置，无本地扩展源码。单独构建的纯 Python wheel 为 `python_hostlist-2.3.0-py3-none-any.whl`，SHA-256 为 `88710a4a83c8ea58a81e5526897b1415427c634c75a6a6253d1e163ec6f4ebb9`。

加入该审计 wheel 后，目标平台解析得到 49 个 wheel、637.90 MiB；离线 `--no-index --only-binary` dry-run 成功。48 个 PyPI wheel 的文件名与官方 SHA-256 逐项匹配，完整 `SHA256SUMS` 49/49 复验通过；自建 wheel后续单独 scp，不伪造 PyPI URL。

## 2026-09-28：MACE 离线环境安装器（计划）

新增独立 `setup_mace_env.sbatch`：只接受显式 wheelhouse，强制 `PIP_NO_INDEX`/`--no-index --find-links` 和 binary-only 安装；可安全 `venv --clear` 重建严格位于任务运行时根的 MACE 环境；安装 `mace-torch==0.3.16` 与本项目后执行 `pip check`、MACE/e3nn/torch 版本导入检查并保存 freeze。预期与 MatterSim 环境完全隔离，缺少审计 wheel或任一依赖时立即失败。检查 Bash 语法、路径安全、无网络索引、版本 pin、完整回归和 whitespace。

实际结果：Bash 语法通过；静态检查确认安装前完整 SHA-256 校验、强制 no-index/find-links、binary-only MACE pin、安全 `venv --clear`、`pip check`、版本导入与 `mace-freeze.txt`；16 项 pytest 和 Python 编译通过（仅现有 cache warning）；`git diff --check` 通过（仅 LF/CRLF 提示）。可以提交，待服务器 wheelhouse 完整后运行。

MACE 控制文件 staging 计划：服务器连接先 pull，再创建任务 tmpfs 目录；只传 48 项官方 URL 清单、49 项总哈希清单和 39 KiB 审计 wheel。传输后核对清单行数和审计 wheel SHA-256；不提交 MACE 下载作业，保持 MatterSim 502 独占计算节点公网。

staging 结果：服务器先 pull 到 `0709315` 并创建任务目录；短 scp 成功。服务器端 `wc -l` 为 `PYPI_URLS=48`、`SHA256SUMS=49`，审计 wheel SHA-256 校验 `OK`。未提交 MACE 下载作业；同期 MatterSim 502 仍 RUNNING，已推进到 `m` 开头的依赖。
