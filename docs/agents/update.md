# 进度更新

- 2026-09-29：1082 被其他远端会话占用且本机无可安全终止的 SSH 进程；下一次监控将把 1080 pull 限制为 10 秒，然后无条件执行离线作业查询，避免代理状态遮蔽 511 进度。
- 2026-09-29：一次 511 监控 SSH 卡在代理 pull；确认并结束了本任务产生的父/ProxyJump 两个残留进程，释放 1082，Slurm 作业不受影响。下一连接为 pull 加有限超时并确保随后离线读取作业状态。
- 2026-09-29：完成 DPA-2 Zenodo 10461723 manifest 和下载器 MD5 校验支持；固定 `data-v1.3.tgz` 的精确大小/官方 checksum 与 SSE-PBE-D split 责任，27 项测试及编译/元数据/格式检查通过。
- 2026-09-29：MatterSim 作业 511 已在 node221 启动并下载首个新增 CUDA wheel；并行开始 DPA-2 Zenodo 10461723 数据 manifest 与官方 MD5 校验支持，不占用 GPU 或本地下载 17 GB 归档。
- 2026-09-29：服务器同步到 `45881fe` 并确认 162 行双清单后，正确的 MatterSim 增量下载作业已提交为 511；当前等待同账号作业 508 释放 node221，未干预既有作业。
- 2026-09-29：Guqq 经临时回环 1082 成功 pull 到 `3b27f13`，任务 wheelhouse 清单已更新为 162 项且保留 144 个既有 wheel；复杂查重表达式解析失败，未提交新作业，下一连接改用简单队列门控。
- 2026-09-29：已取消未运行的错误作业 510；确认 1080 SOCKS 的本机直连出口无法访问 GitHub。下一连接将用仅回环可见、随会话回收的 1082 静态反向转发复用本机 7897 HTTP 代理，先恢复服务器 pull。
- 2026-09-29：服务器代理 pull TLS 中断，仍停在 `f31e4c4`；误提交的旧清单下载作业 510 发现时尚为 PENDING。已登记纠正操作，下一连接先重试 pull，随后取消 510 并核对队列，不让错误计数作业运行。
- 2026-09-29：提交 `7fd2670` 在 GitHub HTTPS 直连连续失败三次后，经 Windows 已启用的回环代理成功推送；拒绝了与 GitHub 官方值不匹配的 SSH 主机指纹，并将命令行代理与主机密钥安全经验写入 `lessons.md`。
- 2026-09-29：补齐 MatterSim wheelhouse 的版本化交付：162 项官方 URL/SHA-256 清单和模块 README 已加入 `data/manifests`，完整一致性/哈希检查与 22 项回归通过；服务器可经 Git 同步清单，无需单独 scp。
- 2026-09-29：完成 MatterSim Linux CUDA 闭包修复：显式固定 PyTorch 2.8.0 三件套与 CUDA 12.8，wheelhouse 扩展为 162 项；完整哈希、Linux/CPython 3.10 离线解析、22 项回归、编译与脚本静态检查通过。下一步推送后在 node221 增量下载新增 18 项并重跑离线 setup。
- 2026-09-28：开始将 Guqq 反向 SOCKS 调整为多连接共享模式：保留固定 `127.0.0.1:1080`，关闭“转发失败即终止登录”，并同步更新操作规范。
- 2026-09-28：完成 Guqq 多连接共享 SOCKS 调整：本地 SSH 配置现为 `ExitOnForwardFailure no`，后续连接遇到 1080 占用时仍可登录；`AGENTS.md` 已说明代理持有、复用与断开后重建流程。
- 2026-09-28：用户确认多连接共享网络配置已完成；重新读取最新版 `AGENTS.md`，后续连接将允许 1080 绑定警告并继续远端命令，先恢复存储检查。
- 2026-09-28：多连接会话已能在 1080 冲突后继续；代理 pull/curl 均超时，证明既有监听不可用。只读存储检查显示 `/` 余约 2.7 GiB、`~/.cache` 占 152 GiB、无其他持久挂载；准备以一次性回环 1081 代理恢复联网并验证 Slurm `/dev/shm`。
- 2026-09-28：一次性回环 1081 代理成功，Guqq 已拉取最新提交；Slurm 探针作业 `489` 在 `node221` 验证 `/dev/shm` 可写且约 126 GiB。决定将可重建环境、缓存与 checkpoint 放入 `/dev/shm/xmz-recursive`，不清理现有用户缓存。
- 2026-09-28：首次 MatterSim 环境命令因嵌套引号导致远端 shell 解析失败，命令整体未执行；将去掉内联 Python 并以二进制-only 安装和 `pip show` 重试。
- 2026-09-28：第二次 MatterSim 环境尝试创建了 venv，但 pip 因缺少 SOCKS 支持在下载前停止；下一步使用 curl 下载 PySocks wheel离线引导 venv pip，再继续 binary-only 安装。
- 2026-09-28：PySocks bootstrap 成功，随后连接在非必要的 pip 升级下载阶段提前结束；已按连续三次失败规则补充环境安装经验，下一次跳过升级并直接安装 MatterSim wheels。
- 2026-09-28：确认前一轮 pip 升级已部分完成至 26.2.1，SOCKS 索引访问触发其内部 urllib3 `PoolKey` 异常；将重建任务专用 venv 并保留系统 pip 22。
- 2026-09-28：重建 venv 后确认 pip 22 + PySocks 正常；发现 PyPI 最高可安装 MatterSim 为 1.2.3，已审计该版本 M3GNet API、修正精确 pin 并通过 16 项测试。
- 2026-09-28：MatterSim 1.2.3 下载在短 SSH 命令结束时再次中止；调整为持久 SSH keeper + Slurm 网络探针 + Slurm setup 作业，长安装不再直接运行于登录节点。
- 2026-09-28：隐藏 1081 keeper 已启动并验证登录节点代理；inline `sbatch --wrap` 因多层引号拆分失败，未产生作业。新增固定 runtime probe sbatch，下一次按文件提交。
- 2026-09-28：固定 Slurm 网络探针 `490` 在 node221 通过，公网出口为 `47.130.251.126`，tmpfs 约 126 GiB；随后提交 MatterSim 环境安装作业 `491`。
- 2026-09-28：MatterSim setup 作业 `491` 失败：keeper 退出后 wandb wheel 下载哈希不符，pip 拒绝安装；旧 keeper 已退出。将用可轮询前台 keeper 和定向 cache 清理重试。
- 2026-09-28：启动可轮询前台 keeper 会话 55766；网络复验作业 `492` 通过，任务 cache 无 wandb 残留，已提交 MatterSim setup 重试作业 `493`。
- 2026-09-28：Vlab 主动关闭纯 `ssh -N` keeper 55766；补充经验并改用每 20 秒产生远端心跳的 keeper，随后继续监控 setup 493。
- 2026-09-28：setup 493 已确认在新 keeper 启动前因 atomate2 wheel 哈希不符失败；带 20 秒心跳的 keeper 72062 正常，准备在其存活期间重新提交。
- 2026-09-28：心跳 keeper 72062 下的 Slurm 网络探针 `494` 通过；任务 cache 无 atomate2 残留，已提交 MatterSim setup 作业 `495`。
- 2026-09-28：Vlab 再次重置带应用层心跳的 keeper 72062；停止通过反向 SOCKS 承载长 pip 下载，切换到本地 binary wheelhouse、哈希清单、scp 与 Slurm 离线安装流程。
- 2026-09-28：开始诊断启用 `RemoteForward 127.0.0.1:1080` 后 `ssh Guqq` 无法连接的问题，优先检查远端端口占用与 `ExitOnForwardFailure yes` 的组合影响。
- 2026-09-28：定位 Guqq 连接失败为远端 `127.0.0.1:1080` 端口冲突；详细日志显示跳板机和 Guqq 认证成功后才出现 `remote port forwarding failed for listen port 1080`。禁用新转发的对照连接成功，确认问题不在网络、ProxyJump 或密钥。
- 2026-09-28：开始修改 `AGENTS.md` 中的 Guqq 网络流程，将强制 `bash net.sh` 与 3 分钟等待替换为仅在 SSH 会话期间存活的本地反向 SOCKS 代理。
- 2026-09-28：完成 `AGENTS.md` 修订：增加登录节点 SOCKS 环境变量示例和会话生命周期说明，删除 `net.sh`/180 秒流程，增加转发故障诊断、禁止对外暴露端口以及 Slurm 计算节点不继承回环代理的约束。
- 2026-09-28：开始配置本地 `Host Guqq` 的 SSH 反向动态转发，目标为连接时自动提供 Guqq 本机 `127.0.0.1:1080` SOCKS5 端口，断开时由 SSH 自动回收；本次按用户明确要求跳过 `net.sh` 和等待。
- 2026-09-28：完成 `Host Guqq` 反向 SOCKS 配置。`ssh -G Guqq` 确认动态 `RemoteForward` 和会话参数生效；本地与 Guqq 代理出口均为 `3.1.58.103`；会话退出后在禁用新转发的检查连接中确认 `127.0.0.1:1080` 拒绝连接。Guqq 上 `~/recursive` 当前不存在，因此每次连接的首项 `git pull` 已尝试但无法执行。
- 2026-09-28：用户确认网络已重新配置；重新完整读取更新后的 `AGENTS.md`，停止旧的 `net.sh`/等待流程，准备使用会话级 SOCKS 恢复服务器工作树并继续 Slurm 验收。
- 2026-09-28：通过会话级 SOCKS 成功将 Guqq `~/recursive` 快进到 `b41299f`，仓库根目录、HEAD 和 remote 均验证通过；确认 Python 3.10.12、RTX 5090 与 `compute` 分区。根分区仅余约 2.6 GiB，环境安装前先检查安全存储位置。
- 2026-09-28：后续存储检查连接因 Guqq 的 1080 监听冲突在远端命令前终止；本地 `Get-Process ssh` 未发现残留会话，配置仍为动态 `RemoteForward 127.0.0.1:1080` 与 `ExitOnForwardFailure yes`。进入只读端口归属诊断。
- 2026-09-28：禁用新增转发的首次诊断连接在代理 pull 阶段无输出并超时，尚未取得 `ss` 结果；下一次使用 5 秒网络超时后继续只读检查。

- 2026-09-28：按用户要求在当前工作目录初始化 Git 仓库，默认分支为 `main`；尚未执行 add、commit 或配置 remote。真实 Slurm 推理仍需正确的远程仓库地址完成服务器同步。
- 2026-09-28：用户提供并确认 `https://github.com/Mingzhe-Xuan/recursive.git`；远端 `main` 已存在且包含当前实现，本地分支与其同步。开始服务器环境与三个真实 backbone 的 Slurm K=0/K=1 验收。
- 2026-09-28：服务器首次同步连接按规范首先执行 `git pull`，确认 `~/recursive` 尚不存在；下一次连接将再次先 pull，再 clone 已确认的远端。
- 2026-09-28：服务器再次连接首先重试 pull，确认目录仍不存在后已通过 Git clone 创建 `~/recursive`；下一步拉取最新记录并检查环境与资源。
- 2026-09-28：完成 DeePMD-kit `2024Q1` DPA-2 Repformer 递归封装、3 项 fake-model 回归测试、OpenLAM `Domains_SSE-PBE` 真实 K=0/K=1 验收脚本、Slurm 提交文件和环境约束记录；测试总数增至 16，全部通过。真实作业继续等待正确 Git remote URL 后同步到服务器。

- 2026-09-23：开始修改 `docs/plan/plan_1.md`，目标是严格定义递归计算过程，并删除原第 10、11 节。
- 2026-09-23：完成修订。新增完整状态空间递推、循环接缝、suffix、预测、训练目标和固定点诊断；删除原“分阶段执行”和“计算资源估算”两节。
- 2026-09-23：开始整理首轮实现目标 `docs/goal/goal_1.md`。
- 2026-09-23：完成 `goal_1.md`，明确整段/逐层递归、固定/结构自适应深度、norm/equivariant adapter、最小实验与阳性后完整实验。
- 2026-09-23：开始修改 norm adaptation，使其仅对齐当前结构的输入状态范数，不使用训练集整体统计量。
- 2026-09-23：完成 `goal_1.md` 与 `plan_1.md` 的同步修改；norm adapter 现为 per-structure input RMS norm alignment。
- 2026-09-28：开始收紧 `goal_1.md`：仅保留 irrep-level norm alignment，固定 backbone 为 `eval()`，以递增深度扫描选择最佳重复次数，并调研三类模型原论文中的可获取评测任务和数据集。
- 2026-09-28：完成 `goal_1.md` 重写。锁定 MatterSim/Matbench phonons、MACE/97-material ffonons、DPA-2/SSE-PBE-D；新增下载与 checksum 责任、depth early-stopping、冻结测试和完成标准。LaTeX、UTF-8、标题及旧范围残留检查通过。
- 2026-09-28：开始 Goal 1 实现。确认当前目录只有文档且不是 Git 仓库；计划先完成通用递归核心及 mock 测试，再接入 MatterSim，并通过服务器 Slurm 验证 K=0/K=1。
- 2026-09-28：完成通用递归核心实现：完整动态状态、irrep-level norm alignment、整段/逐层递归、冻结快照、配置序列化和递增 depth early stopping；8 项单元测试通过。
- 2026-09-28：完成 MatterSim M3GNet wrapper 和 fake-model 集成测试。包装器复现官方几何预处理与 readout，递归状态同时含 atom/edge；测试总数增至 10，K=0 逐位一致且 K=1 有限。
- 2026-09-28：完成 MatterSim 真实 checkpoint K=0/K=1 验收脚本与 Slurm 提交文件；脚本记录 checkpoint hash、版本、容差、能量、gamma 和冻结状态。服务器 alias 在沙箱内无法解析，尚未提交作业。
- 2026-09-28：按网络故障流程在 Guqq 运行 `net.sh` 并等待 3 分钟；确认 Slurm `compute` 分区可用。服务器没有 `recursive` 工作树，本地没有 Git 元数据，且 `Mingzhe-Xuan/recursive` 不存在；真实推理因缺少正确 Git remote URL 暂不能合规同步。
- 2026-09-28：修正 norm alignment：同一状态内所有相同 `(ell, parity)` packed 段现在联合计算 RMS 并严格共享 gamma；新增回归测试。
- 2026-09-28：完成 MACE-MP-0 small L=0 wrapper、fake K=0/K=1 测试、真实 checkpoint 验收脚本与 Slurm 文件。测试总数增至 13，全部通过。
- 2026-09-28：确认 MatterSim setup `495` 因代理中断导致 torch wheel 哈希不匹配而失败，pip 未安装损坏内容；停止短时 keeper。setup 脚本开始接入完整 wheelhouse、强制离线索引、安全重建 venv 和 freeze 清单，下一步在本地解析 Linux cp310 binary 依赖闭包。
- 2026-09-28：完成 MatterSim 离线安装实现与本地验收：setup 支持强制离线 wheelhouse 和安全重建 venv；Linux x86_64 / CPython 3.10 依赖闭包为 144 个 wheel、736.27 MiB，离线 dry-run 和 SHA-256 144/144 通过；16 项回归、编译、Bash 语法与 whitespace 检查通过。
- 2026-09-28：离线 setup 已以 `bf2c517` 推送并同步到 Guqq；首次 736 MiB 整目录 scp 在约两分钟后被 Vlab 中断。调整为基于 SHA-256 清单的增量短传：大 wheel 本地分块，服务器任务 staging 重组后统一复验。
- 2026-09-28：短 scp 实测仅约 30 KiB/s，转为 PyPI 官方 URL 的可恢复下载；144 个 URL 与官方 SHA-256 已逐项匹配。新增 `scripts/download_wheelhouse.sh`，通过 CRLF 清单、残片续传、完整跳过和失败保留测试，避免内联 SSH 多层 quoting。
- 2026-09-28：服务器首轮固定脚本已完成多个 wheel并在 botocore SSL EOF 后保留残片；为 curl 增加 1 KiB/s 持续 30 秒的低速超时和短重试间隔，避免代理失效后的长时间空等。
- 2026-09-28：确认 Guqq 网络重配后可无代理直连 PyPI 且支持 Range；wheelhouse 下载将转为固定 node221 的 Slurm 作业，先探测计算节点直连，再续传并做 144 项哈希验收。
- 2026-09-28：Slurm 直连 wheelhouse 下载作业 `499` 已提交到 node221；作业与 SSH 生命周期解耦，等待计算节点探针和断点续传结果。
- 2026-09-28：作业 499 直连持续写入但吞吐仅几十 KiB/s，736 MiB 预计需 7–9 小时；下载 sbatch 时限由 1 小时调整为 12 小时，优先原地延长以保留进度。
- 2026-09-28：集群拒绝普通用户原地延长作业 499，未改变运行中任务；将利用已验证的 `.partial` 语义安全取消并以 12 小时配置在 node221 重提。
- 2026-09-28：已取消任务自有的 1 小时作业 499，并在同一 node221 以已提交的 12 小时配置重提为作业 `500`；wheel 和 `.partial` 保留用于续传。
- 2026-09-28：作业 500 已确认 `TimeLimit=12:00:00` 且从残片推进；等待期间开始本地解析 MACE 0.3.16 的独立 Linux/CPython 3.10 binary wheelhouse。
- 2026-09-28：作业 500 在 35/144 的 h5py 因原低速阈值失败；保留残片，并将直连默认调整为 128 B/s 持续 120 秒、100 次/2 小时有限重试。该经验已写入 `lessons.md`。
- 2026-09-28：完成 MACE 本地离线闭包：49 个 wheel、637.90 MiB，dry-run 与 49/49 SHA-256 通过；python-hostlist 2.3.0 因无官方 wheel，经纯 Python sdist 审计后单独构建并记录双重哈希。
- 2026-09-28：宽松有限重试已推送并同步；MatterSim 12 小时续传作业 `501` 已提交到 node221，从现有 35 个完整 wheel 和 h5py 残片继续。
- 2026-09-28：作业 501 因前置 PyPI HEAD 的单次 15 秒连接超时失败，未进入下载循环；为探针增加 20 次、最多 10 分钟的有限重试后重提。
- 2026-09-28：计算节点探针重试已同步，MatterSim 12 小时续传作业 `502` 已提交到 node221，等待从 35/144 与 h5py 残片继续。
- 2026-09-28：完成 MACE 独立离线 setup：安装前校验完整 SHA-256，强制 no-index/binary-only，安全重建专用 venv，执行依赖/版本检查并保存 freeze；本地检查全部通过。
- 2026-09-28：准备 staging MACE 的 48 项 URL、49 项总哈希和 39 KiB 审计 wheel；暂不启动第二个大下载，保持 MatterSim 502 独占公网带宽。
- 2026-09-28：MACE 的 48 项 URL、49 项总哈希和 39 KiB 审计 wheel 已传到任务 tmpfs；服务器端清单行数与 wheel SHA-256 通过，未启动并发下载。
- 2026-09-28：MatterSim 离线 setup 增加安装前全清单 SHA-256 校验与继承代理清除，确保任何残片/损坏 wheel 在 venv 重建前失败；本地检查通过。
- 2026-09-28：完成跨 wheelhouse 哈希播种脚本；以目标 SHA-256 清单为唯一准据，只对精确匹配的缺失 wheel 创建硬链接，正确既有文件跳过、错误既有文件拒绝覆盖。CRLF 清单、硬链接身份、错误保护、16 项回归、编译与静态检查均通过。
- 2026-09-28：完成 MatterSim checkpoint 任务目录下载入口；官方 1M 权重由 Slurm 在目标节点断点续传到 tmpfs 并原子落盘，输出大小和 SHA-256。K=0/K=1 改为读取显式文件路径，避免官方别名写入 home；文档和全部本地检查同步通过。
- 2026-09-29：恢复检查确认 MatterSim 作业 502 已退出队列，wheelhouse 为 125/144；日志在 torch 下载阶段连续连接超时，留下 0 字节 `.partial`。保留全部已校验 wheel，计划在核对最终状态后按既有断点语义重提。
- 2026-09-29：确认无重复 MatterSim 下载作业后，在 node221 将 125/144 wheelhouse 断点重提为作业 507；未删除完整 wheel 或 torch 残片。集群 accounting 已禁用，后续使用 `squeue`、固定日志与哈希清单验收。
- 2026-09-29：持久 SSH 管理会话被跳板机重置后，已登记下一次连接用途；继续只读监控 MatterSim 作业 507，完成前不启动 MACE 下载。
- 2026-09-29：MatterSim 作业 507 已连续运行约 1 小时 31 分，`torch-2.14.0` 残片推进至 343,851,008 bytes；完整 wheel 仍为 125/144，任务健康运行，继续等待完成后做 144 项哈希验收。
- 2026-09-29：完成首个论文数据交付单元：新增 `matbench_phonons` 官方来源/SHA-256 manifest 和标准库校验下载器，覆盖续传、Range 回退、错误哈希与路径逃逸；全套 21 项测试通过。
- 2026-09-29：完成 MACE 论文 v1 的 97-material PhononDB manifest；作者提交树、97 个 MP↔Togo 映射、PBE 标签/超胞与两项来源哈希交叉一致，全套 22 项测试通过。
- 2026-09-29：MatterSim 作业 507 完成 144/144 且服务器独立哈希复验通过；离线 setup 509 随即暴露 torch 2.14 的 Linux 条件依赖缺失。已确认 PyPI 无其精确 NCCL 版本，改为重建显式 torch 2.8.0/CUDA 12.8 闭包。

- 2026-11-02 00:41 +08:00：新增 docs/plan/plan_2.md，工作名称 Sequential Self-Evolution（亦可称 Sequential Test-Time Scaling）。覆盖 CGCNN、Matformer、iComFormer、完整 JARVIS 回归任务清单、pooling 前原子特征全库缓存、额外线性层、逐阶段随机初始化及历史冻结、默认第 0–5 轮/三个 seeds、必要对照、MAE/累计计算曲线、模块接口、测试与 Slurm 阶段。更新当前状态并保留旧 Goal 1 历史；本轮只改文档。

- 2026-11-02T01:09+08:00：完成 CGCNN seed123 本地流程实现：固定 MIT 官方源码/描述符和 JARVIS 2021 元数据、29 任务、周期构图/分组划分、线性投影、完整训练/缓存链、断点与哈希保护、原始输入和累计步数对照、延后测试评测及 MAE/时间曲线；新增独立模块 README、配置与 Slurm 入口。35 项测试和静态检查通过，当前准备提交同步并开展真实服务器验收。

- 2026-11-02T01:19+08:00：setup 878 在 SOCKS→PyPI TLS 阶段以 35 失败，未进入安装。增加校验后的离线 wheelhouse 安装路径，保持原锁定依赖；查明 Figshare API 下载固定文件成功，31 MB ZIP 的官方 MD5/字节数通过。下一步提交该修复，scp 两组约 32 MB 资源后用 Slurm 重试环境和数据准备。

- 2026-11-02T01:24+08:00：SCP 大包被跳板中断后，在未开始任何真实训练时固定服务器现有兼容材料库版本，离线传输缩至 466 KB；本地 8 项验收与静态检查保持通过，下一步传输小包并重提 Slurm setup。模型、训练协议和全任务范围不变。

- 2026-11-02T01:33+08:00：真实setup879通过GPU/8项测试，prepare880下载阶段因代理断线失败，未进入构图。修复构建工具元数据并支持经MD5/大小验证的SFTP staging，准备用reput断点传输完整ZIP；模型训练尚未开始。

- 2026-11-02T01:44+08:00：8项离线资源与完整JARVIS ZIP经SFTP大小核对已到服务器，metadata setup881和prepare882已提交。真实构图前补齐任务/图dataset SHA一致门控及builder来源绑定，36项回归通过；将用新prepared根路径执行最终预处理，旧882产物保留而不冒用新来源身份。

- 2026-11-02T01:58+08:00：887审计确认raw55723、unique55712、5个重复ID；4个重复ID完全一致，JVASP-97311仅形成能有冲突。实现同ID同结构规范化和按任务排除冲突标签，保留全库结构、原始位置/记录hash/冲突数值，manifest同时固定raw/unique/重复与冲突ID。39项测试通过，下一步重新提交全库prepare及同配置pilot。

- 2026-11-02T02:12+08:00：真实环境888通过12项集成测试；889完成55712结构、0失败、29任务全部就绪，审计包含11行重复合并及形成能[-1.7139,-1.71102]冲突处理。890 seed123真实训练已开始，第0轮epoch4之前最佳验证MAE0.1457127。新增pilot成功后的标签无关CUDA native/batch/cache验收门控，用于自动扩展全29任务第0–5轮和对照；本地仅增加scripts，核心训练协议/源hash不变。

- 2026-11-02T02:15+08:00：全任务作业启动时复核精确环境并单独记录，若继承库变化会显式失败，保护长运行的可复现性；不改变890当前模型与训练预算。

- 2026-11-02T02:21+08:00：890实测到第0轮epoch32、best验证MAE0.07208431；全任务后续链891/892/893已排队并经scontrol确认890→afterok891→afterok892_0–28%1→afterany893。已拉回data_audit/environment/raw_snapshot_audit/jobs/round0_history到忽略的本地outputs证据目录。本轮没有最终测试MAE或完整循环曲线，仍需完成真实两轮和29任务r0–5+对照。

- 2026-11-02T02:32:08+08:00：新增独立CGCNN执行诊断脚本，在复制的checkpoint上比较原生pooling与segment候选前向/梯度及算子开销；脚本和文档静态检查通过，尚未执行GPU诊断。核心src/config和890训练未变。

- 2026-11-02T02:35:29+08:00：真实执行诊断通过既定前向/梯度门槛，识别pooling开销，但保留原训练路径以维护正在运行的协议；共享GPU计时不作为完整训练加速结论。890第0轮已62epoch、best验证MAE0.05821373，891/892/893依赖复核有效。已拉回诊断、算子表及最新训练history，目标仍active。

- 2026-11-02T02:37:09+08:00：verified wait，890实测RUNNING并完成第0轮66epoch，尚无第0轮完成标记或第1轮结果。后续三作业依赖等待有效，保留既定训练预算和队列，不重复提交。

- 2026-11-02T02:42:59+08:00：verified wait，890仍运行并完成第0轮78epoch；建立本地55秒间隔持久监控，避免每个状态查询重连，阶段变化自动结束。当前尚无r0缓存或r1，后续依赖有效，训练预算/核心源码不变。

- 2026-11-02T03:09:35+08:00：持续核查890，r0epoch131、best验证MAE0.05133525，后续依赖等待。新增docs/plan/cgcnn_seed123_resources.md记录真实吞吐及完整必要对照成本，明确不早停估算假设和待补齐显存/IO证据，保持完整目标与训练预算。

- 2026-11-02T03:18:02+08:00：新增pilot_resources.py并接入真实验收入口，补齐计划要求的缓存字节/读取与固定批次峰值测量路径，明确零目标代理损失/lr=0模型副本/OS页缓存未知边界；39项本地回归通过，GPU数据待原pilot完成。890最新第0轮149epoch，best验证MAE0.04913135，未重启或改预算。

- 2026-11-02T03:21:00+08:00：服务器已同步ee775bc资源验收实现，现有891会读取更新后的Python入口，无需重提890/891；核心src/config差异为空。890最新r0epoch155、best验证MAE0.04913135，完整研究实验仍未完成。

- 2026-11-02T03:46:18+08:00：新增execution_pool.py、pool.sbatch及Slurm CPU检查入口；8波覆盖29任务，每波最多4进程共享一GPU、随后串行评测，实际并发由真实最大批次显存/CPU/主机内存门控；单波时限21天，不改任务模型/训练预算。45项本地回归通过，6项调度最终复核通过。原正式队列未动，待Linux检查与源码同步后切换受afterok891保护的pending任务。

- 2026-11-02T04:05:23+08:00：进入真实第1轮：第0轮222epoch/154734步完成，best验证MAE0.04822800，全库55712/562055节点缓存147579938字节、12.91秒，16结构缓存/链一致性通过。Linux894通过18项CPU集成后，将旧pending892迁移为895八波资源门控pool，先核验893重接再取消旧数组，未动890。已拉回checkpoint关联元数据、training/history/cache_timing/链核查和迁移/CPU日志，新observer96216监控第1轮，目标仍active。

- 2026-11-02T04:31:51+08:00：补齐plan_2第5节缓存交付字段，以SHA绑定补充manifest保留基础缓存身份；公开评测预先验证全部对照，CUDA子进程逐次复核环境。46项本地回归通过，不改src/config或运行中权重。r1最新epoch69、best验证MAE0.04456512；后续891/895/893依赖有效，下一步Slurm CPU复核并同步新入口。

- 2026-11-02T04:40:34+08:00：补充缓存manifest和完整对照预检已同步并通过Slurm896的19项CPU集成（本地46项亦通过）。入口896a171不改变原缓存/权重/训练身份；真实全库校验待891/后续任务。r1最新85epoch、best验证MAE0.04418608，891/895/893依赖仍有效。

- 2026-11-02T05:02:38+08:00：verified wait，第1轮实际推进到128epoch，best验证MAE0.04402161；尚未完成训练/缓存，真实891与完整矩阵仍待，不以排队或已有本地测试替代完成。observer96216继续运行，计算/训练协议无变更。

- 2026-11-02T05:57:29+08:00：真实两轮pilot与891全部成功（r0验证0.04822800、r1验证0.04402161，非测试结果）；两轮全库缓存及补充manifest/全分片审计已核验。资源报告支持4并发，895_0实际启动形成能对照、带隙/总能/ehull基线，日志/PID/history均在推进。已拉回完整小型验收/资源/来源证据；矩阵observer8154继续工作，全部29任务r0–5/对照及测试曲线尚未完成。


- 2026-11-02T06:14:57+08:00：新增scripts级可选任务分组：按有效标签数均衡未启动wave，保护全部已有ledger，绑定配置/源数据/图/审计SHA并记录到最终汇总。运行中wave0及src/config保持不变。本地49项通过，最终接口3项重验通过；Slurm复核及实际发布待完成。


- 2026-11-02T06:17:54+08:00：调度入口aae5124已推送并Guqq代理pull；Slurm898固定日志确认22 passed in 6.92s。候选runtime分组经SHA/来源/配置/全部既有ledger校验后原子发布，SHA 8c3cf7f017ccf2794584db01c8dc55dcd8c5d54c86a3904736cbb5f2048ebfcb；唯一已有wave000成员原样保护，895不取消/不重提，未来wave读取新分组，893依赖不变。最新实际观测2026-11-02T06:17:30.378172+08:00四任务持续训练、无failure、0/29报告完成；完整目标仍active。


- 2026-11-02T06:21:42+08:00：上一goal turn为progress（aae5124调度及运行时分组发布）；本轮为verified wait，通过工具会话8154重复读取实际SSH/squeue与训练history，最新2026-11-02T06:21:10.398471+08:00确认895_0/job897仍RUNNING。formation_energy_peratom controls/original/round_001 epoch117/steps81549；optb88vdw_bandgap round_000 epoch120/steps83640；optb88vdw_total_energy round_000 epoch115/steps80155；ehull round_000 epoch116/steps80388。无failure、0/29报告完成，895_1–7仍PENDING；未重启/重提/改预算，完整29项r0–5及对照目标继续active。下一步等待现有训练阶段结束并核验缓存/控制转换。


- 2026-11-02T06:32:17+08:00：上一goal turn为verified wait；本轮继续通过原工具会话8154连续12次有界轮询（约9分钟），实际squeue/history确认895_0/job897持续RUNNING。最新2026-11-02T06:32:10.491264+08:00：formation_energy_peratom epoch139、optb88vdw_bandgap epoch142、optb88vdw_total_energy epoch136、ehull epoch139；无failure，0/29完整报告。单次无输出后续查同一handle得到新进展，未重启/重提/改配置。当前阶段未转换，继续等待既有训练并核验完成后的缓存/对照；完整目标仍active。


- 2026-11-02T06:41:36+08:00：上一轮为verified wait，本轮续查原observer8154并核对真实资源；Slurm897仍RUNNING，最新2026-11-02T06:41:20.594669+08:00为formation_energy_peratom epoch157、optb88vdw_bandgap epoch161、optb88vdw_total_energy epoch154、ehull epoch157，无failure、0/29报告。短时Slurm srun元数据查询实测GPU利用率90%、NVML显存4423/32607MiB，节点CPUAlloc16/48、CPULoad5.65；单点利用率不能证明更高并发收益，因此保持已验证4并发、8波和已发布不可变分组，不改预算或重提作业。下一步等待阶段完成和缓存/对照转换，完整目标仍active。


- 2026-11-02T07:01:24+08:00：上一goal turn为verified wait及资源核查；本轮通过原observer8154连续24次有界轮询、约18分钟verified wait，实际squeue/history持续确认895_0/job897 RUNNING。最新2026-11-02T07:00:35.745747+08:00：formation_energy_peratom controls/original/round_001 epoch195/steps135915；optb88vdw_bandgap round_000 epoch202/steps140794；optb88vdw_total_energy round_000 epoch192/steps133824；ehull round_000 epoch196/steps135828。无failure、0/29完整报告，阶段尚未转换；未改模型、配置、预算或队列。下一步等待既有训练结束并核验全库缓存/对照转换，完整29项r0–5与必要对照目标仍active。


- 2026-11-02T07:37:47+08:00：完成带隙r0阶段转换核验（本轮为持续verified wait后的实际实验progress）。r0按validation patience结束于266epoch/185402步、最佳验证MAE0.1585009272 eV、训练/验证7784.60秒；缓存13.916秒，55712唯一ID集合与已验收全库完全一致、562055原子/64维float32/218分片。checkpoint SHA 2beb0e53…、cache SHA e2820265…与training/timing/root chain/16结构一致性记录相互匹配，config/core/graph身份一致。16结构直接链/缓存最大节点差1.7166e-5，通过固定atol2e-5+rtol1e-4；第1轮已实际训练（拉回初始7epoch历史）。小型证据及本地metadata核验JSON保持Git忽略。最新2026-11-02T07:37:16.037377+08:00四worker仍训练、无failure、0/29完整报告；全29项r0–5/对照/最终测试仍未完成，目标继续active。下一步续查带隙r1、形成能对照及总能/ehull的r0→缓存→r1转换。


- 2026-11-02T09:40:21+08:00：四性质范围实现：显式selected/deferred配置SHA绑定、延期task入口训练前拒绝、report-only view复用固定绘图器、完整0–5轮/两对照及执行状态验证、当前scope完成计数4/其余25延期。完整本地57项通过，ruff format/check通过；无src/config科学身份变化，Slurm CPU与实际scope发布待进行。


- 2026-11-02T09:51:16+08:00：完成用户四性质范围调整。4fb240b已Guqq pull并通过Slurm899全部30项CPU集成（12.01秒），本地57项和最终8项均通过。runtime execution_scope.json SHA ef3595e2a3d20845dca44d5386a0eee5e6bbcb0082c588e65c09041de13ef3a0已校验config及wave000四成员后原子发布，895_1–7取消、895_0/job897继续、893已release且仍afterany895。其他25性质明确deferred，训练核心/预算/seed/全库55712结构缓存不变；当前验收仅四性质0–5轮及必要对照。


- 2026-11-02T09:51:16+08:00：新增真实metadata核验通过：总能r0 300epoch/209100步、best验证MAE0.05124270436、缓存14.027秒；ehull r0 300epoch/207900步、best验证0.11916632863、缓存14.113秒；带隙r1 139epoch/96883步、best验证0.15119843529、缓存9.329秒/86813参数（投影5980）。三份缓存均55712唯一ID/562055原子/64维float32/218分片，完整ID集合、cache/timing/chain/checkpoint/config/core/graph及父缓存身份匹配，固定16结构组合容差检查记录一致。形成能original1为300epoch/209100步、best验证0.04533867818，独立原始输入/相同训练ID与归一化核验通过；累计对照继续，目标269042步。数据/审计JSON均保持Git忽略；最新2026-11-02T09:50:22.941194+08:00四任务仍训练、无failure，本阶段完整结果尚未完成。


- 2026-11-02T09:55:54+08:00：完成ehull r1产物核验（本轮progress）。r1按patience结束207epoch/143451步，best验证MAE0.11350609162，训练/验证6198.72秒；全库第二份缓存9.729秒、55712唯一结构/562055原子/64维float32/218分片。checkpoint SHA c7a4f7d3ab6cf44da47d95f7d43839977e642890fffe46b089a8697c4eb27be9、cache SHA 7bfefe867e79e963ca1d58820e0195c6dc2b5431c60a4ba7429c2b4b8f722cc4、父缓存SHA 520e75542644a8881e0e0132de5faa042c8107c108fdf1166816c14aa177e994与chain/timing/config/core/graph匹配；与r0相同训练归一化/ID hash，新增投影5980参数（总86813），累计主链351351步。16结构链探针两阶段最大节点差2.6703e-5/2.8610e-5，按固定atol2e-5+rtol1e-4组合容差通过，不能只与绝对容差比较。小型metadata及审计JSON已拉回并Git忽略。最新2026-11-02T09:54:58.007342+08:00当前四worker仍训练、无failure，四性质完整0–5轮/对照/最终曲线仍未完成。下一步等待总能r1与现有对照，并核验后续转换。


- 2026-11-02T13:38:26+08:00：goal维持用户paused状态，仅响应进度/scaling问题做只读服务器查询（未恢复自动推进，未更改/提交/取消任何训练）。实际2026-11-02T13:36:34.251632+08:00895_0/job897 RUNNING8小时14分、893 PENDING(Dependency)，四性质无failure、无最终测试report。形成能主链r2完成94epoch/65518步、验证MAE0.04341245115、已有3份缓存标记，当前original2对照174epoch；original1验证0.04533867818、累计步数r1对照269042步已完成/验证0.04503066799。带隙r1验证0.15119843529、累计对照186099/282285步；总能r1完成283epoch/197251步、验证0.04670103468、累计对照50184/406351步；ehull r1验证0.11350609162、累计对照108108/351351步。当前只有形成能完成到第2轮，其他到第1轮；全部数值为验证指标，不能据此宣布0–5轮完成或稳定scaling规律。查询快照在Git忽略目录current_status_user_query.json。


- 2026-11-02T16:16:35+08:00：goal维持paused，仅响应用户重复进度/scaling问题做只读查询。实际2026-11-02T16:14:35.180239+08:00895_0/job897 RUNNING10小时52分，893仍PENDING(Dependency)，四性质无failure/无最终test report。形成能r2仍为0.04341245115，original2已完成300epoch/验证0.04497838910，当前cumulative2为116399/334560步。带隙新增r2完成137epoch/95489步，验证0.15229601411，高于r1的0.15119843529（约0.73%）；r1累计步数对照已完成282285步/验证0.15211903219，当前original2对照21epoch。总能cumulative1为255102/406351步，ehull cumulative1为312543/351351步。已完成evolution轮次上限分别2/2/1/1；证据支持r0→r1普遍改善，但更高轮次已出现分化，不能据单seed验证指标宣称单调scaling。上一查询快照已归档到忽略目录status_queries。未提交/修改任何训练或恢复自动推进。


- 2026-11-02T16:36:04+08:00：仅响应用户ETA问题，goal继续paused，未修改训练/配置/调度。使用2026-11-02T16:33:19.974709+08:00真实活动步数和最近10epoch测得约32.24–32.64秒/epoch；四任务并行按最慢任务剩余墙钟估算，包含0–5轮/原始输入/累计步数两类对照，后续original对照按300epoch。情景为后续演化阶段100epoch：剩余45.80小时、预计2026-11-04T14:21:33.963184+08:00，瓶颈optb88vdw_total_energy；后续演化阶段150epoch：剩余52.07小时、预计2026-11-04T20:37:44.513034+08:00，瓶颈optb88vdw_total_energy；后续演化阶段200epoch：剩余58.34小时、预计2026-11-05T02:53:55.062884+08:00，瓶颈optb88vdw_total_energy；后续演化阶段300epoch：剩余70.88小时、预计2026-11-05T15:26:16.162583+08:00，瓶颈optb88vdw_total_energy。未来演化阶段早停未知，100/150/200/300为情景假设而非停止时间承诺；不含最终统一评测/绘图，假设资源吞吐不变且无重启。150epoch情景约52小时（11月4日晚），300epoch情景约71小时（11月5日下午）；后续应按实测轮次更新。


- 2026-11-02T22:07:59+08:00：goal继续paused，仅响应用户进度/scaling问题只读查询。实际2026-11-02T22:06:15.584708+08:00895_0/job897 RUNNING16小时44分，893 PENDING(Dependency)，四任务无failure/无测试report。形成能主链完成r3（98epoch/68306步、验证0.04334152541），r2→r3改善约0.163%；当前original3对照241epoch。带隙主链到r2，cumulative2进度256496/377774步。总能新增r2完成99epoch/69003步、验证0.04668207961，r1→r2仅改善约0.041%；当前cumulative2为24395/475354步。ehull新增r2完成147epoch/101871步、验证0.11466172945，比r1回升约1.018%；当前cumulative2为107415/453222步。带隙r2比r1回升约0.726%。四性质r1均优于已完成matched-step对照，但更深轮次已表现任务相关的边际递减/波动；单seed验证证据不足以宣称稳定scaling规律。未修改/提交任何训练、未恢复自动推进。


- 2026-11-02T22:32:14+08:00：用户要求实际暂停训练，现已完成停训管理阶段。先hold893并在现有Slurm897内CPU加载验证四份last/best/config、模型/optimizer/RNG及完整epoch字段，复制恢复备份；首次scancel897返回0仍RUNNING，复核后改scancel --verbose895_0，实际2026-11-02T22:23:42+08:00确认JobState=CANCELLED/ExitCode0:15，所有895训练元素消失、原四worker及launcher PID退出，资源释放。893保持JobHeldUser。原始checkpoint/全部缓存/数据/日志保留，wave/context已标paused并记录暂停前已发生墙钟成本。formation_energy_peratom controls/original/round_003 已校验备份epoch265/steps184705；optb88vdw_bandgap controls/cumulative/round_002 已校验备份epoch392/steps273224；optb88vdw_total_energy controls/cumulative/round_002 已校验备份epoch60/steps41820；ehull controls/cumulative/round_002 已校验备份epoch179/steps124047。暂停账本及备份已SFTP到本地并复核last/best SHA及config身份，生成物全部Git忽略。当前四性质0–5轮未完成，整体goal为paused而非complete；旧连续运行ETA失效，不自动恢复训练。恢复须明确授权、保持core/config身份，并将held893依赖改到新job后再release。

- 2026-11-02T23:39:53+08:00：完成独立CGCNN残差验证实现：src/residual_scaling分为protocol/cache/training/pipeline/reporting，三组共用旧R0、复用direct R1/R2、两新分支严格匹配实际步数和seed，eta1且固定R0统计。增加成对节点/累计预测归档、恢复/身份校验、验证曲线、独立Slurm CPU/GPU门禁和最多4 worker调度。全62项本地回归及静态检查通过；旧核心/配置未改，旧0–5/893继续暂停。计划docs/plan/residual_scaling_validation.md。
