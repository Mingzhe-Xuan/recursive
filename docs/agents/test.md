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
