# 当前状态

Goal 1 的通用递归核心以及 MatterSim、MACE、DPA-2 三个 wrapper 已完成本地实现，16 项测试通过。MatterSim 服务器 wheelhouse 最近观测为 63/144；带前置探针有限重试和慢速下载重试的 12 小时作业 `502` 正在 node221 续传。MACE 的独立本地 wheelhouse 已完成：49 个 wheel、637.90 MiB，离线 dry-run 与 49/49 SHA-256 通过；服务器已 staging 清单与审计 wheel。跨 wheelhouse 哈希播种脚本已完成本地验收，可在 MatterSim 下载结束后复用精确匹配的 wheel。

# 当前计划

1. 提交并同步跨 wheelhouse 哈希播种脚本；继续监控 `node221` 作业 `502`，完成 MatterSim 服务器端 SHA-256 144/144 校验。
2. 由 Slurm 重建任务专用虚拟环境并完全离线安装，再下载官方 checkpoint、运行 MatterSim K=0/K=1。
3. MACE 的 48 项官方 URL、49 项总哈希与小型审计 wheel 已完成服务器 staging；待 MatterSim 下载完成后再补齐共享/官方 wheel，并用已完成的离线 setup 创建隔离环境。
4. 将 job ID、日志、版本、checkpoint checksum 和结果 JSON 同步回本地并完成验收记录。
5. 随后下载论文对齐数据集并进入递增 depth scan。

# 变更记录

- 2026-09-28：跨 wheelhouse 哈希播种实现完成本地验收；脚本只为目标清单中源文件哈希精确匹配的缺失 wheel 创建硬链接，并拒绝覆盖错误目标。下一步提交推送并继续监控 MatterSim 502，完成后先离线安装 MatterSim，再用该脚本减少 MACE 重复下载。

- 2026-09-28：开始实现 Guqq 多连接共享反向 SOCKS；用户选择由首个成功绑定 1080 的会话提供代理，后续会话在转发绑定失败时仍正常登录并复用已有代理。下一步是修改本地 SSH 配置和 `AGENTS.md`，再执行静态检查。
- 2026-09-28：完成 Guqq 多连接共享反向 SOCKS 配置；本地 `ExitOnForwardFailure no` 已生效，固定动态反向转发仍为 Guqq `127.0.0.1:1080`。`AGENTS.md` 已同步记录首连接持有、后续连接复用以及持有者断开后新建连接恢复的行为。
- 2026-09-28：用户再次确认网络已重新配置并要求继续；已完整重读最新版 `AGENTS.md`。下一步按多连接共享规则继续存储检查，端口占用警告不再等同于登录失败。
- 2026-09-28：多连接规则验证成功使远端命令继续执行，但现有 1080 监听无法代理；存储检查确认唯一持久 ext4 分区仅余约 2.7 GiB、`~/.cache` 为 152 GiB。下一步不动未知监听或既有缓存，使用一次性回环 1081 代理并通过 Slurm 验证 tmpfs 可见性。
- 2026-09-28：一次性回环 1081 代理成功恢复 Git 和公网访问；Slurm 探针作业 `489` 在 `node221` 验证 `/dev/shm` 可写且约 126 GiB。确定使用 `/dev/shm/xmz-recursive` 作为可重建运行时根目录，下一步接入 sbatch 并创建 MatterSim 环境。
- 2026-09-28：首次 MatterSim 环境创建命令在 shell 解析阶段失败，未执行任何远端子命令、未留下半成品环境。下一步使用无内联 Python 的命令重试，并继续禁止源码编译。
- 2026-09-28：MatterSim venv 已创建，但其 pip 缺少 SOCKS extra，下载前即停止，尚未安装 MatterSim。下一步用 curl 下载 PySocks wheel并离线引导 pip；若第三次仍失败则按规范补充环境安装经验。
- 2026-09-28：PySocks 已成功离线引导，但非必要的 pip 升级下载中连接提前结束，MatterSim 尚未安装。连续三次环境建立未完成后已将原因和规避方法写入 `lessons.md`；下一步跳过安装器升级，直接安装 binary-only MatterSim。
- 2026-09-28：上一轮 pip 升级实际完成到 26.2.1，并在 SOCKS 索引请求中出现内部 urllib3 `PoolKey` 异常。下一步按已记录经验清理并重建仅属于本任务的 tmpfs MatterSim venv，保留 Python 3.10 自带 pip 22 后重试。
- 2026-09-28：MatterSim venv 已恢复为 pip 22 + PySocks；PyPI 版本核验发现原 1.2.5 pin 不可安装，现已根据官方 v1.2.3 API 审计校正并通过本地测试。下一步安装 1.2.3 并提交真实 Slurm K=0/K=1。
- 2026-09-28：短 SSH 会话中的长 pip 安装再次提前结束，MatterSim 仍未完成安装。策略调整为本地隐藏 SSH keeper 持续提供回环 1081，并先由 Slurm 网络探针验证路径，再通过专用 setup 作业安装环境；避免登录节点长任务和会话生命周期耦合。
- 2026-09-28：隐藏 1081 keeper 已运行且登录节点代理正常；inline Slurm 探针因跨 shell 引号拆分未提交，setup 也未提交。下一步改用仓库内固定 probe sbatch 文件，消除命令行 quoting 风险。
- 2026-09-28：固定 Slurm 网络探针 `490` 成功，确认计算作业的 1081 网络路径；已提交 MatterSim 环境安装作业 `491`。下一步监控该作业并在成功后提交真实推理。
- 2026-09-28：MatterSim setup `491` 因 keeper 退出导致 wandb wheel 哈希校验失败；未安装损坏内容。下一步由可轮询前台 keeper 保持代理，定向清除任务 cache 的 wandb 条目后重试。
- 2026-09-28：前台 keeper 会话 55766 已建立；网络复验 `492` 成功，setup 重试 `493` 已提交。下一步监控 493 并在成功后提交真实 K=0/K=1。
- 2026-09-28：纯转发 keeper 55766 被 Vlab 主动关闭；按经验调整为带应用层心跳的 keeper，下一步恢复代理并检查 setup 493。
- 2026-09-28：确认 setup 493 在新 keeper 启动前已因 atomate2 wheel 哈希不符失败；心跳 keeper 72062 当前稳定。下一步在该 keeper 下重新执行网络探针和 setup。
- 2026-09-28：心跳 keeper 下的网络探针 494 成功，已提交 MatterSim setup 495。下一步保持 keeper 并监控安装结果。
- 2026-09-28：心跳 keeper 72062 仍被 Vlab 重置，长代理下载方案判定不可用。下一步确认 495 后改为本地 wheelhouse + scp + Slurm 离线安装。
- 2026-09-28：确认 setup `495` 在下载 torch 2.14.0 wheel 时因代理中断导致 SHA-256 不匹配而失败，pip 拒绝安装；短时 keeper 已停止。当前进入本地 wheelhouse 实现阶段，setup 将支持 `--no-index --find-links`、安全重建专用 venv 和保存 freeze 清单。
- 2026-09-28：本地 MatterSim wheelhouse 已完成：144 个 Linux/CPython 3.10 wheel、离线依赖 dry-run 成功、SHA-256 144/144 一致；离线 setup 的语法、16 项回归、编译与 whitespace 检查均通过。下一步提交推送后传输到服务器 tmpfs。
- 2026-09-28：离线 setup 提交 `bf2c517` 已推送并在服务器成功 pull；整目录 scp 在约两分钟后被 Vlab 关闭。下一步按清单识别缺失/不完整文件，将大 wheel 分块短传、重组后再做完整哈希校验。
- 2026-09-28：scp 对照吞吐仅约 30 KiB/s，分块 scp 不可行；PyPI URL/官方哈希清单 144/144 生成成功，固定断点续传脚本已通过 CRLF、续传、跳过和失败保护测试。下一步经 Git 同步脚本并重复短会话续传。
- 2026-09-28：固定脚本首轮服务器下载有效，已完成从 aioitertools 到 boto3 等多个 wheel；botocore 中途 SSL EOF 后残片保留。因 curl 在死连接上重试过久，增加低速超时后再续传。
- 2026-09-28：独立 1081 的后续会话仍被跳板机快速重置，但登录节点无代理 PyPI HEAD 已成功。策略调整为固定 node221 的 Slurm 直连下载作业；下一步本地实现、测试、Git 同步后提交。
- 2026-09-28：固定 node221 的 Slurm 直连下载作业 `499` 已提交。下一步监控其 HEAD 探针、续传日志和最终 144 项哈希验收。
- 2026-09-28：作业 499 约 4 分钟时 botocore 残片已达 7,118,848 bytes，直连有效但按总量估算需 7–9 小时；调整 sbatch 时限为 12 小时，下一步尝试原地延长运行中作业。
- 2026-09-28：集群拒绝普通用户原地延长 499，作业未改变。下一步利用已验证的断点语义取消 499，并在同一 node221 以 12 小时时限立即重提。
- 2026-09-28：作业 499 已取消，12 小时续传作业 `500` 已提交到 node221。下一步核对实际时限和断点恢复日志。
- 2026-09-28：作业 500 已确认 node221、12 小时且从残片续传；等待期间并行进入 MACE 独立 wheelhouse 解析，继续保持 backbone 环境隔离。
- 2026-09-28：作业 500 在 35/144 的 h5py 因过严低速阈值失败；按 lessons 调整为慢速直连阈值和长有限重试。MACE 本地 wheelhouse 已完成 49 项离线解析/哈希验收，python-hostlist 纯 Python sdist 已单独审计构建。
- 2026-09-28：下载重试调整已同步，MatterSim 12 小时续传作业 `501` 已提交到 node221；下一步监控 35/144 之后的续传和最终哈希。
- 2026-09-28：作业 501 在前置 HEAD 的单次 15 秒连接超时处失败，未改变 wheelhouse；下一步为探针增加最多 10 分钟有限重试并重提。
- 2026-09-28：探针重试补丁已同步，MatterSim 下载重提为作业 `502`；下一步确认其通过探针并从 h5py 残片继续。
- 2026-09-28：MACE 独立离线 setup 已完成并通过 Bash、静态、16 项回归和编译检查；待 wheelhouse 同步后在 Slurm 中做真实安装。
- 2026-09-28：MatterSim 502 在大 wheel 上慢速运行；等待期间只 staging MACE 两个清单与 39 KiB 审计 wheel，不启动并发大下载。
- 2026-09-28：MACE 控制文件 staging 已完成，服务器行数 48/49、审计 wheel 哈希通过；MatterSim 502 同期推进到 `m` 段依赖并继续独占公网。
- 2026-09-28：MatterSim 离线 setup 补齐安装前完整 SHA-256 门控和代理清除；本地 Bash、16 项回归、编译与静态检查通过。
- 2026-09-28：进入 Guqq SSH 连接故障诊断阶段；用户报告配置反向 SOCKS 后无法连接。下一步是复现连接并根据详细 SSH 日志定位失败阶段。
- 2026-09-28：完成 Guqq SSH 连接故障诊断；ProxyJump 和两层公钥认证均成功，失败原因是 Guqq `127.0.0.1:1080` 已被其他会话占用，且 `ExitOnForwardFailure yes` 导致新 SSH 整体退出。对照连接确认该监听已失去代理能力，本机无残留 `ssh.exe` 进程；未终止任何可能属于用户的远端会话。
- 2026-09-28：进入 SSH 会话级反向 SOCKS 转发配置阶段；用户要求每次 `ssh Guqq` 自动转发、断开后自动停止，并明确跳过 `net.sh` 和 180 秒等待。下一步是备份并最小化修改本地 SSH 配置，然后执行连接生命周期测试。
- 2026-09-28：完成 SSH 会话级反向 SOCKS 配置和验证；Guqq 经 `127.0.0.1:1080` 获得的出口 IP 与本地一致，并在会话退出后拒绝连接。测试同时发现 Guqq 的 `/home/xmz/recursive` 已不存在；后续服务器实验需先恢复工作树。
- 2026-09-28：开始修订 Guqq 网络操作规范；原因是会话级反向 SOCKS 已实测可用，不再需要 `bash net.sh` 和固定 180 秒等待。下一步是修改 `AGENTS.md` 并检查命令、路径、Markdown 和旧流程残留。
- 2026-09-28：完成 Guqq 网络操作规范修订；`AGENTS.md` 现要求登录节点联网命令显式使用会话级 SOCKS，禁止运行 `bash net.sh` 和固定等待，并区分了登录节点与 Slurm 计算节点的网络边界。
- 2026-09-28：用户确认网络已重新配置并要求继续；已重读更新后的 `AGENTS.md`，SSH/反向 SOCKS 故障诊断阶段结束。下一步按新规范恢复服务器仓库并检查运行环境。
- 2026-09-28：服务器仓库同步成功并完成轻量资源检查；发现 `/` 仅余约 2.6 GiB，直接创建三个环境和下载模型有耗尽磁盘风险。下一步只读查找可用挂载点与任务相关占用，再确定环境布局。
- 2026-09-28：存储检查连接因 Guqq `127.0.0.1:1080` 被占用而被 `ExitOnForwardFailure` 提前终止；本地未发现存活 SSH 进程。下一步使用禁用新增转发的连接只读确认远端监听归属，不擅自终止未知进程。
- 2026-09-28：首次禁用新增转发的诊断连接在代理 pull 阶段无输出并超时，未取得端口归属信息。下一次将 pull 网络等待限制为 5 秒，保证后续只读诊断有机会执行；若仍失败则按连续三次失败规则查阅经验记录。

- 2026-09-23：开始修订计划文档；下一步是补充完整数学形式并删除指定章节。
- 2026-09-23：完成数学形式、adapter 固定点分析和评价量定义；删除原第 10、11 节并通过格式检查。
- 2026-09-23：开始编写 `goal_1.md`；下一步是确定最小实现边界、实验决策树和完成标准。
- 2026-09-23：完成 `goal_1.md`；已通过 LaTeX、Markdown、UTF-8 和章节编号检查。
- 2026-09-23：开始将 norm adaptation 改为 per-structure input-norm alignment；下一步是同步修订 goal 和 plan。
- 2026-09-23：完成 norm adaptation 修订；删除训练集统计匹配，改为按结构、状态分量和 irrep block 对齐输入 RMS 范数。
- 2026-09-28：开始按最新实验决策收紧 Goal 1；原因是 adapter 范围、模型模式、递归深度选择和论文对齐任务已经明确；下一步是核验原论文与官方数据资源并重写目标文档。
- 2026-09-28：完成 Goal 1 重写和来源核验；范围收紧为 frozen/eval backbone、irrep-level norm alignment 和递增 depth scan，并锁定三项论文对齐任务；下一阶段为数据 manifest、服务器下载和 backbone 接口审计。
- 2026-09-28：进入实现阶段；检查发现工作区没有 Git 元数据和任何源码，先建立通用实现与测试，同时检查服务器和远端基础设施；真实推理必须通过 Slurm。
- 2026-09-28：完成通用递归核心与 MatterSim M3GNet 本地包装器；10 项轻量测试通过，K=0 fake-M3GNet 路径逐位一致且 K=1 有限。下一步是通过 Git 同步验收脚本并在 Slurm 上使用真实 checkpoint 验证。
- 2026-09-28：服务器网络恢复并确认 `compute` 为可用 GPU 分区，但服务器无本项目仓库，本地也无 `.git`，推测的 GitHub 地址不存在。为遵守“服务器源码只能经 Git 同步”，真实推理阶段等待正确 remote URL。
- 2026-09-28：完成同类型 irrep 联合缩放修复与 MACE-MP-0 small L=0 wrapper；13 项测试通过，真实 MACE K=0/K=1 Slurm 验收入口已准备。下一步审计 DPA-2 repformer 状态边界。
# 当前状态补充（2026-09-28）

DPA-2 的 2024Q1 Repformer 状态边界、本地实现与验收入口已经完成：动态状态为 `g1/g2/h2`，邻居表、mask、switching weight 与 mapping 固定；每个额外 K 重复完整 Repformer 层序列。16 项测试和编译检查通过。当前目录现已初始化为 `main` 分支的 Git 仓库；三个 backbone 均已有真实 checkpoint 的 K=0/K=1 Slurm 脚本。下一步是配置正确的 Git remote、完成初始提交并推送，随后在服务器拉取并通过 Slurm 验收。

# 变更记录补充

- 2026-09-28：进入 DPA-2 实现单元；已根据 DeePMD-kit `2024Q1` 官方源码确定 Repformer 前处理、层调用和 `_cal_h2g2` 输出路径，先完成本地回归测试，再通过 Git/Slurm 运行真实 checkpoint。
- 2026-09-28：完成 DPA-2 Repformer 实现、fake K=0/K=1 回归、真实 OpenLAM 验收脚本和 Slurm 入口；全套 16 项测试通过。下一步是在取得正确 Git remote URL 后依次提交 MatterSim、MACE、DPA-2 的真实 GPU 作业。
- 2026-09-28：按用户要求在工作区执行 `git init -b main`，仓库根目录确认为当前项目目录；未暂存、未提交、未配置 remote。
- 2026-09-28：用户确认 remote 为 `https://github.com/Mingzhe-Xuan/recursive.git`；已验证远端 `main` 存在、本地分支正在跟踪且工作区干净，进入服务器 Slurm 验收阶段。
