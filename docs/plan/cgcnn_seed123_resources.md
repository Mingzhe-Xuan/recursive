# CGCNN seed 123：实测耗时与资源估算

当前执行范围已由用户收敛为首组四性质0–5轮及既定对照，其他25项延期；以下29任务资源估算是历史长期矩阵参考，不是当前仍在排队的工作量。895_1–7已取消，运行中895_0/job897保留。

范围对应 [plan_2](plan_2.md) 的 CGCNN 单 seed 子集：29 个任务，seed 123，第 0–5 轮，以及原始输入重训和累计优化步数对照。固定预算见 [配置](../../configs/self_evolution/cgcnn_seed123.json)，实际阶段状态见 [state](../agents/state.md)。此记录不调整训练预算或验收范围。

## 已测量的部分

RTX 5090、固定 batch 64 的 formation energy 第 0 轮，已拉回的 62 个完成 epoch 累计训练/验证墙钟为 1904.69 秒，平均 **30.72 秒/epoch**。证据是忽略目录 `outputs/self_evolution/cgcnn-seed123-evidence/round0_history.json`。准备阶段另耗时 116.02 秒，55712 个结构全部成功构图。

隔离共享 GPU 固定批次诊断测得 native 单步 19.316 ms、segment 候选 10.133 ms；这两个数既不是完整 epoch 吞吐，也不能用来折减当前生产实验预算。生产路径保持原生 pooling。

## 完整矩阵的数量级参照

若一个任务每个演化阶段和原始输入对照都训练满 300 epoch，前六阶段的累计优化步数对照按实际总步数匹配，则单任务最多对应：

- 演化链：6 个单阶段预算；
- 原始输入独立重训：5 个单阶段预算；
- 累计步数对照：2+3+4+5+6=20 个单阶段预算。

合计 **31 个单阶段预算**，即 9300 个 epoch 等价的优化步数。该算式约束的是优化步数；验证频率和部分 epoch 会影响墙钟开销。

以当前 formation energy 的平均 epoch 墙钟直接外推，满 300 epoch 单阶段约 **2.56 小时**，完整单任务约 **79.36 小时（3.31 天）**。任务脚本申请的时限为 [7 天](../../scripts/slurm/self_evolution/task.sbatch)，此估算不能保证作业一定在时限内结束；已有逐 epoch checkpoint 可用于核验身份后的恢复。

29 项有效标签合计 **801007**，formation energy 为 **55711**。进一步假设所有任务每样本耗时相同、划分比例相近且均训练满预算，用有效标签量同比例外推，得到约 **47.5 天的串行训练/验证墙钟参照**。它不是严格上界或完成时间承诺：early stopping 会减少步数，结构原子数、训练/验证实际划分、缓存 IO、CPU 调度和任务本身会改变吞吐；全库缓存、链验收、部署计时及报告还会增加成本。该数字也不是实测 GPU 忙碌时间。

## 待 pilot 完成后补齐

第 0/1 轮训练完成后，结合 `training.json`、`cache_timing.json`、缓存 manifest 和 `chain_verification.json` 核对实际训练步数、缓存耗时与字节数。已有验收入口将调用 [pilot_resources.py](../../scripts/self_evolution/pilot_resources.py)，在 Slurm 中对两个独立模型副本测量固定批次代理训练步骤、PyTorch allocator 峰值、首次校验图/缓存读取及设备传输，写出 `pilot_resources.json`；真实 GPU 结果仍待 pilot 完成。该脚本不读取标签，lr=0，仅更新副本的优化器状态和 BN buffer；峰值限于诊断批次，读取耗时包含校验/反序列化/拼接，OS 页缓存状态未知，不能冒充整轮训练峰值或裸盘带宽。完整链部署计时在正式链完成后生成。当前尚无真实跨轮 MAE 曲线，不用验证集训练轨迹代替最终测试结果。

## 独立任务并行入口

串行参照提示完整矩阵成本较大。节点实测为 48 CPU 核、约 252 GiB 内存，当前原生训练进程 RSS 约 3 GiB；Linux `MemAvailable` 约 228.5 GiB，不能用约 2.8 GiB 的 `MemFree` 误判可用内存。另提供 [pool.sbatch](../../scripts/slurm/self_evolution/pool.sbatch)：29 任务分为 8 组，每组最多 4 个独立训练进程，共享所申请的同一个 GPU allocation。各任务的 seed、原生算子、阶段数、batch 和优化预算保持原配置。

资源验收会额外探测全库中原子数最大的一个完整批次，测量第 0/1 轮副本的 reserved 峰值。调度入口在启动时校验真实验收、资源 SHA、配置、核心代码和图身份；以每进程 `2 × peak_reserved + 1 GiB`、总量不超过 75% GPU 内存、CPU/主机内存规划选择 1–4 并发。最大批次 OOM 会明确记录并退回单进程；该保守余量不是任意后续批次的绝对内存保证。

每组全部训练退出后才串行评测/部署计时，保留独占 GPU 计时口径；共享训练墙钟须带执行条件解读，不能当作孤立模型的 GPU 忙碌时间。每组申请 16 CPU、64 GiB、1 GPU，时限 21 天，以容纳退回单进程时的一组任务。计划中的训练预算并未增加；并行速度必须据实测报告，不能将 47.5 天直接除以并发数作为承诺。旧 task array 与 pool 只启用一种，替换时保留作业 ledger 和汇总依赖。

## 第 0 轮完成后的实测记录（2026-11-02T04:02:53+08:00）

formation energy 第 0 轮按 validation patience 停在 **222 epoch / 154734 步**，最优验证 MAE **0.04822800 eV/atom**，训练/验证累计 **6698.23 秒（1.86 小时）**。这些是验证指标，测试评估仍延后到完整预设链与对照完成。

全库缓存已完成：**55712 结构、562055 原子、64 维 float32、218 分片**；远端完整缓存目录轻量统计为 **147579938 字节（140.74 MiB）**，包含分片及元数据，生成/校验累计 **12.91 秒**。缓存生成路径逐片校验完成后已进入第 1 轮。缓存/直接链在 16 个固定结构的数值检查通过（atol=2e-5、rtol=1e-4），节点最大绝对误差 **6.1988831e-06**；该一致性探针的覆盖范围是 16 个结构。

小型证据已拉回 `outputs/self_evolution/cgcnn-seed123-evidence/`，包括 `round0_training.json`、`round0_cache_timing.json`、`chain_manifest_round0.json`、`chain_verification_round0.json`、`pool_migration.json` 和 `pool_check_894.out`，均保持 Git 忽略。正式队列现为 **890 → afterok 891 → afterok 895（8 波）→ afterany 893**，旧 pending 892 已取消；Slurm894以 ExitCode0:0 完成18项CPU集成检查。真实GPU资源报告仍待第1轮完成后的891，不能提前声称已测。

## 两轮验收与并发启动（2026-11-02T05:49:31+08:00）

r1按patience结束于164epoch/114308步，训练/验证5231.45秒，best验证MAE0.04402161 eV/atom。完整缓存55712结构/562055原子，147595808字节，8.13秒。Slurm890/891均ExitCode0:0，891在32结构通过官方native/wrapper、单结构/批量及两阶段链/缓存检查，容差仍atol2e-5/rtol1e-4；这是组合容差，节点绝对最大差4.5776e-5不能单独与atol比较。尚未进行最终预设轮数的测试评估。

真实独立副本测量：代表批次64结构/699原子，第0/1轮reserved均150MiB；最大原子数批次64结构/5238原子，第0/1轮reserved均672MiB，allocated约525.5/528.7MiB。均为指定批次代理步骤的PyTorch allocator统计，不是全训练峰值。缓存首次校验读取/拼接约0.184秒（代表r1）和0.090秒（最大批次r1），OS页缓存未知，不作为裸盘带宽。

895_0（实际job897）按真实报告选择4并发，四个训练进程及每任务历史已确认。初始短窗口每任务每epoch约28–31秒，与原单任务约30秒同量级；任务/阶段与数据不同，不能将其视作整个矩阵严格4倍加速。全部训练结束后才串行评测。验收/资源/补充manifest SHA已在本地核验并保存在忽略的证据目录。

## 未启动分组的工作量均衡

保留已启动第0组全部4项任务，仅把其余25任务按当前数据审计中的有效标签数降序排列，仍保持8组、每组最多4任务和最后1项。来源/配置/图/审计SHA绑定的运行时分组文件由 [task_schedule.py](../../scripts/self_evolution/task_schedule.py) 校验；任何已存在wave ledger的成员变化都会拒绝。模型、任务seed、训练预算、缓存链和测试规则均不变。

用每组最大有效标签数之和作为barrier工作量代理，原顺序288676，均衡后223656，减少约22.5%。该指标忽略early stopping、原子数和共享资源竞争，不能当作实测加速。先完成本地回归及Slurm CPU检查，再发布运行时调度文件；既有第0组继续原进程，后续排队wave启动时读取分组，无需取消或重提数组。


实际启用记录（2026-11-02T06:17:54+08:00）：本地49项、Slurm898的22项CPU检查通过，入口aae5124已同步。运行时`<work>/run/pool/task_schedule.json` SHA `8c3cf7f017ccf2794584db01c8dc55dcd8c5d54c86a3904736cbb5f2048ebfcb`，发布前后全部既有ledger检查通过（仅wave000）；排队895_1–7继续原数组，不重启895_0，893仍依赖整个数组完成。第1待启动组为kpoint_length_unit、encut、magmom_oszicar、epsx；原始任务命名空间/种子不变。


并发复核（2026-11-02T06:41:36+08:00记录）：首组4任务运行时，在当前Slurm897 allocation中以短时srun查询nvidia-smi元数据，GPU utilization单点为90%，NVML memory.used/total为4423/32607MiB；scontrol节点CPUAlloc16/48、CPULoad5.65。NVML总显存口径与PyTorch可用设备内存口径不同，此值不替换既有资源门控。单点利用率既不是SM占用率，也不足以估计8并发吞吐，因此保留已验收4并发，没有进一步更改资源申请/波次/任务成员。


## 带隙第0轮完成（2026-11-02T07:37:47+08:00记录）

optb88vdw_bandgap在四任务共享GPU条件下按patience结束于266epoch/185402步，训练/验证累计7784.60秒，best验证MAE **0.15850093 eV**。全库缓存55712结构/562055原子/64维float32/218分片，13.916秒；checkpoint SHA `2beb0e53ec60ee20d6cf4a6975bd9a17aefd8b25f08b5c43080817fc22b857e6`，cache manifest SHA `e2820265d07b557e6730db45559470b4b262bc264dc4f9ecd312234bb7e481a3`。小型证据已拉回`outputs/self_evolution/cgcnn-seed123-evidence/optb88vdw_bandgap/`，metadata审计的完整ID覆盖/身份绑定通过。16固定结构链探针最大节点差1.7166e-5，在固定组合容差内通过；此探针不等同全库逐结构直接链数值对照。第1轮已实际训练，测试评估仍延后。


- 2026-11-02T09:51:16+08:00：完成用户四性质范围调整。4fb240b已Guqq pull并通过Slurm899全部30项CPU集成（12.01秒），本地57项和最终8项均通过。runtime execution_scope.json SHA ef3595e2a3d20845dca44d5386a0eee5e6bbcb0082c588e65c09041de13ef3a0已校验config及wave000四成员后原子发布，895_1–7取消、895_0/job897继续、893已release且仍afterany895。其他25性质明确deferred，训练核心/预算/seed/全库55712结构缓存不变；当前验收仅四性质0–5轮及必要对照。


- 2026-11-02T09:51:16+08:00：新增真实metadata核验通过：总能r0 300epoch/209100步、best验证MAE0.05124270436、缓存14.027秒；ehull r0 300epoch/207900步、best验证0.11916632863、缓存14.113秒；带隙r1 139epoch/96883步、best验证0.15119843529、缓存9.329秒/86813参数（投影5980）。三份缓存均55712唯一ID/562055原子/64维float32/218分片，完整ID集合、cache/timing/chain/checkpoint/config/core/graph及父缓存身份匹配，固定16结构组合容差检查记录一致。形成能original1为300epoch/209100步、best验证0.04533867818，独立原始输入/相同训练ID与归一化核验通过；累计对照继续，目标269042步。数据/审计JSON均保持Git忽略；最新2026-11-02T09:50:22.941194+08:00四任务仍训练、无failure，本阶段完整结果尚未完成。


- 2026-11-02T09:55:54+08:00：完成ehull r1产物核验（本轮progress）。r1按patience结束207epoch/143451步，best验证MAE0.11350609162，训练/验证6198.72秒；全库第二份缓存9.729秒、55712唯一结构/562055原子/64维float32/218分片。checkpoint SHA c7a4f7d3ab6cf44da47d95f7d43839977e642890fffe46b089a8697c4eb27be9、cache SHA 7bfefe867e79e963ca1d58820e0195c6dc2b5431c60a4ba7429c2b4b8f722cc4、父缓存SHA 520e75542644a8881e0e0132de5faa042c8107c108fdf1166816c14aa177e994与chain/timing/config/core/graph匹配；与r0相同训练归一化/ID hash，新增投影5980参数（总86813），累计主链351351步。16结构链探针两阶段最大节点差2.6703e-5/2.8610e-5，按固定atol2e-5+rtol1e-4组合容差通过，不能只与绝对容差比较。小型metadata及审计JSON已拉回并Git忽略。最新2026-11-02T09:54:58.007342+08:00当前四worker仍训练、无failure，四性质完整0–5轮/对照/最终曲线仍未完成。下一步等待总能r1与现有对照，并核验后续转换。


- 2026-11-02T16:36:04+08:00：仅响应用户ETA问题，goal继续paused，未修改训练/配置/调度。使用2026-11-02T16:33:19.974709+08:00真实活动步数和最近10epoch测得约32.24–32.64秒/epoch；四任务并行按最慢任务剩余墙钟估算，包含0–5轮/原始输入/累计步数两类对照，后续original对照按300epoch。情景为后续演化阶段100epoch：剩余45.80小时、预计2026-11-04T14:21:33.963184+08:00，瓶颈optb88vdw_total_energy；后续演化阶段150epoch：剩余52.07小时、预计2026-11-04T20:37:44.513034+08:00，瓶颈optb88vdw_total_energy；后续演化阶段200epoch：剩余58.34小时、预计2026-11-05T02:53:55.062884+08:00，瓶颈optb88vdw_total_energy；后续演化阶段300epoch：剩余70.88小时、预计2026-11-05T15:26:16.162583+08:00，瓶颈optb88vdw_total_energy。未来演化阶段早停未知，100/150/200/300为情景假设而非停止时间承诺；不含最终统一评测/绘图，假设资源吞吐不变且无重启。150epoch情景约52小时（11月4日晚），300epoch情景约71小时（11月5日下午）；后续应按实测轮次更新。


- 2026-11-02T22:32:14+08:00：用户要求实际暂停训练，现已完成停训管理阶段。先hold893并在现有Slurm897内CPU加载验证四份last/best/config、模型/optimizer/RNG及完整epoch字段，复制恢复备份；首次scancel897返回0仍RUNNING，复核后改scancel --verbose895_0，实际2026-11-02T22:23:42+08:00确认JobState=CANCELLED/ExitCode0:15，所有895训练元素消失、原四worker及launcher PID退出，资源释放。893保持JobHeldUser。原始checkpoint/全部缓存/数据/日志保留，wave/context已标paused并记录暂停前已发生墙钟成本。formation_energy_peratom controls/original/round_003 已校验备份epoch265/steps184705；optb88vdw_bandgap controls/cumulative/round_002 已校验备份epoch392/steps273224；optb88vdw_total_energy controls/cumulative/round_002 已校验备份epoch60/steps41820；ehull controls/cumulative/round_002 已校验备份epoch179/steps124047。暂停账本及备份已SFTP到本地并复核last/best SHA及config身份，生成物全部Git忽略。当前四性质0–5轮未完成，整体goal为paused而非complete；旧连续运行ETA失效，不自动恢复训练。恢复须明确授权、保持core/config身份，并将held893依赖改到新job后再release。
