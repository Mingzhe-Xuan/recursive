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

## 2026-09-28：跨 wheelhouse 哈希播种（计划）

新增通用脚本，以目标 `SHA256SUMS` 为准扫描源 wheelhouse；仅当目标缺失、文件名安全、源文件存在且 SHA-256 精确匹配时创建硬链接。目标已存在且哈希正确时跳过，存在但哈希错误时失败，不覆盖；源/目标跨文件系统导致硬链接失败时也失败，不静默复制。用微型 CRLF 清单测试匹配播种、已存在跳过、非匹配忽略和错误目标保护；再执行 Bash 语法、完整回归和 whitespace 检查。

实际结果：Bash 语法通过；CRLF 微型清单输出 `seeded=1 existing=1`，匹配项完成播种、正确既有项跳过、非匹配项保持缺失；`fsutil hardlink list` 确认源与目标是同一硬链接；预置错误目标时脚本以状态 1 退出且未覆盖文件。提交前将文件名约束收紧为以字母或数字开头、以 `.whl` 结尾的安全字符集，并增加 `..` 路径逃逸清单拒绝测试。完整 `pytest` 为 16 项通过（仅现有 cache warning），Python 编译与 `git diff --check` 通过（仅 LF/CRLF 提示）。

## 2026-09-28：MatterSim checkpoint 任务目录下载（计划）

官方 1.2.3 wheel 审计确认 checkpoint 别名会硬编码写入 `~/.local/mattersim/pretrained_models`，且官方下载函数没有断点续传或原子落盘。新增 node-local Slurm 下载入口，将官方 GitHub raw 资源写入 `${RECURSIVE_RUNTIME_ROOT}/checkpoints/mattersim`：完整文件存在时跳过，下载写入 `.partial`、支持续传，成功后原子改名并输出大小与 SHA-256。K=0/K=1 作业改为要求显式 `MATTERSIM_CHECKPOINT` 或使用该任务目录默认路径，验证脚本收到实际文件路径。检查两个 sbatch 的 Bash 语法、URL/路径/原子语义、README 与环境文档一致性、16 项回归、Python 编译和 whitespace。

实际结果：两个 sbatch 的 Bash 语法通过；静态检查确认官方 URL、任务 checkpoint 目录、`.partial`、`--continue-at -`、成功后 `mv`、大小/SHA-256 输出，以及 K=0/K=1 的显式文件路径均存在。README 和环境文档已改为 node-local 布局，不再指示 `.venv-mattersim` 或 checkpoint 别名。16 项 pytest 通过（仅现有 cache warning），Python 编译与 `git diff --check` 通过（仅 LF/CRLF 提示）。

## 2026-09-29：作业 507 续监控连接记录（实际）

仅修改服务器连接用途文档。`git diff --check -- docs/agents/gpu.md` 通过（仅现有 LF/CRLF 转换提示）；记录明确要求登录后先执行显式 1080 代理的 `git pull`，随后只读监控 507，不并发启动 MACE 下载或登录节点计算。

作业实测记录检查：`squeue` 与 `scontrol` 一致显示 507 在 node221 为 RUNNING、`TimeLimit=12:00:00`；文件检查显示 125 个完整 wheel 和 343,851,008-byte 的 `torch-2.14.0` 残片。更新 `gpu.md`、`state.md`、`update.md` 后，定向 `git diff --check` 通过（仅现有 LF/CRLF 转换提示）。

## 2026-09-29：论文数据 manifest 与校验下载器（计划）

先为 MatterSim 主任务建立 `matbench_phonons` 的版本化 JSON manifest，记录官方直链、文件名、1265 条样本、目标名/单位和 matminer 官方 SHA-256；数据文件本身继续由 `.gitignore` 排除。新增仅依赖 Python 标准库的通用 manifest 下载器，要求：拒绝不安全文件名和未知/缺失字段；正确文件跳过；下载写入 `.partial`；HTTP Range 受支持时续传、不支持时安全覆盖；SHA-256 通过后原子改名；错误哈希不得生成最终文件。测试覆盖本地 HTTP 服务器下的全新下载、正确既有文件、断点续传、忽略 Range 的覆盖路径、错误哈希和路径逃逸；再执行全套 pytest、Python 编译、manifest 内容断言与 whitespace 检查。

实际结果：`uv run pytest` 在执行前正确发现 MatterSim 与 MACE extras 的 e3nn 约束互斥，因此未用混合环境；仓库 `.venv` 没有 pytest，改用已有 pytest/torch 的系统 Python，并把 `--basetemp` 限定到工作区 `tmp`，避免系统临时目录权限问题。最终 21 项测试全部通过（16 项原有 + 5 项下载器；仅旧 `.pytest_cache` 不可写警告）。Python 编译、100 字符行宽检查、manifest 的样本数/目标/单位/SHA-256 断言和 `git diff --check` 均通过。系统环境没有 ruff，因此没有把不可用 lint 伪记为成功；计划内验收项均已完成。

## 2026-09-29：MACE PhononDB 97 材料 manifest（计划）

以 MACE-MP 论文关联的 `janosh/ffonons` 为一手实现来源，固定提交 `480bc92d6719962b584c98e8bce4ffa1c2d74031`。manifest 记录该提交中的摘要与 MP↔Togo 映射原始文件、精确 SHA-256、97 个论文图对应的唯一 MP ID→Togo ID 映射、PhononDB 官方下载 URL 模板、0.01 THz 虚频容差和评测字段。检查要求：映射恰为 97 且键值唯一；所有 97 项同时存在于 PBE 摘要且 supercell 非空；97 个 URL 均可由模板确定；两项 ffonons artifact 可被通用下载器解析；来源文件哈希、JSON 格式和 whitespace 通过。数据 ZIP 后续在服务器下载后补充逐文件本地 SHA-256，不在首次下载前虚构官方 checksum。

实际结果：稀疏克隆的 ffonons 提交为 `480bc92d6719962b584c98e8bce4ffa1c2d74031`；论文图目录恰有 97 个唯一 MP ID，manifest 的 97 个键和 97 个唯一 Togo ID 与其完全一致。压缩摘要对 97 项均有 PBE 行且 supercell 全部非空；摘要和映射文件的实际 SHA-256 与 manifest 两项 artifact 完全一致。通用 loader 接受该 manifest，完整测试为 22 项通过（仅旧 `.pytest_cache` 不可写警告），Python 编译、100 字符行宽与 `git diff --check` 通过。

## 2026-09-29：MatterSim Linux CUDA 闭包修复（计划）

真实离线 setup 509 暴露本地 Windows 跨平台解析遗漏 Linux 条件依赖，并且自动选择的 torch 2.14.0 精确要求尚未在 PyPI 发布的 `nvidia-nccl-cu13==2.30.7`。改为显式固定已完成 PyPI dry-run 的稳定组合：torch 2.8.0、torchvision 0.23.0、torchaudio 2.8.0、CUDA 12.8 的 14 个 NVIDIA wheel和 triton 3.4.0；该版本线支持 RTX 5090/Blackwell。补齐 18 个新 wheel 的官方 URL/SHA-256，保留已验证的通用依赖但 setup 必须显式安装三项 torch pin，避免 resolver 回选 2.14。验收包括：完整 Linux/CPython 3.10 离线 dry-run；所有 URL 与 PyPI 官方 SHA-256 对应；全清单逐项哈希；setup Bash/静态 pin/无索引检查；22 项 pytest、Python 编译和 whitespace。失败的 509 不因修复而删除日志或降低离线要求。

实际结果：从 PyPI PEP 658 元数据固定 18 个新增 wheel 的官方 URL 与 SHA-256，本地清单现为 162 项、文件名无重复，逐文件重新计算 SHA-256 为 162/162 一致。显式加入 torch 2.8.0 所有 14 个 CUDA 12.8 条件依赖与 triton 3.4.0 后，Linux x86_64 / CPython 3.10 的 `--no-index --only-binary` dry-run 成功；首次检查遗漏 `manylinux_2_27` 平台标签而按预期拒绝 cuDNN，补齐与实际 wheel 一致的 2.28/2.27/2014/2.17/2010/2.12 标签后完整闭包通过。setup 已显式固定 MatterSim 与三项 torch 版本，并在 `pip check` 后精确断言安装版本。22 项 pytest 全部通过（仅旧 `.pytest_cache` 不可写警告），Python 编译、Bash 语法和 `git diff --check` 通过（后者仅 LF/CRLF 提示）。可以提交并在服务器通过 Slurm 增量获取新增 18 项后进行真实离线安装。

版本化清单补充计划：将 162 项 `PYPI_URLS` 与 `SHA256SUMS` 作为小型文本元数据放入 `data/manifests/mattersim_wheelhouse_cp310_linux/`，wheel 二进制本身继续忽略。要求目录 README 明确目标平台、顶层 pin、格式和更新流程；两个清单均为 162 个唯一安全文件名、文件名集合及哈希逐项一致，URL 仅使用 HTTPS PyPI 文件域；再执行完整本地 wheel 哈希复验、22 项回归、Python 编译与 whitespace 检查。

版本化清单实际结果：`PYPI_URLS` 与 `SHA256SUMS` 均为 162 行，文件名各自唯一且集合/逐项哈希完全一致；文件名安全规则和 `https://files.pythonhosted.org/` 域名检查通过，162 个本地 wheel 的实际 SHA-256 全部匹配。模块 README 已记录目标平台、四项顶层 pin、双清单格式、Slurm staging/下载命令和更新约束。22 项 pytest、Python 编译、README 100 字符行宽与 `git diff --check` 通过（仅旧 cache 与 LF/CRLF 提示）。

## 2026-09-29：DPA-2 Zenodo 数据 manifest（计划）

以 Zenodo 官方 API 的固定记录 `10461723` 为准，为 `data-v1.3.tgz` 建立版本化 manifest，记录 DOI、发布日期、精确字节数 `17073396886`、官方 MD5 `789bedf203d673bdc95a09b582d83823`、DeePMD 数据格式、SSE-PBE-D 选择目标和归档内 train/test split 责任。由于 Zenodo 只发布 MD5，扩展通用原子下载器以安全支持 manifest 中恰好一个 `sha256` 或 `md5`，不伪造 SHA-256；最终下载后可另记本地 SHA-256。测试覆盖 MD5 下载/既有文件、错误 MD5 不发布、同时或完全不提供受支持 checksum 时拒绝；保留全部 SHA-256 回归，再执行完整 pytest、编译、JSON/元数据、行宽和 whitespace 检查。17 GB 归档仅在服务器任务数据目录由 Slurm 下载，本地不取大文件。

实际结果：Zenodo 官方 API 返回记录 10461723、发布日期 2024-01-06、`data-v1.3.tgz` 大小 17,073,396,886 bytes 和 MD5 `789bedf203d673bdc95a09b582d83823`，均已逐项固定到 manifest；只选择包含上游/下游数据与 split 的数据归档，不把非必需的 267 MB code/model archive 加入自动下载。下载器保持 schema 1 兼容，要求每个 artifact 恰有一个受支持 checksum，并按所选算法验证既有文件、partial 和原子发布。首次回归仅因 SHA-256 错误消息少了连字符而失败，恢复既有 `SHA-256` 文案后 27 项测试全部通过；Python 编译、官方元数据断言、JSON、100 字符行宽与 `git diff --check` 通过（仅旧 cache 与 LF/CRLF 提示）。

## 2026-11-02 00:35 +08:00：Sequential Self-Evolution 计划文档（检查计划）

本单元仅修改文档。检查新增计划的 UTF-8、Markdown 标题/围栏/数学环境、现有相对链接与计划目录树一致性；检查三个 backbone、全任务清单、线性投影、缓存链、固定数据划分、训练预算对照、MAE 曲线和 Slurm 约束均有明确说明。新模块与接口须标注为拟实现。确认 state.md 既有变更历史逐字保留，执行 git diff --check；不运行模型或把历史 27 项测试记为本轮通过。预期全部文档检查通过。

实际结果（2026-11-02 00:41 +08:00）：新增计划为 UTF-8、384 行、21,959 bytes；12 个二级章节、Markdown 围栏和数学环境成对，8 个相对链接均指向既有文件，6 项外部参考 URL 格式有效。三 backbone、29 项历史任务及新版字段审计、全库缓存、线性投影、历史链、固定划分、默认轮数/seed、预算对照与 Slurm 内容检查通过。state.md 的既有变更历史及 test/update/lessons 原文前缀保留检查通过。git diff --check 通过，仅现有 LF/CRLF 提示；新增未跟踪计划另行检查无行尾空白。官方 GitHub 入口已核对；Nature 链接本轮抓取遇到站点认证重定向，任务表依据此前已读取的官方论文信息，本轮不将其记为重新抓取成功。PowerShell 中文管道的新增记录曾出现问号，已修复并复验。仅文档变更，不运行单元测试或模型，不提交服务器任务。

## 2026-11-02T00:45+08:00：CGCNN 单 seed 实施单元 1（测试计划）

范围：官方代码 pin 与原生 CGCNN 数值一致性；数据标签过滤、零值保留、唯一 ID、确定性划分和重复结构分组；周期构图、padding 与原子顺序；线性投影梯度、训练阶段更新、缓存分片哈希/上游依赖/中断保护；0→1→2 直接链和缓存路径一致；训练统计和缓存不读取验证/测试标签；checkpoint 恢复、原单位 MAE 与任务覆盖。先用小图/HTTP 数据测试，并运行原有回归；实际训练与全库处理通过 Slurm。默认协议与来源清单须在正式训练前固定。预期单元和小数据闭环全部通过后才提交/同步；真实 GPU 和全任务结果另行记录，不以 mock 代替。

实际结果（2026-11-02T01:09+08:00，本地实现）：完整 pytest 为 35 项通过（旧 27 + 新 8），其中独立固定官方 CIFData 构图与原生 forward 对照、缓存损坏/中断恢复、三阶段真实优化、历史缓存链一致、累计优化步数匹配及延后评测/图表生成均通过。新增代码 ruff 检查通过，官方第三方源码保持原样并校验 SHA-256；4 个 Slurm 文件 Bash 语法、Python compileall 与 git diff --check 通过。10 项未使用导入已清理并格式化；最终格式化后再次运行新增回归。以上为小图 CPU 验证，尚不代表真实 JARVIS/GPU 或全任务结果。

提交前复验：格式化后新增 8 项再次通过；ruff、4 份 Bash 语法与 compileall 通过。暂存完整新增文件后发现 upstream 自有 __init__.py/source.json 的 CRLF 被视为行尾空白，已转为 LF（官方源码字节未改），git diff --cached --check 复验通过。全部新增模块 README、相对链接、UTF-8 和单文件小于 10 MiB 检查通过。

## 2026-11-02T01:17+08:00：离线环境引导与官方数据路由修复（计划）

setup 878 已由 scontrol 确认为 FAILED/35，日志为空且发生在 curl 探针，未安装项目包。增加显式离线 wheelhouse 分支，安装前逐项 SHA-256，保留原已锁定 numpy/pymatgen/matplotlib 版本，不降低 GPU/单元测试门槛。固定数据下载 URL 切换到 Figshare 官方 API /v2/file/download/29204826，仍验证原 MD5/大小。检查 Bash 语法、源 manifest、离线文件哈希与大小、README 命令一致；随后真实 Slurm setup 验收。

实际结果（2026-11-02T01:19+08:00）：离线 wheelhouse 共 10 个 wheel、31,866,325 bytes，逐项 SHA-256 清单已生成；固定 JARVIS ZIP 为 31,911,815 bytes，官方 MD5 通过，本地 SHA-256 03e5af365067117d97c73b83fc74b86f79cdba4cc592b346f5aa2209a24c3925。通用 manifest loader 接受 API 路由与原 MD5；setup/prepare Bash 语法和 git diff --check 通过。此修复不改变模型/训练协议，仅切换网络路径；真实离线安装待服务器 Slurm 验收。

## 2026-11-02T01:23+08:00：预训练前环境协议调整（计划）

SCP 32 MB 环境包被跳板重置，未达到离线验收。实测服务器现有 numpy 2.2.6/pymatgen 2025.10.7/matplotlib 3.10.3 是已安装的兼容组合，CGCNN 纯 PyTorch 本身不要求旧版本，故在任何真实训练前改为精确锁定这些继承版本；仅传 7 个纯 Python 测试依赖共约0.5 MB。模型/数据/训练配置、原生差分与缓存链验收标准全部保持。检查精确 pin、离线清单和 Bash 语法；必须通过同一真实 Slurm GPU 和 8 项集成测试才完成环境验收。

实际结果（2026-11-02T01:24+08:00）：精简环境包为 6 个 Linux 所需纯 Python wheel、466,401 bytes（Windows colorama 不需要），逐项 SHA-256 复验通过；ruff、setup Bash、compileall 通过，CGCNN 8 项本地验收再次通过。生产精确版本断言已加入 GPU 检查脚本，真实环境仍待 Slurm 验收。

## 2026-11-02T01:30+08:00：实际安装元数据与断线数据传输修复（计划）

真实setup879已通过GPU和8项测试，但venv旧构建工具产生UNKNOWN元数据；固定setuptools70.2.0/wheel0.45.1，并要求实际项目metadata版本0.1.0。prepare880经官方API已下载约1.9MiB后因SSH代理断开以56失败，保留残片，未构图。新增仅在官方MD5/大小通过后接受SFTP staging文件的路径，传输用SFTP reput续传，不反复覆盖已传字节。检查离线8项清单、Bash语法、项目metadata及compileall，重跑同一Slurm测试门槛。

实际结果（2026-11-02T01:33+08:00）：本地纯 Python wheel 构建成功，METADATA 名称 recursive-atomistic-backbones、版本0.1.0及CGCNN描述符资源正确。更新的8项离线清单全部通过SHA-256；ruff、setup/prepare/task Bash语法、compileall及git diff --check通过。879已权威确认为COMPLETED/0、GPU与8项测试通过；880确认为FAILED/56，保留1.9MiB残片。安装元数据修复及staging门控需由下一轮真实作业验证。

## 2026-11-02T01:41+08:00：真实预处理前的快照绑定（计划）

审计发现prepared任务与graph快照之间缺少显式匹配门控，且构图恢复未绑定描述符/库版本。新增任务dataset SHA与graph dataset SHA一致性拒绝测试；图缓存身份绑定构图代码、描述符及NumPy/pymatgen版本，恢复不复用其他builder。保持原生几何与模型行为不变，运行完整36项测试、静态检查后提交，再用于尚未开始的真实构图。

实际结果（2026-11-02T01:44+08:00）：全部36项pytest通过（旧27 + 新9），新增任务/图快照混用被拒绝；ruff和格式化通过。图builder身份纳入代码/描述符/NumPy/pymatgen版本，恢复不再仅看文件存在或维度。此前传输助手已提交旧代码882，因此正式预处理改用独立 prepared 根路径并先检查/停止任务自有旧预处理，不覆盖其产物。

## 2026-11-02T01:55+08:00：官方归档重复ID规范化（计划）

Slurm887权威审计：raw55723、unique55712、5个重复ID，JVASP-97311的3条记录仅formation_energy_peratom不同，其余4个重复ID的所有字段完全一致。新增显式规范化：同ID必须同结构，合并一致/缺失标签；多个不同有限标签仅在该任务排除，不任意选择；结构仍保留全库。分别固定raw/unique计数和完整源checksum，审计保留每个重复记录hash/冲突值。测试完全重复、缺失合并、冲突标签隔离、不同结构拒绝及ZIP raw/unique门控，保留严格select_labels重复ID拒绝与全部既有测试。

实际结果（2026-11-02T01:58+08:00）：全部39项pytest通过（旧27+新12），去重单元验证完全重复合并、缺失值合并、冲突形成能仅在该任务排除、其他任务和结构保留、不同结构同ID拒绝；raw/unique/重复ID/已知冲突门控分别可拒绝不一致输入。ruff与格式化通过。固定归档官方MD5不变；计数修正依据Slurm887真实审计，不是因失败放松门槛。真实全库预处理待提交新版代码。

## 2026-11-02T02:10+08:00：真实pilot完成后的扩展门控（计划）

新增独立Slurm验收入口：在890成功后加载真实第0轮checkpoint与晶体图，在CUDA上比较官方native forward与wrapper，固定atol2e-5/rtol1e-4；检查单结构/批量一致、eval buffers/权重不变及0→1直接链/缓存一致，不读取任何标签。仅验收成功后允许全29任务seed123第0–5轮和必要对照数组运行，汇总作业afterany保留失败覆盖表。检查新增Python/Bash语法、README命令和只读标签边界；实际GPU结果必须等待真实pilot。

实际结果（2026-11-02T02:12+08:00）：新GPU验收脚本ruff/compileall与accept.sbatch Bash语法、README命令检查通过；不改核心src或训练配置，故不使890缓存/恢复身份失效。真实验收仍须890完成后在Slurm执行，不记为已通过。实测888已通过12项GPU环境集成测试；889全库55712结构0失败、29/29任务ready，116.02秒完成；890已运行至第0轮epoch4，best验证MAE0.1457127 eV/atom，测试标签未用于选择。

2026-11-02T02:15+08:00：全任务每个Slurm作业新增已有inspect_environment的启动复核，记录独立环境JSON并断言精确版本/GPU，防止长矩阵运行期间只读继承包被外部更新而静默混用；Bash语法与ruff通过。该检查函数已在888真实GPU验收通过，未修改src或优化/数据协议。

## 2026-11-02T02:21+08:00：实际运行证据与提交前文档检查

本轮仅记录进度。小型JSON回读显示55712结构、29任务ready、项目metadata0.1.0、原始55723行；训练history有32个完成epoch，best验证MAE0.07208431。scontrol分别确认891 afterok890、892 afterok891（0–28%1）、893 afterany892_*，890为RUNNING。git check-ignore确认本地审计/训练生成物被忽略；实际路径、作业ID和Markdown格式检查通过。提交前git diff --check通过，未重复声称最终实验或真实pilot验收已完成。

## 2026-11-02T02:27+08:00：训练执行开销诊断（计划）

890实测每epoch约30秒，全矩阵含累计步数对照成本较大。只增加scripts诊断，不改src/config或已有权重：复制真实原子图与checkpoint到独立结果目录，在任务890自有Slurm allocation内通过srun --jobid/--overlap做短诊断；对比原生逐图mean pooling与数学等价segment mean的前向/梯度（原定atol2e-5/rtol1e-4）及原路径开销，记录共享GPU条件。不得读取标签、写回checkpoint、改变训练预算或据此跳过必需验收。先ruff/compileall/Bash检查，诊断失败仅记录候选不可用，不影响原训练或将其记为通过。

实际结果（2026-11-02T02:32:08+08:00）：profile_execution.py 的ruff检查、py_compile和git diff --check通过；诊断仅操作checkpoint副本与64个无标签图，候选前向/逐参数梯度沿用固定容差，失败明确标记rejected。实际性能/数值结果待Slurm短步骤，不将静态检查称为GPU验收。

实际结果（2026-11-02T02:35:29+08:00）：真实Slurm步骤890.0成功保存diagnostic.json（CUDA、64结构/699原子、shared_gpu=true）。native及segment候选前向与全部参数梯度均通过固定atol2e-5/rtol1e-4，候选预测最大差2.38418579e-7；固定批次单步19.316ms/10.133ms。原权重/标签不变，独立副本训练，非生产替换或全任务验收。SFTP回读JSON确认上述字段；history已完成62epoch，best验证MAE0.05821373。文档路径、依赖ID和git diff --check检查通过；生成证据确认Git忽略。

- 2026-11-02T02:37:09+08:00（仅文档检查）：squeue/固定日志/history.json交叉确认890为RUNNING、epoch66、46002步、best验证MAE0.05821373；后续891/892/893为依赖等待。核对作业ID、正式work_root和本地证据快照时效，git diff --check通过；无代码或配置修改，不重复运行训练测试。

- 2026-11-02T02:42:59+08:00（监控/文档）：管理辅助脚本py_compile通过；二进制stdin的真实连接先成功pull再查询，连续观测r0epoch76→78，890 RUNNING、无failure，891–893为Dependency。Windows text stdin造成CRLF失败后仅终止明确匹配的本地observer树，未把观测错误解释成训练失败。核查状态文档handle/路径和git diff --check通过。

- 2026-11-02T03:07:50+08:00（资源估算文档检查计划）：基于已拉回的真实62epoch history、29任务标签审计、固定300epoch/64batch配置和实际7天Slurm时限，重算单阶段/31阶段等价预算及标签数同比例估算；明确这是不早停、同吞吐假设下的数量级参照，不能作为运行上界、完成承诺或GPU利用时间实测。核对计划/配置/Slurm脚本相对链接与公式，保持既定任务和训练预算不变。

实际结果（2026-11-02T03:09:35+08:00）：资源记录公式和全部相对链接检查通过，确认29任务ready、有效标签总数801007、形成能55711、配置300epoch、Slurm时限7天；阶段预算6+5+(2+3+4+5+6)=31，62epoch实测均值30.720797秒，得到单任务79.362小时及标签同比例47.544天。明确非运行上界/忙碌GPU时间，未包含全部缓存/验证成本，显存和IO实测仍缺失。git diff --check通过；仅修改文档，无代码/配置测试重跑。

## 2026-11-02T03:12:45+08:00：pilot资源诊断实现单元（计划）

新增scripts级两阶段资源诊断，在真实pilot成功后由已有891验收入口调用，不改src/config/训练身份。记录全部缓存manifest覆盖/实际字节数、随机固定批次图装载与首次校验缓存读取、H2D/原生forward-backward-Adam副本步骤计时及PyTorch峰值allocated/reserved显存；明确为固定批次、零目标代理损失、lr=0副本、OS页缓存未知，不冒充整轮训练峰值或裸盘带宽。测试在已有三阶段CPU集成夹具中暂时移走任务标签文件，验证诊断仍可运行、CPU显存项为空、两阶段缓存覆盖与checkpoint/manifest SHA不变；真实GPU数值必须等pilot后Slurm891，提前只记静态/CPU验证。执行ruff/编译、对应集成测试及Slurm Bash语法，任何失败修复后再提交。

实际结果（2026-11-02T03:18:02+08:00）：全部39项pytest通过（扩展已有三阶段测试，数量未增加），覆盖真实文件标签缺席、两阶段完整缓存元数据、所有checkpoint/manifest/分片SHA不变、异协议拒绝及CPU显存字段为空；ruff/格式/py_compile/accept.sbatch Bash语法/git diff --check通过。首次pytest因默认Temp和.pytest_cache ACL在setup阶段失败，改用任务专用workspace --basetemp及cache_dir后通过，未降低断言。真实GPU峰值/IO结果仍须891在pilot结束后执行。核心src和训练配置未改。

- 2026-11-02T03:21:00+08:00：远端同步后轻量验收通过：HEAD ee775bc，accept_real.py引用audit_pilot，新增脚本存在；git diff 4379c88 HEAD -- src/self_evolution configs/self_evolution为空；squeue890 RUNNING、891 afterok890等待。未在登录节点执行资源/训练脚本或编译。文档链接和git diff --check通过；GPU资源测量仍未执行。

## 2026-11-02T03:29:04+08:00：独立任务共享GPU调度（实现计划）

保持src/config/seed/原生算子和训练预算不变，仅scripts/slurm新增按4任务一组的pool入口；同组独立任务并行训练，全部训练子进程退出后再逐任务独占GPU执行evaluate/部署计时。启动前验证真实验收与资源报告SHA/配置，依代表批次和最大原子数批次的GPU reserved峰值、CPU配置及可用内存保守选择1–4并发；最大批次OOM只记录诊断不可用并退回1，不把OOM记通过。测试范围：29任务分组全覆盖无重复；资源缺失/错hash拒绝、内存小则降低并发；真实CPU子进程验证并发上限、失败任务隔离、其他任务继续、全部run结束前不evaluate、evaluate串行、恢复日志与共享条件元数据完整。扩展已有pipeline测试覆盖代表/最大批次报告及checkpoint/缓存不变。ruff/py_compile/Bash语法及完整pytest通过后提交；正式队列只在真实pilot资源已测且新版入口同步后替换，不能仅凭静态估算启用并行。

实际结果（2026-11-02T03:46:18+08:00）：全部45项本地pytest通过（原39+6项pool），最终账本/报告保留/预算元数据修改后6项pool再次通过。真实短子进程证明并发2上限及重叠、run全部终止后才evaluate、evaluate串行、一任务失败不取消其他任务、旧报告和多次尝试账本保留；资源错配置/core/graph/SHA可拒绝，内存不足/OOM标记回单进程。代表/最大批次CPU集成通过、所有checkpoint/cache分片hash不变。ruff/格式/py_compile、pool及pool_check Bash语法、文档相对链接和git diff --check通过。Slurm Linux检查和真实GPU测量仍待执行，未将它们记通过。

- 2026-11-02T03:51:16+08:00：真实Slurm894 CPU检查通过：scontrol为COMPLETED、ExitCode0:0、runtime8秒；固定log显示18 passed in 6.89s。覆盖当前Linux真实flock/子进程调度、原生/缓存/三阶段CPU集成；未称为GPU资源测量。source HEAD13f4fde，核心src/config diff为空。下一步可迁移pending队列，实际并发由afterok891+运行时真实资源报告门控。

- 2026-11-02T04:05:23+08:00（阶段完成证据）：SFTP回读r0 training确认222epoch/154734步、stop_reason=validation_patience、best验证MAE0.04822800、ckpt8bb926e4…；链manifest target仍5且status partial，仅r0完成。远端缓存元数据/stat确认55712结构/562055原子/64维float32/218片/147579938字节，cache_timing=12.91283808秒。16结构链检查depth0、最大节点差6.1988831e-06，与同一checkpoint SHA对应；当前r1已实际开始。pool迁移ledger phase complete、895 afterok891和893 afterany895_*经scontrol核对。小型证据Git忽略、文档路径/链接/格式及git diff --check检查通过；无新代码改动，不重复跑测试。

## 2026-11-02T04:12:44+08:00：缓存交付元数据补全（实现计划）

审计发现基础cache/manifest.json已有配置hash/分片SHA，但未内联完整配置及分片字节数。为满足plan_2第5节且保留运行中缓存身份，在scripts增加cache_provenance.py：锁住任务，对已完成连续阶段全分片重算SHA/字节数与覆盖/原子计数，输出每阶段cache_provenance.json补充manifest，包含完整配置、数据/图/原子顺序来源、checkpoint/前驱/代码身份及成功/失败ID；根chain_manifest以SHA引用补充manifest。不得修改原cache/manifest、checkpoint、分片或训练配置。run/evaluate和pilot验收入口调用，计算仅Slurm。扩展三阶段CPU集成：标签文件缺席仍生成元数据，配置/逐片字节/数据来源/全覆盖字段正确，重复审计幂等，原数据SHA不变，错配置及分片损坏拒绝且旧审计/链不被部分改写，补充字段与核心评测兼容。ruff/编译、对应及完整测试、真实Slurm CPU复核后同步；真实全库审计在891/正式任务中执行。

- 2026-11-02T04:14:50+08:00（同单元验收范围补充）：公开CLI evaluate在任何测试评估前，使用审计入口require_complete检查预设全链及全部original/cumulative对照的完成文件、协议、checkpoint SHA和累计步数；缺任一对照立即拒绝，不能等主链测试评估后才发现缺失。测试临时移走一个对照training.json，确认审计失败且链/已有审计未改，再恢复后正常运行。只增加scripts门控，核心训练源码不变。

- 2026-11-02T04:28:18+08:00（入口兼容检查）：pool一份Slurm allocation可能持续数日、先后启动多个任务，原每job环境检查不足以覆盖晚启动子进程。公开CUDA run/evaluate每次复用已有inspect_environment复核精确版本/GPU并记录action/PID环境JSON；增加负向入口测试，模拟检查进程失败，证明run_task未调用且failure.json记录错误。CPU路径跳过GPU检查，服务器CPU测试不实际访问GPU。该检查不改变训练参数或核心身份。

实际结果（2026-11-02T04:31:51+08:00）：全部46项pytest通过（原45+1个CLI环境门控测试），ruff/format/py_compile及git diff --check通过。扩展三阶段集成在标签文件缺席时发布完整配置/来源/字节数/逐片SHA/成功失败ID补充manifest，重复发布SHA一致；checkpoint、基础manifest和全部3阶段分片SHA保持不变。缺对照、跨任务control、错来源/配置及分片损坏会拒绝且旧链/审计不部分改写，核心评测兼容新增链字段。期间一个测试临时变量定义顺序错误导致NameError，已修正后完整重跑通过，未删改断言。负向环境检查模拟失败证明训练未调用并记录failure。真实Slurm CPU复核及真实两轮GPU验收仍待，不提前记通过。

- 2026-11-02T04:40:34+08:00：远端源码同步/元数据前置检查通过（HEAD896a171，prepared source SHA与当前官方来源manifest匹配、graph_config等于冻结配置、核心src/config差异为空）；Slurm896为COMPLETED/ExitCode0:0/runtime8秒，固定日志19 passed in 6.95s。此为CPU集成和脚本检查，不是全库审计或两轮真实GPU验收。文档路径、作业ID、schema字段和git diff --check通过；未因仅文档更新重跑训练。

- 2026-11-02T05:02:38+08:00（仅文档）：原observer96216的真实squeue/history连续确认890仍RUNNING，第1轮128epoch、best验证MAE0.04402161，完成标记均未生成且无failure。核对数据为验证指标、原作业与持久handle不变、文档路径和git diff --check通过；本轮无代码变更，不重复执行模型测试。

- 2026-11-02T05:57:29+08:00（真实pilot/矩阵验收）：scontrol确认890/891均COMPLETED、ExitCode0:0；891 runtime7秒，真实CUDA32结构native/wrapper差0、batch/single差4.172325e-7、0→1缓存/链通过既定组合容差，阶段节点最大绝对差1.7166e-5/4.5776e-5。两份补充manifest及resource报告经SFTP回读，SHA与验收引用、完整config、55712成功ID/0失败、562055原子及逐片字节合计均核对通过。最大64结构5238原子reserved峰值672MiB、代表699原子150MiB；报告为独立副本固定批次指标。895_0/job897实际4个PID、4份日志和history证实训练，无failure，0/29完整report。只读新observer8154 latest/JSONL正常，文档链接/路径和git diff --check通过；本轮无业务代码变动。

## 2026-11-02T06:07:17+08:00：pending分组均衡（实现计划）

真实四并发各任务约30秒/epoch，剩余原分组因标签量差异存在barrier等待；用有效标签量作工作量代理，保持已启动wave0，未启动组排序后sum(group_max_labels)由288676变223656（约22.5%下降，非实测速比）。scripts增加来源/config/graphs绑定的可选task_schedule.json；完整29任务仅一次、8组原容量不变，所有已有wave ledger任务列表必须保持。run_wave仅从验证后的分组取成员，不改src/config/seed/batch/轮数/控制和4并发上限；现有wave0不重启。测试完整无重复覆盖/已开始组保护/排序和上下文错配拒绝、派发实际采用指定组；完整pytest/静态检查、Slurm CPU复核后再发布运行目录调度文件，发布前复查全部已出现wave ledger，禁止改动已开始成员。


- 2026-11-02T06:14:57+08:00：pending分组实现本地全量49项回归通过（pytest工作区独立basetemp）；最终候选发布前校验接口补充后3项调度测试再次通过，ruff format/check及git diff --check通过。覆盖全29项唯一分组、全部已启动wave保护、来源/配置拒绝和真实dispatcher选组；下一步Slurm CPU集成复核，未发布运行时文件。


- 2026-11-02T06:17:54+08:00：真实Linux Slurm898通过全部22项self_evolution测试（6.92秒），固定日志已SFTP拉回。runtime分组发布前后复核候选SHA、完整29覆盖、来源/配置/图/审计哈希及唯一既有wave000任务原样，load_schedule重读等于候选；当前895_0仍RUNNING，893依赖保留。文档对应链接/路径存在，git diff --check通过。


- 2026-11-02T06:21:42+08:00：本轮仅更新verified-wait文档记录，无代码/配置改动，不新增训练测试。检查state变更记录原历史逐字保留、当前观测包含真实RUNNING队列与无failure证据，文档路径存在；提交前git diff --check通过。训练未完成不能当作完整实验验收。


- 2026-11-02T06:32:17+08:00：仅更新监控文档；无源码/训练配置变更，不重复运行模型测试。验证state已有变更历史完整保留、最新观测含真实RUNNING及无failure记录、计划和资源说明路径存在，git diff --check通过。当前进度未达到全29任务六轮与对照完成条件。


- 2026-11-02T06:41:36+08:00：本轮仅文档/资源观测记录，无代码、配置或队列修改。核对监控会话实际活动、RUNNING及无failure记录；资源元数据查询在Slurm897内执行；state旧历史完整保留，相关计划/资源路径存在，git diff --check通过。未复跑已通过的49项回归；完整实验仍不满足验收条件。


- 2026-11-02T07:01:24+08:00：仅更新本轮实时等待记录，无源码/配置变更；不重复模型测试。检查observer工具handle仍活动、真实RUNNING及无failure证据、state历史保留和相关计划路径存在，git diff --check通过。完整实验仍未达到全29任务六轮/对照/最终曲线验收条件。


- 2026-11-02T07:36:28+08:00：带隙r0真实产物核验计划：SFTP小型metadata后，检查cache manifest SHA与timing/root chain一致、checkpoint/config/core/graph身份一致、55712唯一结构ID与已验收全库ID集合相同、562055原子/64维float32/218分片、完整training history及步数/最佳验证值一致、固定16结构chain验证记录和r1正向训练进展。仅核对metadata，不在本地重跑训练或加载缓存tensor；全分片tensor检查由Slurm生成路径完成。


- 2026-11-02T07:37:47+08:00：带隙r0真实产物检查全部通过：完整55712 ID集合、562055原子/64维float32/218分片、manifest SHA/timing/chain及checkpoint/config/core/graph身份、266条history/185402步/最优验证值、16结构既定容差记录和r1正步数。核验结果在忽略目录transition_metadata_audit.json；本地仅metadata检查，未复制/重算缓存tensor，Slurm publish_cache路径已逐片验证SHA/有限值/形状。state历史原文保留，文档路径/格式和git diff --check通过，无代码/配置变更，不重复既有49项测试。


- 2026-11-02T09:27:19+08:00：新增阶段metadata核验计划：总能/ehull r0及带隙r1的完整55712 ID覆盖、562055原子/64维float32/218分片、cache/timing/root chain/checkpoint/config/core/graph SHA和父缓存绑定、训练history/步数/最佳验证值及16结构组合容差记录；形成能original1的原始输入模式/无父缓存、与主链相同训练划分/归一化、配置与source身份及300epoch/209100步。只读metadata；逐片tensor校验保留Slurm生成路径口径。观察器重建应得到实际RUNNING和当前新阶段，不据观察超时重提训练。


- 2026-11-02T09:29:37+08:00：四性质汇总实现单元测试计划：外部执行范围绑定配置与精确四任务、其他25明确deferred；不改src/config核心身份；四任务全部完整才可标记当前scope complete，缺一个/一轮/必要控制仍partial；曲线/CSV仅四性质且coverage区分deferred；无scope文件默认29项兼容；Slurm队列只取消验证为PENDING的895_1–7、保留895_0/job897，汇总就绪前held893。本地测试/静态和Slurm CPU复核后才释放汇总。


- 2026-11-02T09:40:21+08:00：四性质范围实现：显式selected/deferred配置SHA绑定、延期task入口训练前拒绝、report-only view复用固定绘图器、完整0–5轮/两对照及执行状态验证、当前scope完成计数4/其余25延期。完整本地57项通过，ruff format/check通过；无src/config科学身份变化，Slurm CPU与实际scope发布待进行。


- 2026-11-02T09:42:55+08:00：最终候选范围验证接口加入后，8项范围测试再次通过；此前完整57项回归通过。ruff format --check/check、文档路径检查及git diff --check通过，git diff 4379c88 -- src/self_evolution configs/self_evolution为空。已从原提交脚本确认汇总893显式CGCNN_WORK_ROOT为当前final工作目录，可验收后安全释放原汇总。


- 2026-11-02T09:51:16+08:00：完成用户四性质范围调整。4fb240b已Guqq pull并通过Slurm899全部30项CPU集成（12.01秒），本地57项和最终8项均通过。runtime execution_scope.json SHA ef3595e2a3d20845dca44d5386a0eee5e6bbcb0082c588e65c09041de13ef3a0已校验config及wave000四成员后原子发布，895_1–7取消、895_0/job897继续、893已release且仍afterany895。其他25性质明确deferred，训练核心/预算/seed/全库55712结构缓存不变；当前验收仅四性质0–5轮及必要对照。


- 2026-11-02T09:51:16+08:00：新增真实metadata核验通过：总能r0 300epoch/209100步、best验证MAE0.05124270436、缓存14.027秒；ehull r0 300epoch/207900步、best验证0.11916632863、缓存14.113秒；带隙r1 139epoch/96883步、best验证0.15119843529、缓存9.329秒/86813参数（投影5980）。三份缓存均55712唯一ID/562055原子/64维float32/218分片，完整ID集合、cache/timing/chain/checkpoint/config/core/graph及父缓存身份匹配，固定16结构组合容差检查记录一致。形成能original1为300epoch/209100步、best验证0.04533867818，独立原始输入/相同训练ID与归一化核验通过；累计对照继续，目标269042步。数据/审计JSON均保持Git忽略；最新2026-11-02T09:50:22.941194+08:00四任务仍训练、无failure，本阶段完整结果尚未完成。


- 2026-11-02T09:51:16+08:00：本次仅收尾文档：实际scope发布前后SHA/config/四任务现有ledger一致，汇总893释放后依赖未改；新增产物metadata检查通过。检查旧state历史逐字保留、计划/脚本路径存在、生成物受.gitignore覆盖及git diff --check通过，无进一步源码变更。当前仍未满足四性质完整六轮/对照/测试曲线完成条件。


- 2026-11-02T09:53:32+08:00：ehull r1真实metadata检查范围：55712唯一结构ID与已验收全库一致，562055原子/64维float32/218分片，cache manifest SHA/timing/root chain/checkpoint/config/core/graph/父缓存一致；与r0相同训练归一化/ID hash，投影参数增加5980；完整history、optimizer_steps/最优验证值与16结构固定atol+rtol记录匹配。仅metadata，本地不重新加载或处理缓存tensor；逐片检查仍由Slurm生成路径完成。


- 2026-11-02T09:55:54+08:00：ehull r1计划内metadata检查全部通过：精确全库ID集合与原子数/特征维度/分片数、权重/父缓存/manifest/chain身份、训练归一化/ID hash、独立阶段种子、投影参数差5980、207条history/143451步/最佳验证值、累计351351步、16结构固定组合容差记录。实际Slurm895_0仍RUNNING、893 PENDING(Dependency)。仅更新文档，无源码/配置变更，不重跑模型测试；旧state历史保留，路径/生成物忽略及git diff --check通过。


- 2026-11-02T13:38:26+08:00：本次仅用户授权状态查询与文档更新：检查真实squeue运行/依赖状态、已完成training.json与未完成history的区分，并按各轮最佳验证MAE计算相对变化。未训练/推理/测试评估、未改代码或科学配置；state历史保留、查询快照受Git忽略、git diff --check通过。不重复运行模型测试。


- 2026-11-02T16:16:35+08:00：本次仅状态查询和文档更新。核对已完成training与活动history区分，按真实步数/目标步数计算控制进度，按r1/r2最佳验证MAE计算相对变化；四性质无failure、全链仍partial。未训练/推理/测试评估/改配置；旧state历史完整保留、快照/归档受Git忽略、git diff --check通过，不重复模型测试。


- 2026-11-02T16:36:04+08:00：ETA仅本地小型metadata算术，无实现/训练变更。验证四性质均覆盖、四种情景齐全、剩余总小时等于三类训练耗时之和、未来epochs增加时剩余时间单调不减；并行总完成时间取最慢任务。当前累计对照按真实目标步数计算，未来按假设演化步数累加。检查文档路径/历史保留、快照忽略及git diff --check，不把情景当作严格上限或实际早停预测。


- 2026-11-02T22:07:59+08:00：本次仅只读状态/验证数值比较及文档更新：实际squeue、training完成标记/活动history、相邻轮次相对变化和已完成matched-step控制比较核对；未运行训练/推理/最终测试，无源码配置改动。旧state历史保留，快照/计算结果受Git忽略，git diff --check通过，不重复模型测试。


- 2026-11-02T22:16:10+08:00：停训管理单元检查计划：验证897归属/当前scope精确四任务、893在停止训练前已hold；通过当前Slurm allocation CPU诊断读取四个last.pt并加载模型/optimizer、核对identity/config/core/hash及epoch/steps/history/RNG字段，备份last/best/config。仅这些条件通过后取消897；确认本任务无活动895元素/无遗留训练PID、893保持held、原始checkpoint/缓存/源码未删除、暂停账本可定位恢复epoch。不把用户停训记录为模型失败或实验完成。


- 2026-11-02T22:32:14+08:00：停训管理最终检查通过。893先held；Slurm897内4个checkpoint CPU读取/model.load_state_dict/Adam状态加载、RNG/history/config/core身份检查通过并备份；改用895_0后实际CANCELLED/ExitCode0:15、无活动训练元素及原PID残留。暂停账本phase=stopped，原始断点仍存在；本地SFTP复制的4份last/best SHA及config身份全部匹配。source/cache未删除，wave墙钟成本保留。仅文档和运行期管理记录，无科学源码/配置修改；state旧历史完整保留、生成物忽略、路径与git diff --check通过，不重跑训练测试。此前数字897停止未生效的检查未被降低或忽略，已用真实终态/进程退出补齐验收。


- 2026-11-02T23:14:43+08:00：残差验证实现单元测试计划：1）Fprev+sigma*delta单位与残差loss等价、零delta不重复加均值；2）同R0、同direct预算/seed、三分支CPU0–2真实训练、预算逐轮精确匹配、仅累计预测val MAE选新checkpoint；3）中途checkpoint恢复与连续训练等价，旧模型/BN/源ckpt及cache SHA不变；4）节点＋预测archive全ID/原子/float32/shape/字节/SHA、部分写入恢复、错parent/协议/腐坏拒绝；5）test标签变化不影响残差训练数值/训练标准化；6）完整4性质/3方案/3轮报告覆盖、缺失不填零、曲线允许变差。代码前置本计划；完成后本地完整回归/ruff/语法/路径检查，Guqq pull后Slurm CPU及真实GPU链验收，全部满足再正式训练。

- 2026-11-02T23:39:53+08:00：残差实现提交前检查通过：全仓库62项pytest（43.27秒），另行新包5项通过；ruff format/check、三个sbatch逐个bash -n、Python3.10 AST、模块README/文档路径、单文件<10MiB、git diff --check通过。与4379c88比较src/self_evolution及configs/self_evolution零差异；全部生成物位于忽略目录。覆盖三分支0–2、累计残差单位/梯度、全缓存、源冻结、固定预算/seed、恢复等价、test标签隔离、epoch>=1选择及错误协议/过期GPU门禁拒绝。下一步服务器Slurm CPU和真实GPU验收，依赖成功后正式新实验。

- 2026-11-02T23:42:46+08:00：Slurm900测试基础设施失败：--basetemp父diagnostics不存在，pytest10项通过/25个setup错误，模型断言未执行；901/902被成功依赖阻止。修复单元计划：check.sbatch先mkdir -p指定study/diagnostics；逐个bash -n及临时全新父目录模拟验证，再提交同步/Slurm重跑同35项，不改变断言与成功标准。

- 2026-11-02T23:43:44+08:00：check.sbatch父目录修复验证通过：全新tmp/residual-fresh-parent/diagnostics下原5项残差测试15.02秒通过、bash -n与git diff --check通过；未修改测试断言。服务器需重跑原35项，900失败证据保留。

- 2026-11-02T23:46:41+08:00：Slurm903 COMPLETED/ExitCode0:0，35项CPU测试13.90秒通过，修复成立；904真实GPU验收运行中、905成功依赖等待。diagnostics/cpu-903中的failure.json是test_environment_failure_prevents_cuda_training_and_is_recorded预期负例，不能计为科学实验失败；正式failure扫描排除diagnostics。旧893保持held。

- 2026-11-02T23:52:24+08:00：Slurm904真实GPU验收COMPLETED/ExitCode0:0（6分55秒）。四性质各direct R0–2全部55712结构导入/全分片审计/验证MAE复核/直接链通过；两残差方案各R1/R2的4步诊断均完整缓存55712结构并直接链对齐。最大节点差raw7.63e-6/feature1.526e-5、累计预测差<=1.193e-6，既定atol2e-5+rtol1e-4未放宽；最大批64结构/5238原子反向/Adam内存两组均704643072字节reserved（约672MiB），显存总33679736832字节。短诊断仅正确性/资源，MAE不进入正式比较；源旧core/config未改。905按成功依赖启动四worker。

- 2026-11-02T23:55:03+08:00：正式905首阶段健康检查通过：23:54:21快照四worker均完成3–4epoch、每个2091–2788 updates，loss/MAE有限、无正式failure；CPU测试预期负例排除。新实验尚无完成阶段，不宣称改善。文档提交前核对四性质来源MAE在固定容差内、预算合计1767548、README/计划/入口路径存在、outputs/tmp均忽略、state历史只追加、git diff --check通过。仅文档与运行证据更新，不重复模型测试。

- 2026-11-03T09:10:43+08:00：结果审查计划：核对905执行状态、8分支16阶段完成、36验证点唯一覆盖/有限值、各轮与direct实际预算及seed一致、固定R0统计、缓存链检查记录；从metadata复核摘要与training最佳MAE，并计算百分比；图表本地检查。仅元数据/文档分析，不重跑模型或测试集。

- 2026-11-03T09:17:20+08:00：结果审查完成：905账本complete，8分支exit0；16新阶段合计1767548步，36唯一有限验证点覆盖精确、CSV/JSON一致；同R0 ckpt/cache、逐轮direct预算/seed、固定训练归一化/eta1均通过。28缓存manifest的SHA/ckpt小文件SHA、55712结构/562055原子/64维float32/相同IDs hash及自有父预测/节点链通过；20链检查记录固定原容差，未重跑tensor。10份现成报告733386字节下载SHA/大小一致。总览/后轮放大PNG/SVG/PDF生成并目视QA，修正刻度精度避免重复显示；小幅改善/最佳对最佳百分比复算通过。仅文档/结果分析，未跑新训练、模型测试或test评估；提交前检查路径、忽略规则、diff格式及旧核心不变。

- 2026-11-03T09:22:18+08:00：0–2横向比较复核：本地已审计summary.json的36个值按(task,variant,round)读取，12条轨迹齐全；百分比使用未舍入原始值(1-MAE2/MAE0)*100，MAE展示6位小数，百分比2位。四性质最优总降幅9.98%/5.00%/12.38%/5.49%核对；仅表述与文档，不改数据/代码，不重跑测试；diff格式检查通过。

- 2026-11-03T09:41:08+08:00：诊断实现单元测试计划：1）手算完美/反向/高相关但过量修正、常数/并列秩/零方差相关性及误差分解；2）逐材料改善/变差/相同人数与MAE贡献守恒；3）train/val分离及test标签变动不影响指标；4）真实tiny晶体三方案R0–2缓存端到端、完整覆盖/父链/预算/源SHA绑定、输出72指标/48比较的通用小规模映射；5）原始记录与cache不变，历史曲线online MSE/val MAE口径显式分开，未保存epoch不伪造eval train曲线。新代码置独立包避免既有实现hash变化；本地测试/ruff/语法后提交，真实批量加载/绘图仅Slurm CPU，不在登录节点计算。

- 2026-11-03T09:50:26+08:00：诊断提交前验收通过：全仓库66项pytest，64.42秒；其中4项诊断覆盖手算/高相关但过量修正、ties/退化相关性、test标签隔离、tiny真实三方案缓存只读分析及9份PNG/PDF导出。初次全回归65通过/1绘图split索引错误，已修复并完整重跑66通过，无降低断言。ruff format/check、Python3.10 AST、bash -n、README/路径/diff检查通过；与已完成版本比较src/self_evolution、src/residual_scaling及两组配置零差异。下一步Guqq pull后Slurm CPU测试与批量诊断。

- 2026-11-03T09:58:35+08:00：真实诊断验收通过：Slurm906 COMPLETED/ExitCode0:0，54秒；4项服务器测试8.65秒通过。72唯一残差行、48纠错行、28学习曲线完整，所有val MAE与原36点完全一致；133380验证材料行的e-d/gain重算、改善/变差/tie人数分区及benefit-harm净收益守恒通过。分析前后81输入文件SHA未变；26文件11507178字节下载SHA/大小一致。已目视检查学习曲线/全轮残差/纠错分布图，原指标口径清楚，完整和放大图均保留。无重训/新推理/test评估，生成物忽略；最终仅文档变更检查路径与diff即可。

- 2026-11-03T10:26:34+08:00：iComformer实现前测试计划：官方源码/许可证/精确SHA审计；原生forward与包装器数值/梯度对齐、节点pool前边界和256→92投影；官方25邻居+晶格几何/边向量/角索引、batch/single、旋转/平移探针；tiny晶体三方案R0–2真实CPU训练/缓存/续训/源冻结/预算seed一致；完整库55712结构与原split/原子顺序绑定；Slurm真实GPU短链与完整缓存/直接链容差、最大图批次显存和环境门禁。依赖缺失的原生模型测试必须在专用服务器venv跑通，不能用stub替代验收。提交前本地适用回归/ruff/语法，服务器全部明显负载走Slurm；正式36点和纠错诊断完成后核验。

- 2026-11-03T10:46:55+08:00：iComformer source/model/graphs阶段验收通过：5项真实依赖pytest（18.12秒），包括官方SHA/许可证、native输出/梯度/BN一致、batch/single、旋转几何、原生周期图逐边一致、投影detach/原输入冻结、tensor图SHA损坏拒绝。ruff通过（上游原文件不格式化），Python3.10 AST/两个bash -n/TOML/package-data/README/路径检查通过。人工最小输入缺props已通过构造Atoms可选字段适配修复；本地PyG导入捕获了未使用的torch-spline-conv旧DLL警告，但使用的PyG/scatter/Jarvis路径全部真实运行、测试退出0，未使用stub。服务器Linux原生ABI仍须Slurm验收。源第三方逐字保留，owned代码检查diff格式，上游仅查精确SHA。

- 2026-11-03T10:58:28+08:00：服务器环境修复验收计划：907因Jarvis namespace碰撞SyntaxError失败，908未运行。需新venv实际import模块路径落在venv、版本2026.4.2、原生5测试通过；各wheel SHA/大小与PyPI元数据一致，安装不解析替换共享Torch。旧源码/环境不修改。原pytest/native标准不降低；bootstrap静态检查后提交，再经Slurm真实验收。

- 2026-11-03T11:02:08+08:00：独立环境修复提交前静态验收通过：9个官方PyPI wheel条目共5671652字节，URL域/路径唯一性/SHA长度/大小/Python3.10 AST检查通过；bootstrap与check入口ruff、两sbatch bash -n通过。实际安装/原生测试仍待Slurm；仅替换失效pending908，不降低原生5测试或版本检查。venv内Jarvis实际模块路径增加断言，pip --ignore-installed --no-deps --no-index仅安装新venv，不卸载/覆盖共享包。

- 2026-11-03T11:18:36+08:00：iComformer训练/缓存/诊断单元通过：2个新pipeline测试＋4个既有诊断测试共6项364.34秒通过，真实tiny四层iComformer三方案0–2、精确预算/seed/R0共享、缓存直接链、源文件不变、Adam/RNG中断恢复CPU逐权重一致、test标签隔离、诊断接入及缺失分支不得完成。新bootstrap 2项0.57秒通过：完整partial不联网复用，curl56但内容完整仅在SHA/大小全匹配时接受，损坏始终拒绝。ruff/Python3.10 AST/bash检查通过。旧source/model真实5测试已通过；本地未使用spline兼容警告不改变验收标准。下一步同步后先恢复固定wheel资源，再Slurm原生/集成检查及完整构图。

- 2026-11-03T12:02:36+08:00：GPU 提交单元实际检查：全仓库 77 passed（385.63 秒）；首次全仓库收集因两个 test_pipeline.py 模块同名失败，重命名新测试文件后完整通过。服务器 909：9 passed，14.93 秒；910：55,712/55,712 图，零失败。另检查 Python 3.10 语法、Bash、Ruff、源码 SHA 和文档路径；GPU 原生输出/梯度及七阶段全库缓存链待真实 Slurm 验收。

- 2026-11-03T12:02:54+08:00：本提交静态检查全部通过：Ruff（自有代码，原样 upstream 除外）、20 文件 Python 3.10 AST、5 个 Slurm Bash 语法、git diff --check、旧 self_evolution/residual_scaling 零源码改动。

- 2026-11-03T12:04:38+08:00：资源配置调整测试计划：采用911实测安全 batch32，不改变模型/学习率/轮数/残差预算规则；重新验证配置解析及GPU门控/并发规则单元测试，并检查JSON与文档差异。

- 2026-11-03T12:05:36+08:00：批32配置变更检查通过：GPU门控/资源单元2 passed（11.50秒）、真实validate_config解析、JSON、diff whitespace；一次独立解析诊断漏设src导入路径已更正重跑通过，不改测试标准。

- 2026-11-03T12:13:21+08:00：Slurm912完成（6分15秒）：原生GPUforward最大输出误差0，所有梯度对齐；direct R0/R1/R2及raw_residual、feature_residual各R1/R2全7阶段每阶段4次Adam更新，缓存55712结构/562055原子/256维，累计验证MAE、全链重算节点与预测在预定atol2e-5/rtol1e-4内通过。test标签未使用，正式训练913已成功通过配置/代码/图/资源SHA门控启动。

- 2026-11-03T12:13:57+08:00：启动记录文档检查通过：README/计划相对链接存在、912真实JSON七阶段全覆盖/梯度/原生误差校验、913 running快照核对、旧两个科学训练包零改动、diff whitespace通过。

- 2026-11-03T12:16:59+08:00：正式训练健康检查通过：913 RUNNING，形成能R0两个完整epoch/2786更新，train normalized MSE 0.077434，val MAE 0.167904；日志/历史JSON一致、无非有限损失或退出。最终文档diff whitespace检查通过。

- 2026-11-03T12:22:45+08:00：实现单元测试计划：CGCNN×2 native手工组合forward/参数独立；MSE反传第一编码器/线性桥/第二编码器均有非零梯度；全部注册参数参与训练；eval单图/批图一致；小图训练、固定train归一化、精确Adam/RNG断点恢复、过期身份/图/任务拒绝；报告读取旧缓存R1实际MAE/更新/训练和缓存成本，部分结果不可冒充完成。Slurm GPU先CPU单测及真实双编码器最大图batch64前后向/Adam，再小样本短训，失败阻止正式作业。

- 2026-11-03T12:49:15+08:00：CGCNN×2首批3项真实缓存链集成测试通过（43.20秒）；最终相关回归39 passed（103.76秒），覆盖旧CGCNN/残差和新增4项（梯度、159197参数、native组合、断点恢复、test隔离、来源/门控拒绝、完整/partial报告）。Ruff、Python3.10 AST、3份Slurm Bash、README结构、10MiB限制及旧3个训练包零源码修改检查通过；GPU实际测试随队列执行，未宣称已通过。

- 2026-11-03T12:52:39+08:00：服务器914 CPU验收完成（8秒），新增4项真实链测试通过，四性质prepared/图/原CGCNN模型超参数/归一化/来源checkpoint与旧summary SHA核验全部通过。915 GPU资源排队、916依赖等待，不宣称GPU已验收或训练完成。启动文档检查：作业JSON状态、四任务scope、固定旧summary SHA与相对模块路径存在性通过；diff whitespace通过。

- 2026-11-04T00:46:21+08:00：本次仅状态查询/文档更新：实测JSON核验913 running、R0完整training/result/cache一致、R1未完成且167epoch、loss有限、failure集合为空、R1改善比例算术正确；快照路径存在与diff whitespace检查通过。未运行训练/推理/不必要单元测试。

- 2026-11-04T08:44:13+08:00：本次仅进度查询与文档：核验真实913 running、direct三轮training/result/缓存完成标记、raw残差R1未完成与136/198预算、MAE有限/failure集合空；R0→R1及R1→R2比例算术校验、快照路径和diff whitespace通过。未运行训练/推理或重复单测。

- 2026-11-04T09:28:50+08:00：本次仅耗时核验/文档：从既有JSON重新计算逐轮秒数、每epoch平均、训练/验证总时长与pool墙钟差，断言范围/有限性/并发1；读取训练循环/调度/模型确认预算/架构/最大图显存门控。未执行GPU profile，额外实现开销仅列待测，不作定量结论。diff whitespace通过。

- 2026-11-04T17:14:00+08:00：仅进度/文档检查：最新JSON确认913 running、五个训练/结果/缓存阶段完成、feature残差R1未完成且123/198/171339更新、无failure且MAE有限；raw R0→1/1→2算术和快照路径校验通过，diff whitespace通过。未运行额外训练/评测/单测。

- 2026-11-05T01:08:23+08:00：仅状态/文档检查：最新JSON确认形成能7个training/result/cache阶段完整且性质进程exit0、带隙R0未完成且87epoch/121278更新、无failure且MAE有限；三组共享R0及feature两轮改善算术、快照路径与diff whitespace校验通过。未执行额外训练/推理或单测。

- 2026-11-05T01:17:22+08:00：用户授权取消/交接验收：连接后首先git pull，scontrol核对913任务名/用户/工作目录后scancel913；随后实际确认CANCELLED/EndTime，停止前8阶段best/last存在，未删除输出。915 GPU验收COMPLETED且三段梯度非零/最大批64/5238原子通过；916 RUNNING/4性质进程/并发4。元数据与快照断言、文档路径和diff whitespace检查通过；本次不修改训练源码，不重复单测。

- 2026-11-05T09:06:23+08:00：最终对照核验：4/4任务exit0与coverage complete；报告config等于固定配置，执行/验收的自身源码hash和config hash一致；所有来源旧缓存summary SHA固定00d48...789d；4组MAE有限且非负，百分比独立重算一致，编码器预算内胜负一致，test_labels_used false。本地保存原summary和已核验对照JSON，原指标单位沿用TASKS，无跨单位均值。文档diff whitespace检查通过；本次无新代码/训练/推理，不重复单测。
