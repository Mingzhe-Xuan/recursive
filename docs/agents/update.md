# 进度更新

- 2026-09-28：开始诊断启用 `RemoteForward 127.0.0.1:1080` 后 `ssh Guqq` 无法连接的问题，优先检查远端端口占用与 `ExitOnForwardFailure yes` 的组合影响。
- 2026-09-28：开始修改 `AGENTS.md` 中的 Guqq 网络流程，将强制 `bash net.sh` 与 3 分钟等待替换为仅在 SSH 会话期间存活的本地反向 SOCKS 代理。
- 2026-09-28：完成 `AGENTS.md` 修订：增加登录节点 SOCKS 环境变量示例和会话生命周期说明，删除 `net.sh`/180 秒流程，增加转发故障诊断、禁止对外暴露端口以及 Slurm 计算节点不继承回环代理的约束。
- 2026-09-28：开始配置本地 `Host Guqq` 的 SSH 反向动态转发，目标为连接时自动提供 Guqq 本机 `127.0.0.1:1080` SOCKS5 端口，断开时由 SSH 自动回收；本次按用户明确要求跳过 `net.sh` 和等待。
- 2026-09-28：完成 `Host Guqq` 反向 SOCKS 配置。`ssh -G Guqq` 确认动态 `RemoteForward` 和会话参数生效；本地与 Guqq 代理出口均为 `3.1.58.103`；会话退出后在禁用新转发的检查连接中确认 `127.0.0.1:1080` 拒绝连接。Guqq 上 `~/recursive` 当前不存在，因此每次连接的首项 `git pull` 已尝试但无法执行。
- 2026-09-28：用户确认网络已重新配置；重新完整读取更新后的 `AGENTS.md`，停止旧的 `net.sh`/等待流程，准备使用会话级 SOCKS 恢复服务器工作树并继续 Slurm 验收。
- 2026-09-28：通过会话级 SOCKS 成功将 Guqq `~/recursive` 快进到 `b41299f`，仓库根目录、HEAD 和 remote 均验证通过；确认 Python 3.10.12、RTX 5090 与 `compute` 分区。根分区仅余约 2.6 GiB，环境安装前先检查安全存储位置。

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
