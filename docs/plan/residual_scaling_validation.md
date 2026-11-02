# CGCNN 残差验证：四性质、seed123、0–2轮

用户授权比较三个方案：direct（当前特征回灌、预测完整标签）、raw_residual（原始原子特征的残差累加）、feature_residual（上一轮节点特征的残差累加）。范围固定为formation_energy_peratom、optb88vdw_bandgap、optb88vdw_total_energy、ehull。旧0–5轮实验和893汇总继续暂停；新实验使用独立outputs/residual_scaling目录。

## 固定协议

- 三组共享各性质已完成的同一个R0 checkpoint、55712结构库、图/标签版本、train/val/test划分和R0训练集归一化。
- direct的R1/R2已完成，读取并核验旧checkpoint/cache，不重复训练、不改旧产物。
- 两种残差方案各轮优化步数严格等于同性质direct对应轮实际步数；不提前减少预算，仍按该轮训练中验证MAE选择checkpoint。
- 模型、Adam/.001/weight_decay0、batch64、原生CGCNN算子、shuffle算法不变；每轮复用direct记录的初始化seed。保留原生随机初始化，暂不增加零头初始化、raw特征旁路或全局联合微调。
- 固定eta=1以隔离“残差目标＋输出累加”的影响，不做额外系数搜索。F0=mu+sigma*model0，Fr=F(r-1)+sigma*g_r；训练loss=((Fr-y)/sigma)^2，mu/sigma固定为R0训练统计。所有旧模型冻结。
- raw_residual的新模型只消费原始原子特征和图；feature_residual消费本分支上一轮64维节点缓存和同一图。原始输入＋缓存拼接另属后续消融，本次不混入。
- 最优checkpoint仅从实际训练epoch>=1选择，不把历史模型/eta=0回退当作新轮次，从而不人为制造单调验证曲线。
- 各轮在全库缓存节点特征和累计预测，严格绑定checkpoint/parent/config/代码/图SHA、原子顺序、ID覆盖、dtype与分片字节。预测单位为原始物理单位。
- 本次用于方案筛选，只报告验证集曲线、优化步数/参数量/真实训练及缓存墙钟。测试集不用于训练、标准化、早停、系数调参或这次比较；单seed不宣称统计显著。

## 模块与接口

新代码位于src/residual_scaling，避免改变旧self_evolution的核心hash和恢复身份。

| 目录 | 职责与接口 |
| --- | --- |
| protocol | study配置、固定预算/seed、旧R0–2只读导入审计、实现与源数据身份 |
| cache | 同一分片保存节点特征＋累计预测；publish/open/get/verify及原子恢复 |
| training | 固定步数残差训练、累计验证MAE、checkpoint/optimizer/RNG恢复 |
| pipeline | 共享R0、direct归档导入、两残差分支0→1→2、直接链/缓存一致性 |
| reporting | 四性质三方案验证曲线、CSV/JSON、参数/预算/耗时和失败覆盖 |
| scripts/residual_scaling | CLI、CPU/GPU验收、单GPU最多4独立worker调度 |
| scripts/slurm/residual_scaling | CPU检查、真实GPU验收、正式实验/汇总入口 |

每目录有README。旧src/self_evolution和configs/self_evolution不修改。

## 验收与执行

先完成CPU合成三轮集成：算术/单位正确、预算/seed匹配、恢复等价、零残差保留累计预测、旧权重/BN/cache冻结、全ID/原子数、损坏/错parent/错误协议拒绝、不使用test标签、曲线允许回升。随后本地完整回归＋静态检查，提交/push后Guqq先pull，通过Slurm CPU复核及真实GPU固定结构的直接链/缓存对齐。

正式作业通过Slurm，使用现有专用venv（不改依赖）。先一次性导入/审计旧R0–2并生成累计预测archive，再以最多4独立CUDA worker调度8条新分支，按已知R1+R2预算排序；每条分支内部严格顺序。资源门控复用已核验的旧最大批次测量并校验当前环境。失败保留，不填零、不自动覆盖旧实验。最终检查全部4×3×3个验证点及缓存链、预算和图表后再解释是否改善。

## 固定的正式训练预算

每种残差方案各自执行下表预算（不含共享R0）；direct只读复用。

| 性质 | R1优化步数 | R2优化步数 | 每分支合计 |
| --- | ---: | ---: | ---: |
| formation_energy_peratom | 114308 | 65518 | 179826 |
| optb88vdw_bandgap | 96883 | 95489 | 192372 |
| optb88vdw_total_energy | 197251 | 69003 | 266254 |
| ehull | 143451 | 101871 | 245322 |

两种方案总计1767548个新optimizer updates、八条分支、16个新训练阶段。预算来自已完成direct training.json，运行时仍逐项校验，不以本表代替来源身份。以旧四worker实测约32秒/epoch粗估约6小时，当前实现/争用吞吐不同，正式开始后按实测更新。
