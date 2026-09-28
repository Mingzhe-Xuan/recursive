# 当前状态

Goal 1 的通用递归核心、MatterSim M3GNet wrapper 和 MACE-MP-0 small L=0 wrapper 已完成本地实现。norm alignment 已覆盖同一 irrep 类型的多个不连续 packed 段并共享 gamma；当前 13 项测试通过。MatterSim/MACE 的真实 checkpoint 验收脚本和 Slurm 文件已准备。工作区仍不是 Git 仓库；服务器没有对应的 `recursive` 工作树，推测的 `Mingzhe-Xuan/recursive` 远端不存在，因此在取得正确 GitHub remote URL 前无法按规范同步和提交真实推理作业。

# 当前计划

1. 从用户处取得正确 Git remote URL；初始化/关联本地仓库并推送，服务器 clone 或 `git pull` 后创建可复现虚拟环境，通过 Slurm 跑 MatterSim K=0/K=1。
2. 下载并记录 Matbench phonons 数据 manifest/checksum，准备 frozen readout pilot。
3. 审计并实现 DPA-2 wrapper 及对应测试，不以 mock 或前两个模型替代完整目标。
4. 依次完成论文任务的 depth scan、验证集选择与结果记录。

# 变更记录

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
