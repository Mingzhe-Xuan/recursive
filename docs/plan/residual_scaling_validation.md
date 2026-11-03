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

## 2026-11-03T09:41:08+08:00 后续只读诊断计划

使用已有成对预测缓存、checkpoint元数据和完整history，不重新训练。独立模块src/recursive_diagnostics/metrics提供signed correction评估；analysis验证来源与缓存链、区分train/val、汇总曲线并导出报告；scripts/recursive_diagnostics为CLI，scripts/slurm/recursive_diagnostics为CPU计算入口，每模块有README。与旧两个训练包完全分离，保留core/implementation hash。

定义父残差e=y-F_(r-1)、修正delta=F_r-F_(r-1)，只访问train和val标签。相关性同时报告Pearson/Spearman、无中心余弦；改善材料比例按绝对误差比较（tie_atol=1e-8原始单位），区分方向正确、过量修正；MSE收益=2*mean(e*delta)-mean(delta²)。全局最小二乘修正倍率仅作为幅度诊断，不应用或调参，不读取test。

各轮最佳checkpoint的eval缓存统一计算训练/验证MAE/RMSE和父残差尺度，避免训练BN/时刻差异。历史曲线保留online train normalized MSE与val MAE的实际口径，分图，不把它们当作同一指标；报告最佳val epoch、末期训练/验证变化。没有保存的中间checkpoint不能补成逐epoch eval训练MAE，不重训补全。

本地手算/退化情形/合成晶体三方案集成测试后，通过Slurm CPU加载全库archive、核对只读来源SHA、计算train/val指标与相关性/逐材料改善、生成学习曲线及图表。输出独立outputs/recursive_diagnostics；批量结果和图表全部忽略。

## 2026-11-03 纠错方向与训练/验证诊断结果

Slurm906 CPU作业COMPLETED/ExitCode0:0，54秒；先运行4项诊断测试8.65秒全部通过，再只读流式分析原有缓存。未重新训练/推理、未改变任何预测或权重、未访问test评估。结果72行train/val残差指标、48行相邻轮纠错指标、28条完整学习曲线及133380条验证材料记录；81个输入文件SHA在分析前后不变。26份产物11507178字节已拉回并逐文件校验SHA/大小，均Git忽略。

定义父残差e=y-F_previous、修正delta=F_current-F_previous。以下相关性为验证集Pearson，R1针对R0残差、R2针对本分支R1残差；改善人数按逐材料绝对误差下降统计，tie_atol=1e-8原始单位。训练与验证MAE降幅均来自同一最佳checkpoint的eval预测缓存，不使用online训练MSE作直接泛化差距。

| 性质 | 方案 | 验证相关性R1→R2 | R2验证改善人数/总数 | R1→R2训练MAE降幅 | R1→R2验证MAE降幅 |
| --- | --- | --- | --- | ---: | ---: |
| formation_energy_peratom | raw_residual | 0.3704 → 0.1217 | 2862/5569 (51.39%) | 2.933% | 0.327% |
| formation_energy_peratom | feature_residual | 0.2428 → 0.0308 | 2870/5569 (51.54%) | 1.541% | 0.488% |
| optb88vdw_bandgap | raw_residual | 0.1851 → 0.1198 | 2415/5565 (43.40%) | 8.338% | 0.055% |
| optb88vdw_bandgap | feature_residual | 0.2244 → 0.0282 | 2884/5565 (51.82%) | 3.762% | 0.275% |
| optb88vdw_total_energy | raw_residual | 0.2798 → 0.0990 | 2879/5565 (51.73%) | 12.037% | 1.142% |
| optb88vdw_total_energy | feature_residual | 0.2649 → 0.0221 | 2808/5565 (50.46%) | 0.751% | 0.092% |
| ehull | raw_residual | 0.1743 → 0.0981 | 2922/5531 (52.83%) | 0.982% | 0.462% |
| ehull | feature_residual | 0.1698 → 0.0134 | 2770/5531 (50.08%) | 4.114% | 0.209% |

两项检查的解释：

- 递归特征残差R2验证Pearson仅0.0134–0.0308，Spearman0.0202–0.0885；原始特征残差R2仍约0.0981–0.1217。二者都比R1弱，feature分支下降更明显；在当前模型与协议下，可泛化的纠错方向明显减弱，但这不能证明所有剩余误差本身不可学习。
- feature R2只有约50.08%–51.82%验证材料更准，raw R2范围43.40%–52.83%。raw带隙R2为2415/5565更准、3150更差，但改善贡献0.00725564与损害0.00716980相抵后净MAE仍下降0.00008584（0.0554%）：均值收益并不等于大多数材料获益。
- 训练端与验证端分化：raw带隙R2训练MAE下降8.338%，验证仅0.055%；raw总能12.037%对1.142%；feature带隙3.762%对0.275%、ehull4.114%对0.209%。这更支持训练误差的进一步拟合没有充分泛化，而不是统一地认为所有分支仅缺训练轮数。
- feature R2最佳val epoch分别形成能10/94、带隙55/137、总能30/99、ehull39/147，后面仍训练了大量epoch但没有刷新最优。R2后期带隙/ehull在线训练MSE继续下降而val近乎平台/波动。形成能feature和部分其他分支训练端也趋于平台/波动，不能把全部任务归为单一原因。
- raw R2最优epoch89/94、131/137、96/99、129/147接近预算末端，不能完全排除继续优化仍有小幅收益；当前诊断不足以断言优化已完全收敛。
- feature R2在形成能、总能、ehull上MAE微降而RMSE略升；MAE改善不代表所有误差尺度都改善。已额外报告方向正确率、过量修正、无中心余弦及MSE收益分解，最小二乘倍率只作诊断、未应用或调参。

已有学习曲线的train值是训练模式、跨batch参数变化的online normalized MSE；val是epoch结束的eval MAE，二者分图标记，不能拿其数值直接相减。完整曲线和90百分位放大图均保留。缺失中间checkpoint，不能重建逐epoch eval train MAE，本次没有为补曲线重训。

本地报告：outputs/recursive_diagnostics/cgcnn-seed123-evidence。summary.json完整嵌套指标，corrections.csv/residuals.csv/learning_curves.csv便于筛选，validation_materials.csv.gz提供逐材料原始纠错记录；train_validation_residuals.png对比统一eval口径0–2残差，learning_round_002_zoom.png显示第二轮学习走势，correction_round_002.png显示修正/父残差分布。9组PNG/PDF已目视检查。

结论限于当前单seed与验证集选择协议：后续轮次呈现泛化纠错信号弱、改善与损害相抵、部分训练端饱和/波动的组合，不能用“只要加训练轮数”概括，也不能由此证明其他模型、输入或训练方法无效。没有新增训练/系数搜索或解封测试集。
