# Goal 1：冻结原子基础模型中的递归计算与 irrep-level norm alignment

## 1. 目标与范围

本目标研究：在 MatterSim、MACE 和 DPA-2 三类预训练原子模型中，冻结并固定原生 backbone 后，重复执行已有计算 block 是否能够改善模型在原论文公开评测任务上的表现。

本版只实现一种接缝适配：**按状态类型和 irrep 类型分组的 norm alignment**。不实现可训练 linear/nonlinear adapter、LoRA、结构自适应深度控制器或其他可训练接缝。

本目标分为三个阶段：

1. 审计三类 backbone 的完整动态状态、block 边界和可闭合接缝，并验证 K=0 原生一致性；
2. 在论文对齐的公开任务上，从小到大扫描额外重复次数 \(K=1,2,3,\ldots\)，记录验证集表现并选择最佳深度；
3. 只有观察到可信的正向信号后，才扩大到更多随机种子、接缝位置和 backbone。

核心参数约束为

\[
\nabla_{\theta}\mathcal L=0,
\]

其中 \(\theta\) 表示预训练 backbone 的全部参数。norm alignment 不含可训练参数，也不读取标签。

---

## 2. Backbone 冻结与执行模式

所有实验必须满足：

- backbone 始终处于 eval 模式；
- backbone 参数全部设置为 requires_grad=False，且不进入 optimizer；
- dropout、BatchNorm 和其他带状态模块不更新；
- checkpoint buffer 在训练和推理过程中保持不变；
- 标量结构属性任务允许在 no_grad 环境中缓存表示；
- 后续若评估力，可以保留输出对坐标 \(R\) 的自动微分图，但仍不得计算或更新 backbone 参数梯度。

冻结检查同时验证：参数梯度为空、参数值未变化、buffer 未变化以及模型始终处于 eval 模式。

---

## 3. 统一模型与状态定义

给定原子结构

\[
x=(Z,R,C),
\]

其中 \(Z\) 为元素种类，\(R\) 为原子坐标，\(C\) 为周期晶胞。模型构造静态几何上下文

\[
G=\Gamma_\theta(x),
\]

并产生初始动态状态

\[
U_0=E_\theta(x;G).
\]

设 backbone 包含 \(N_B\) 个逻辑计算 block：

\[
B_l^{\theta_l}:
\mathcal H_{l-1}\times\mathcal G
\rightarrow\mathcal H_l,
\qquad l=1,\ldots,N_B.
\]

原生前向为

\[
U_l=B_l^{\theta_l}(U_{l-1};G).
\]

递归状态必须包含模型在层间传递的全部动态分量：

\[
\begin{aligned}
U_l^{\mathrm{MatterSim}}&=(A_l,E_l),\\
U_l^{\mathrm{MACE}}&=H_l,\\
U_l^{\mathrm{DPA2}}&=(g_{1,l},g_{2,l},h_{2,l}).
\end{aligned}
\]

其中：

- MatterSim 同时携带 atom 和 edge features；
- MACE 的一个逻辑 block 包含配对的 interaction + product；
- DPA-2 携带 repformer 所需的 atom/pair state、mask、neighbor list、switching weight 和其他固定上下文；
- 静态几何上下文 \(G\) 在同一次递归前向中只构造一次并重复使用。

每个边界必须提供显式 state_spec，记录 shape、dtype、state component、irrep、parity、multiplicity、mask 和是否为动态状态。不得只凭总维度相等判定接缝兼容。

---

## 4. 递归执行方式

### 4.1 连续计算段循环

选择连续计算段 \([a,b]\)：

\[
F_{a:b}^{\theta}
=B_b^{\theta_b}\circ\cdots\circ B_a^{\theta_a}.
\]

原生执行为

\[
V^{(0)}=F_{a:b}^{\theta}(U_{a-1}^{(0)};G).
\]

将第一次进入计算段的状态记为接缝参考状态：

\[
U_{a-1}^{\mathrm{ref}}=U_{a-1}^{(0)}.
\]

第 \(k\) 次额外循环为

\[
U_{a-1}^{(k)}
=S_{\mathrm{norm}}\left(V^{(k-1)};U_{a-1}^{\mathrm{ref}}\right),
\]

\[
V^{(k)}=F_{a:b}^{\theta}(U_{a-1}^{(k)};G),
\qquad k=1,\ldots,K.
\]

\(K\) 表示额外执行次数，总段执行次数为 \(K+1\)。K=0 不调用 norm alignment，必须还原原生路径。

优先审计完整 backbone 接缝 \((a=1,b=N_B)\)。只有当 \(\mathcal H_{N_B}\) 与 \(\mathcal H_0\) 的状态类型兼容时才执行完整循环；否则记为“不适用”，并按 state_spec 选择后缀段或中间段，不允许通过无依据的 reshape、截断或补零伪造兼容性。

### 4.2 逐层重复

进入第 \(l\) 层的状态记为 \(W_{l-1}\)，该层首次调用为

\[
V_l^{(0)}=B_l^{\theta_l}(W_{l-1};G).
\]

该层的参考状态固定为 \(W_{l-1}\)。第 \(r\) 次额外调用为

\[
U_{l-1}^{(r)}
=S_{\mathrm{norm},l}\left(V_l^{(r-1)};W_{l-1}\right),
\]

\[
V_l^{(r)}=B_l^{\theta_l}(U_{l-1}^{(r)};G),
\qquad r=1,\ldots,K_l,
\]

并令

\[
W_l=V_l^{(K_l)}.
\]

首轮比较统一逐层深度 \(K_l=K\) 和单层定位扫描。首轮不搜索任意非均匀 \(\mathbf K\)。

---

## 5. Irrep-level norm alignment

### 5.1 分组规则

norm alignment 按以下两级分别执行：

1. 状态类型 \(c\)，例如 atom、edge、pair、\(g_1\)、\(g_2\)、\(h_2\)；
2. irrep 类型 \(\tau=(\ell,p)\)，其中 \(\ell\) 为角动量阶数，\(p\) 为 parity。

对状态类型 \(c\) 中的 irrep \(\tau\)，将有效张量记为

\[
X_{c,\tau}\in
\mathbb R^{n_c\times q_{c,\tau}\times(2\ell+1)},
\]

其中 \(n_c\) 是当前结构中的有效 atom/edge/pair 数，\(q_{c,\tau}\) 是 multiplicity。padding 和被 mask 的元素不参与计算。

定义 per-structure RMS：

\[
\rho_{c,\tau}(X)
=\sqrt{
\frac{1}{d_{c,\tau}}
\sum_{i=1}^{n_c}
\sum_{q=1}^{q_{c,\tau}}
\sum_{m=-\ell}^{\ell}
X_{i,q,m}^{2}
},
\]

其中

\[
d_{c,\tau}=n_c q_{c,\tau}(2\ell+1).
\]

### 5.2 对齐变换

给定当前循环输出 \(V_{c,\tau}\) 和首次进入接缝时的参考输入 \(U_{c,\tau}^{\mathrm{ref}}\)，定义

\[
\gamma_{c,\tau}
=\operatorname{clip}\left(
\frac{\rho_{c,\tau}(U^{\mathrm{ref}})}
{\rho_{c,\tau}(V)+\epsilon},
\gamma_{\min},
\gamma_{\max}
\right),
\]

\[
S_{\mathrm{norm},c,\tau}
\left(V;U^{\mathrm{ref}}\right)
=\gamma_{c,\tau}V_{c,\tau}.
\]

同一状态类型、同一 \((\ell,p)\) 下的 multiplicity 和所有磁分量

\[
m=-\ell,\ldots,\ell
\]

共享同一个标量 \(\gamma_{c,\tau}\)。因此不同 \(m\) 不得独立缩放。不同状态类型或不同 \((\ell,p)\) 分别计算缩放系数。

没有显式高阶 irrep 的标量状态按 \((\ell=0,p=+1)\) 处理，但 atom、edge 和 pair 等状态类型仍不得合并计算范数。

### 5.3 约束

- 每个结构独立计算，不跨 batch 或数据集聚合；
- 不读取标签，不保存 running statistics；
- 不中心化、不添加 bias、不做逐通道 mean/std matching；
- 不改变 shape、irrep 内容、mask 或图连接关系；
- identity 作为无对齐基线保留，但不是另一种可训练 adapter；
- \(\epsilon\)、\(\gamma_{\min}\) 和 \(\gamma_{\max}\) 必须写入配置；
- 对齐前后必须执行旋转、反射和原子置换一致性测试。

---

## 6. 递归深度扫描与 early stopping

递归深度不是由控制器预测，也不是预先只枚举到 \(4\)。实验按

\[
K=0,1,2,3,4,\ldots
\]

从小到大顺序执行，其中 \(K=0\) 为原生基线，随后依次增加一次额外重复。

对每个已评估深度，使用相同 readout 架构、训练预算和 epoch-level early stopping 规则，得到验证指标 \(\mathcal E_{\mathrm{val}}(K)\)。当前扫描范围内的最佳深度为

\[
K^*
=\arg\min_{K\in\mathcal K_{\mathrm{observed}}}
\mathcal E_{\mathrm{val}}(K).
\]

“递归深度 early stopping”是指在递增扫描过程中观察最佳验证效果对应的重复次数，而不是训练深度控制器。首轮至少完整评估 \(K=0,1,2,3,4\)。之后满足任一条件时停止继续增加深度：

- 连续 depth_patience 个新深度没有产生新的验证集最佳值；
- 出现 NaN/Inf、不可恢复的数值发散或状态范数超过配置阈值；
- 达到预先配置的 K_hard_max、显存上限或计算预算。

默认 pilot 配置为 depth_patience=3、K_hard_max=16。若在运行前修改，必须在配置和实验记录中说明，不能查看测试集后修改。最终返回所有已观察深度中的 \(K^*\)，而不是最后执行的深度。

测试集只评估由验证集锁定的 \(K^*\) 和对应的 \(K=0\) 基线。

---

## 7. 论文对齐的任务清单

三类 backbone 的原论文面向不同任务，绝对误差不能跨任务直接排名。主要结论采用同一 backbone、同一数据、同一 split 和同一 readout 下 \(K>0\) 相对 \(K=0\) 的变化。

### 7.1 MatterSim

- checkpoint：MatterSim-v1.0.0-1M，M3GNet 架构；
- 主任务：Matbench matbench_phonons；
- 输入：周期晶体结构；
- 标签：最高光学声子 DOS 峰 last phdos peak；
- 数据量：1265；
- 单位：\(\mathrm{cm}^{-1}\)；
- 主指标：官方五折划分上的 MAE；
- 论文对齐依据：MatterSim 论文的 end-to-end property prediction 报告该任务，并给出 M3GNet fine-tuning 结果。

本实验冻结 backbone，因此不把论文中的 full fine-tuning 数值当作必须复现的 \(K=0\) 指标；论文数值只作为任务和量纲参考。正式基线是本项目统一 frozen-backbone readout 的 \(K=0\)。

### 7.2 MACE

- checkpoint：官方 MACE-MP-0 small；
- 主任务：MACE-MP 论文公开的 97-material PBE PhononDB/ffonons 集；
- 输入：论文使用的相同晶体及超胞约定；
- 回归标签：最高声子频率或 phonon band width，单位 THz；
- 分类标签：是否存在低于论文容差的 imaginary mode；
- 主指标：回归 MAE，辅报 \(R^2\)；分类辅报 accuracy、balanced accuracy 和混淆矩阵；
- 数据与代码：官方论文关联的 janosh/ffonons 公开资源。

该数据集原本用于 zero-shot 势能/力场的声子评测，没有官方监督式 readout split。为训练统一 frozen readout，本项目固定使用按材料分组的五折交叉验证，并保存生成的 fold 文件及 hash。原论文的 zero-shot native 结果单独报告，不与 frozen-readout 结果混为一项。

### 7.3 DPA-2

- checkpoint：官方 OpenLAM_2.1.0_27heads_2024Q1.pt；
- model branch：Domains_SSE-PBE；
- 主任务：DPA-2 论文的下游数据集 SSE-PBE-D；
- 体系：Li-P-S-Sn 固态电解质；
- 论文划分：2563 个训练构型、131 个测试构型，共 2694 个构型；
- 标签：结构能量和原子力；
- 首轮主指标：energy RMSE，统一换算为 eV/atom；
- 后续指标：在坐标梯度与原生复现检查通过后增加 force RMSE，单位 eV/Å。

论文没有为该数据集定义独立 validation split。本项目从论文训练部分按固定 seed、按轨迹或构型来源分组划出 validation；测试部分保持不变。split 文件和 hash 必须在第一次训练前锁定。

### 7.4 数据来源与下载

数据由本项目直接从官方来源下载，不由用户手工准备：

- Matbench：Materials Project 官方 Matbench 数据接口或直接下载；
- MACE phonon 数据：MACE-MP 论文关联的 janosh/ffonons 仓库及其引用的 PhononDB 数据；
- DPA-2：论文 Data Availability 指定的 AIS Square/Zenodo 数据归档，提取 SSE-PBE-D 及其 split 元数据。

数据集、checkpoint、论文 PDF、缓存和解压产物均不进入普通 Git。每个下载项必须记录来源 URL、版本、下载日期、文件大小和官方 checksum；官方未提供 checksum 时记录本地 SHA-256。DPA-2 完整归档约 17 GB，只在服务器任务数据目录下载和解压，仓库中只保存 manifest 与下载脚本。

---

## 8. Readout 与训练控制

最终表示经过与任务相容的 pooling 后输入 readout：

\[
\hat y^{(K)}
=R_\phi\left(P(Z^{(K)}(x),x)\right).
\]

所有深度必须使用相同的 pooling、readout 架构、参数量、optimizer、学习率搜索空间、epoch 上限、epoch-level early stopping、数据增强、batch size、标签标准化和 seed 集合。

只允许更新 readout 参数 \(\phi\)。norm alignment 没有可训练参数。每个 \(K\) 独立训练 readout，不继承上一个深度的最佳权重。

开发阶段使用一个 seed。确认实验使用三个预先固定的 seeds。测试集不得用于选择 \(K\)、接缝位置、norm 超参数、readout 超参数或训练 epoch。

---

## 9. 正确性测试与诊断

### 9.1 必须通过的测试

1. K=0 wrapper 与官方原生 latent/forward 在固定 dtype、设备和 batch 下数值一致；
2. batch size 1 与多结构 batch 对每个样本一致；
3. 原子置换不改变 invariant 输出；
4. 等变状态通过旋转和反射测试；
5. 同一 irrep 的所有 \(m\) 分量确认使用同一 \(\gamma_{c,\tau}\)；
6. mask 和 padding 不进入 norm；
7. backbone 参数、梯度和 buffer 均未变化；
8. 保存并重新加载递归配置后结果可复现。

K=0 一致性使用官方 forward 作为参考，并为每个 checkpoint、dtype 和硬件组合记录 atol 与 rtol，不使用没有容差定义的“严格相等”。

### 9.2 每个配置的诊断

每个 \((\text{model},a,b,K,\text{adapter})\) 记录：

- train/validation/test 主指标；
- 推理延迟、峰值显存和实际执行的 block 次数；
- 每个状态类型和 irrep 的 RMS、最大绝对值及 \(\gamma_{c,\tau}\)；
- NaN/Inf、readout 梯度异常和坐标梯度异常；
- 接缝前后的 invariant distribution drift；
- 连续两次循环的状态变化量；
- readout 的训练/验证差距；
- depth early-stopping 的完整轨迹和停止原因。

状态变化量定义为

\[
M_k
=\mathbb E_x\left[
\frac{\|V^{(k)}(x)-V^{(k-1)}(x)\|_2}
{\|V^{(k-1)}(x)\|_2+\epsilon}
\right].
\]

若 \(M_k\) 接近零且任务表现不变，则记为无效固定点，不视为有效的额外计算。

---

## 10. 正向信号、停止条件与实验升级

正向信号必须同时满足：

1. 至少一个 \(K>0\) 在验证集上优于同一 backbone 的 \(K=0\)；
2. 三个确认 seeds 的改善方向一致；
3. K=0 原生复现、冻结检查和对称性检查均通过；
4. 改善不能由更大的 readout、更多训练 epoch 或数据泄漏解释；
5. 状态没有进入无变化固定点，也没有依赖数值发散；
6. 测试集只用于验证已经锁定的 \(K^*\)。

以下情况停止扩大该 backbone 的实验并记录负结果：

- 多个类型兼容的接缝都无法在 \(K\ge1\) 保持数值稳定；
- norm alignment 和 identity 都不能避免稳定退化；
- 无法完整取得或回灌动态状态；
- wrapper 无法在既定容差内复现官方 K=0；
- 递归路径破坏等变性、置换不变性、周期边界或坐标梯度。

本 Goal 不因阳性结果而增加可训练 adapter 或结构自适应深度。阳性后的扩展仅包括更多接缝、更多 seeds、完整 depth curve，以及相同 backbone 的 weak/strong checkpoint 对照。

---

## 11. 交付物与完成标准

目标模块包括 recursive_backbones/common、recursive_backbones/mattersim、recursive_backbones/mace、recursive_backbones/dpa2、adapters、readouts、configs、tests、scripts 和 data/manifests；每个代码模块包含 README.md。

交付物包括：

- 三种 backbone 的状态与 block 边界审计；
- 通用连续段循环和逐层重复执行器；
- irrep-level norm alignment，确认不同 \(m\) 共享缩放；
- backbone eval 模式和冻结检查；
- 从小到大的 depth scan、depth early stopping 和 \(K^*\) 选择记录；
- 三项论文对齐任务的数据 manifest、固定 split 和 checksum；
- K=0 一致性、对称性、batch 一致性和状态完整性测试；
- 每个 backbone 的完整 validation depth curve、失败配置和停止原因；
- 是否观察到可重复正向信号的明确结论。

最低完成条件是：

1. 三种 backbone 均完成接口、状态和论文任务可用性审计；
2. MatterSim 完成 matbench_phonons 的完整 pilot；
3. MACE 和 DPA-2 至少分别完成 K=0 与第一个类型兼容的 K=1 配置；
4. 至少一个 backbone 完成到 depth early stopping 的完整递增扫描；
5. 所有结论均基于验证集选择，并形成继续或停止的证据链。

若某 backbone 因官方接口无法访问完整状态而无法执行递归，允许以“工程不可行”结束，但必须提交复现步骤、错误证据和已排除的替代边界，不能只标记为未完成。

---

## 12. 一手来源

- MatterSim 论文：[MatterSim: A Deep Learning Atomistic Model Across Elements, Temperatures and Pressures](https://arxiv.org/abs/2405.04967)
- MatterSim 官方仓库与模型卡：[microsoft/mattersim](https://github.com/microsoft/mattersim)
- Matbench 官方仓库：[materialsproject/matbench](https://github.com/materialsproject/matbench)
- MACE-MP 论文：[A foundation model for atomistic materials chemistry](https://arxiv.org/abs/2401.00096)
- MACE foundation models 官方仓库：[ACEsuit/mace-foundations](https://github.com/ACEsuit/mace-foundations)
- MACE phonon 评测资源：[janosh/ffonons](https://github.com/janosh/ffonons)
- DPA-2 论文：[DPA-2: a large atomic model as a multi-task learner](https://www.nature.com/articles/s41524-024-01493-2)
- DPA-2 官方数据归档：[Zenodo 10.5281/zenodo.10461723](https://zenodo.org/records/10461723)
- DPA-2/OpenLAM 官方 checkpoint 与 branch 说明：[DeepModeling discussion #3772](https://github.com/deepmodeling/deepmd-kit/discussions/3772)
