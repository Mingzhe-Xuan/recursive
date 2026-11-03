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

## 2026-11-03 完成结果与解释

独立905执行账本status=complete，八个worker分支均exit_code=0；16个新阶段完成，1767548个新optimizer updates，训练池账本墙钟21547.12秒（5.99小时）。汇总包含完整4×3×3=36个验证点。该计时不冒充GPU独占训练成本或最终汇总的精确Slurm结束时间。当前无新训练运行，旧893仍held。

以下均为seed123验证MAE，原始性质单位，越低越好；三组各性质R0完全共享。

| 性质 | 方案 | R0 | R1 | R2 |
| --- | --- | ---: | ---: | ---: |
| formation_energy_peratom | direct | 0.04822800 | 0.04402161 | 0.04341245 |
| formation_energy_peratom | raw_residual | 0.04822800 | 0.04372176 | 0.04357859 |
| formation_energy_peratom | feature_residual | 0.04822800 | 0.04417591 | 0.04396044 |
| optb88vdw_bandgap | direct | 0.15850093 | 0.15119843 | 0.15229601 |
| optb88vdw_bandgap | raw_residual | 0.15850093 | 0.15502157 | 0.15493573 |
| optb88vdw_bandgap | feature_residual | 0.15850093 | 0.15098937 | 0.15057388 |
| optb88vdw_total_energy | direct | 0.05124270 | 0.04670104 | 0.04668208 |
| optb88vdw_total_energy | raw_residual | 0.05124270 | 0.04541679 | 0.04489824 |
| optb88vdw_total_energy | feature_residual | 0.05124270 | 0.04554739 | 0.04550551 |
| ehull | direct | 0.11916633 | 0.11350609 | 0.11466173 |
| ehull | raw_residual | 0.11916633 | 0.11392108 | 0.11339428 |
| ehull | feature_residual | 0.11916633 | 0.11286440 | 0.11262822 |

两种残差方案的八条分支在R1→R2全部下降，降幅约0.055%–1.142%；direct的带隙与ehull分别回升约0.726%/1.018%。这表明在本次固定seed与预算下，残差累加的后续轮次下降更一致，但大部分增益仍来自R0→R1，未消除边际递减；仅两次递归不支持可持续scale的结论。

按每个方案0–2轮各自最佳验证值比较（避免只拿direct退化后的R2作参照）：形成能仍direct R2最好0.04341245；带隙feature_residual R2=0.15057388，相对最佳direct R1改善0.413%；总能raw_residual R2=0.04489824，相对最佳direct R2改善3.821%；ehull feature_residual R2=0.11262822，相对最佳direct R1改善0.773%。其中总能提升较明显，形成能无优势，带隙/ehull增益小，应保留单seed限制。原始特征残差没有统一优于特征残差，不能据此断言反馈特征无用。

完整性复核：28份全库缓存（12份direct导入＋16份新缓存）均55712结构/562055原子/64维float32，同一ID集合hash；20份直接链检查记录采用原固定atol2e-5+rtol1e-4。逐项检查checkpoint/manifest SHA、source来源、各分支自己的父预测/节点缓存、16阶段预算/seed/R0归一化、最佳累计验证MAE及CSV/JSON一致。原全分片tensor校验在905汇总中完成，本轮仅轻量metadata/SHA复核，没有重新训练、读取test评估或在登录节点加载tensor。

服务器原始报告：outputs/residual_scaling/cgcnn-seed123-r012-v1/reports；本地只读副本：outputs/residual_scaling/cgcnn-seed123-evidence/reports。另由同36点生成overview与later_rounds四面板PNG/SVG/PDF，已目视检查（放大图使用五位小数以避免重复刻度）。CSV/JSON/图表和审计快照均Git忽略，不作为源码提交。

这次是方案筛选，测试集继续封存；所有效果均非独立测试结果，也不宣称统计显著。当前不启动多seed、更深轮次或其他backbone，旧0–5轮实验继续暂停。

来源报告SHA256：00d48ddb411053940eed81100b767cfd6c80a4adfc2bcf779c19c4e3f7db789d。
