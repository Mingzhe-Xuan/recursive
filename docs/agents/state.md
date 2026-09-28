# 当前状态

Goal 1 的通用递归核心以及 MatterSim、MACE、DPA-2 三个 wrapper 已完成本地实现，16 项测试通过。Guqq 的 `~/recursive` 已同步至提交 `b41299f`，remote 和仓库根目录验证通过；Python 为 3.10.12，GPU 为 RTX 5090，Slurm 分区为 `compute`。三个真实 checkpoint 的验收脚本和 Slurm 文件均已准备。当前风险是根分区仅余约 2.6 GiB，需先确认安全的环境、缓存和 checkpoint 存储位置。

# 当前计划

1. 检查服务器挂载点、用户配额和任务相关缓存占用，选择容量足够且不覆盖既有数据的环境/checkpoint 目录。
2. 创建并记录任务专用虚拟环境，下载官方 checkpoint，通过 Slurm 依次跑 MatterSim、MACE、DPA-2 的 K=0/K=1。
3. 将 job ID、日志、版本、checkpoint checksum 和结果 JSON 同步回本地并完成验收记录。
4. 随后下载论文对齐数据集并进入递增 depth scan。

# 变更记录

- 2026-09-28：进入 Guqq SSH 连接故障诊断阶段；用户报告配置反向 SOCKS 后无法连接。下一步是复现连接并根据详细 SSH 日志定位失败阶段。
- 2026-09-28：进入 SSH 会话级反向 SOCKS 转发配置阶段；用户要求每次 `ssh Guqq` 自动转发、断开后自动停止，并明确跳过 `net.sh` 和 180 秒等待。下一步是备份并最小化修改本地 SSH 配置，然后执行连接生命周期测试。
- 2026-09-28：完成 SSH 会话级反向 SOCKS 配置和验证；Guqq 经 `127.0.0.1:1080` 获得的出口 IP 与本地一致，并在会话退出后拒绝连接。测试同时发现 Guqq 的 `/home/xmz/recursive` 已不存在；后续服务器实验需先恢复工作树。
- 2026-09-28：开始修订 Guqq 网络操作规范；原因是会话级反向 SOCKS 已实测可用，不再需要 `bash net.sh` 和固定 180 秒等待。下一步是修改 `AGENTS.md` 并检查命令、路径、Markdown 和旧流程残留。
- 2026-09-28：完成 Guqq 网络操作规范修订；`AGENTS.md` 现要求登录节点联网命令显式使用会话级 SOCKS，禁止运行 `bash net.sh` 和固定等待，并区分了登录节点与 Slurm 计算节点的网络边界。
- 2026-09-28：用户确认网络已重新配置并要求继续；已重读更新后的 `AGENTS.md`，SSH/反向 SOCKS 故障诊断阶段结束。下一步按新规范恢复服务器仓库并检查运行环境。
- 2026-09-28：服务器仓库同步成功并完成轻量资源检查；发现 `/` 仅余约 2.6 GiB，直接创建三个环境和下载模型有耗尽磁盘风险。下一步只读查找可用挂载点与任务相关占用，再确定环境布局。

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
