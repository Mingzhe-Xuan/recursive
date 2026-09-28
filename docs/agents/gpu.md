# GPU/服务器连接记录

- 2026-09-28：计划连接 `Guqq`，用途是确认服务器 Git 工作树位置、远端同步状态、Slurm 分区和可用环境，以便后续提交 MatterSim 原生推理与 K=1 作业。该用途属于允许的轻量管理检查；不在登录节点运行训练、推理、评测、编译或批量处理。
- 2026-09-28：再次连接 `Guqq`，用途是按网络故障流程先运行 `bash net.sh` 并等待 3 分钟，再尝试 `git pull`、确认正确仓库路径与 Slurm 状态。仅执行轻量管理操作，不在登录节点运行模型。
- 2026-09-28：计划在沙箱外重试 `Guqq`，原因是沙箱内 `ssh -G` 没有加载用户 SSH alias 配置且把主机名直接解析为 `guqq`。连接成功后的第一项远端操作仍为 `bash net.sh`，随后等待 3 分钟；仅处理网络、Git 路径和 Slurm 轻量检查。
- 2026-09-28：网络恢复流程完成后新建轻量检查连接；先在默认目录执行 `git pull`，再只读查找 home 下的 Git 工作树并查看 `sinfo`，以确定代码同步位置和可用 Slurm 分区。
- 2026-09-28：新建仓库身份核对连接；先执行 `git pull`，再只读查看候选仓库的 remote、分支和顶层文件，确认是否存在与本地 `recursive` 对应的工作树，不作服务器源码修改。
- 2026-09-28：重试仓库身份核对；上次命令被本地 PowerShell 提前展开远端循环变量，本次改用受保护的远端 shell 字符串。仍先执行 `git pull`，随后只读查询，不修改服务器文件。
- 2026-09-28：计划连接 `Guqq` 同步已确认的 `https://github.com/Mingzhe-Xuan/recursive.git`。连接后的第一项远端操作为对 `~/recursive` 执行 `git pull`；若工作树尚不存在，则随后 clone。之后仅创建任务专用虚拟环境、下载官方 checkpoint，并通过 Slurm 提交 MatterSim、MACE、DPA-2 的 K=0/K=1 验收，禁止在登录节点运行模型推理。
- 2026-09-28：上次连接首先执行 `git -C ~/recursive pull`，返回目录不存在。计划再次连接；仍首先尝试同一 `git pull`，确认失败后 clone `https://github.com/Mingzhe-Xuan/recursive.git` 到 `~/recursive`，随后只做仓库同步和环境管理，不在登录节点运行推理。
- 2026-09-28：服务器已从确认的 remote clone 到 `~/recursive`。计划再次连接并首先执行 `git pull`，随后只读检查 Python、CUDA/驱动、Slurm 分区和可用磁盘，再据此创建任务专用虚拟环境；本次不在登录节点运行模型推理。
- 2026-09-28：计划连接 `Guqq` 验证 SSH 反向动态转发；用户明确要求本次忽略 `bash net.sh` 和 `sleep 180`。连接前先将 `RemoteForward 127.0.0.1:1080` 写入本地 `Host Guqq` 配置，连接后首先执行 `git -C ~/recursive pull`，再仅做 SOCKS 端口和公网出口的轻量测试；不运行计算任务，不修改服务器受 Git 管理的源码。
- 2026-09-28：计划连接 `Guqq` 诊断 SSH 在启用会话级反向 SOCKS 后无法登录的原因。仅执行 SSH 配置展开、详细连接日志和端口转发诊断；不运行 `net.sh`，不在登录节点运行计算任务。若能登录，按规范先检查仓库并执行 `git pull`或确认需要 clone。
- 2026-09-28：重新读取更新后的 `AGENTS.md` 后计划连接 `Guqq` 恢复项目工作树。先检查 `~/recursive`：存在则第一项执行带 `socks5h://127.0.0.1:1080` 代理的 `git pull`，不存在则通过同一代理 clone 已确认的 remote；随后仅做仓库、Python、GPU、Slurm 和磁盘的轻量检查，不在登录节点运行推理或编译。
- 2026-09-28：上次连接已成功 pull 并验证服务器仓库。计划再次连接：首先在 `~/recursive` 执行代理 `git pull`，随后只读检查各挂载点、用户配额及 home 下任务相关缓存/环境占用，为三个隔离环境和 checkpoint 选择安全目录；不删除数据、不运行推理或编译。
