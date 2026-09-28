# Project I 执行计划：预训练原子模型中的递归计算段

## 1. 项目目标

本阶段研究冻结的原子基础模型中，是否存在可以在原生深度之外重复执行的计算子程序。

本阶段希望回答：

1. 哪些预训练计算段在重复执行时具有计算闭包性？
2. 连续多层循环是否比单层自循环更稳定、更有效？
3. 递归失效是否可以由循环接缝处的 latent distribution shift 解释？
4. normalization 或低容量 adapter 能否延长有效递归深度？
5. 较弱 backbone 增加推理计算后，能否接近较强 checkpoint 的表现？

---

## 2. 完整数学定义

### 2.1 输入、几何上下文与动态状态

一个原子结构写为

\[
x=(Z,R,L),
\]

其中 \(Z\) 是元素种类，\(R\in\mathbb R^{N\times 3}\) 是原子坐标，\(L\in\mathbb R^{3\times 3}\) 是周期晶胞。backbone 首先构造模型特定的静态几何上下文

\[
G=\Gamma_\theta(x),
\]

它可以包含邻接表、周期镜像、边向量、距离、径向基、球谐函数、截断权重及原子种类编码。在一次递归前向中，\(G\) 只由原结构计算一次，并在所有额外循环中保持不变；除非某项消融实验明确要求重新构图。

用 \(U_l\in\mathcal H_l\) 表示第 \(l\) 个计算边界上的**完整动态状态**。\(U_l\) 不一定是单个张量，例如：

\[
\begin{aligned}
U_l^{\mathrm{MatterSim}}&=(A_l,E_l),\\
U_l^{\mathrm{MACE}}&=H_l,\\
U_l^{\mathrm{CHGNet}}&=(A_l,B_l,\Theta_l),\\
U_l^{\mathrm{DPA2}}&=(g_{1,l},g_{2,l},h_{2,l}).
\end{aligned}
\]

静态的 \(G\) 不包含在 \(U_l\) 中，但每个 block 均可读取它。实现时必须回传该边界上的全部动态分量，不能只回传方便取得的 atom feature。

### 2.2 原生前向过程

设冻结 backbone 参数为 \(\theta\)，共有 \(L\) 个计算 block：

\[
B_l^{\theta_l}:\mathcal H_{l-1}\times\mathcal G
\rightarrow\mathcal H_l,
\qquad l=1,\ldots,L.
\]

输入编码器给出

\[
U_0=E_\theta(x;G),
\]

原生状态轨迹递推为

\[
U_l=B_l^{\theta_l}(U_{l-1};G),
\qquad l=1,\ldots,L.
\]

若使用模型原生预测头，则

\[
\hat y^{\mathrm{native}}
=D_\theta(U_L;x,G).
\]

若评估冻结表示，则先使用与目标物理量相容的 pooling \(P\)，再使用容量固定的下游 readout \(R_\phi\)：

\[
\hat y^{\mathrm{native}}
=R_\phi(P(U_L,x)).
\]

后续所有递归路径必须在 \(K=0\) 时严格还原这条原生路径。

### 2.3 计算段

选择连续边界 \(1\le a\le b\le L\)，定义计算段

\[
F_{a:b}^{\theta}
=B_b^{\theta_b}\circ B_{b-1}^{\theta_{b-1}}
\circ\cdots\circ B_a^{\theta_a},
\]

因此

\[
F_{a:b}^{\theta}:
\mathcal H_{a-1}\times\mathcal G
\rightarrow\mathcal H_b.
\]

其原生输入和输出分别是

\[
U_{a-1}^{(0)}=U_{a-1},
\qquad
V^{(0)}=F_{a:b}^{\theta}(U_{a-1}^{(0)};G)=U_b.
\]

这里上标 \((k)\) 表示第几次执行所选计算段，而下标 \(l\) 表示原生网络边界；二者不得混用。

### 2.4 循环接缝

为了再次执行同一计算段，需要接缝映射

\[
S_\psi^{b\rightarrow a-1}:
\mathcal H_b\rightarrow\mathcal H_{a-1}.
\]

第 \(k\) 次额外循环定义为

\[
U_{a-1}^{(k)}
=S_\psi^{b\rightarrow a-1}(V^{(k-1)}),
\qquad k=1,\ldots,K,
\]

\[
V^{(k)}
=F_{a:b}^{\theta}(U_{a-1}^{(k)};G),
\qquad k=1,\ldots,K.
\]

合并后得到递归动力系统

\[
V^{(k)}
=T_{a:b,\psi}(V^{(k-1)};G),
\]

其中

\[
T_{a:b,\psi}
=F_{a:b}^{\theta}\circ S_\psi^{b\rightarrow a-1}.
\]

本计划统一规定：

- \(K=0\)：计算段只执行一次，即原生模型；
- \(K=1\)：在原生执行之后额外执行一次；
- 总计算段执行次数为 \(K+1\)。

该约定避免把“循环次数”和“额外计算次数”混为一谈。

### 2.5 循环后的 suffix 与最终预测

若 \(b<L\)，完成 \(K\) 次额外循环后，从 \(V^{(K)}\in\mathcal H_b\) 继续执行原生 suffix：

\[
\bar U_b^{(K)}=V^{(K)},
\]

\[
\bar U_l^{(K)}
=B_l^{\theta_l}(\bar U_{l-1}^{(K)};G),
\qquad l=b+1,\ldots,L.
\]

最终表示为

\[
Z_{a:b}^{(K)}=\bar U_L^{(K)}.
\]

若 \(b=L\)，则直接令

\[
Z_{a:L}^{(K)}=V^{(K)}.
\]

预测统一写为

\[
\hat y_{a:b}^{(K)}
=R_\phi\!\left(P(Z_{a:b}^{(K)},x)\right),
\]

或在能量/力实验中使用模型原生能量头

\[
\hat E_{a:b}^{(K)}=D_\theta(Z_{a:b}^{(K)};x,G),
\qquad
\hat F_{a:b}^{(K)}=-\nabla_R\hat E_{a:b}^{(K)}.
\]

因此，只要整个递归路径对坐标可微，力仍由同一个标量能量导出；但保守性、有限差分一致性和数值连续性仍需实测。

### 2.6 递归方式是同一公式的特例

上述定义覆盖以下设置：

1. 单层重复：\(a=b\)；
2. 中间计算段循环：\(1<a\le b<L\)；
3. 后缀循环：\(b=L\)；
4. 全 backbone 循环：\(a=1,b=L\)。

本项目以连续多层计算段为主方法，单层重复作为严格基线。

### 2.7 Identity 接缝的成立条件

只有当

\[
\mathcal H_b\equiv\mathcal H_{a-1}
\]

时才能使用 \(S=I\)。这里的等价不只表示张量维度相同，还必须同时满足：

- 动态状态分量完全相同；
- 每个分量的通道数和语义一致；
- equivariant irreps、multiplicity 和 parity 一致；
- normalization convention 一致；
- atom、edge、bond、angle 或 pair 索引的定义一致。

若只有维度相同而 latent type 不同，仍应视为非兼容接缝。

### 2.8 冻结条件与可训练参数

整个项目固定

\[
\nabla_{\theta}\mathcal L=0.
\]

可训练参数仅包括接缝参数 \(\psi\) 和下游 readout 参数 \(\phi\)。不同实验必须明确属于以下哪一种：

\[
\begin{array}{ll}
\text{direct recursion}:& \psi=\varnothing,\ S=I,\\
\text{latent-only alignment}:& \psi\text{ 仅由无标签 latent 目标训练},\\
\text{task-supervised seam}:& \psi\text{ 由下游任务损失训练},\\
\text{probe-only}:& \psi\text{ 固定，仅训练 }\phi.
\end{array}
\]

这些结果必须分开报告。

---

## 3. 核心假设

### H1：计算段闭包

某些连续预训练计算段可以在冻结权重的条件下被额外执行，并改善下游表示或预测性能。

### H2：连续计算段优于单层重复

对于计算段

\[
B_a\rightarrow B_{a+1}\rightarrow\cdots\rightarrow B_b,
\]

段内转移仍保持训练时的原生顺序。与反复执行同一层相比，分布错位主要集中在

\[
B_b\rightarrow B_a
\]

这一循环接缝，因此预计更加稳定。

### H3：接缝漂移预测递归失效

递归深度增加后，接缝表示逐渐偏离 \(B_a\) 的原生输入分布：

\[
D_k^{\mathrm{in}}
=D\left(
\operatorname{Law}(U_{a-1}^{(k)}),
\operatorname{Law}(U_{a-1}^{(0)})
\right)\uparrow.
\]

该偏移预计与下游性能退化相关。

### H4：轻量接缝对齐能够恢复闭包

若递归失败主要来自坐标、尺度或表示分布错位，则 normalization 或低容量、对称性兼容的 adapter 应能降低漂移，并把最优递归深度推向更大的 \(K\)。

---

## 4. Backbone 顺序

### 4.1 第一优先级：MatterSim-1M

目的：以最低工程风险验证计算段递归是否存在有效信号。

MatterSim 的 M3GNet backbone 使用多个 `MainBlock`，每层共同更新：

\[
(A_l,E_l)\rightarrow(A_{l+1},E_{l+1}),
\]

其中 \(A_l\) 为 atom features，\(E_l\) 为 edge features。递归时必须传递完整状态，而不能只回灌 atom features。

计划比较 MatterSim-1M 的递归结果与原生 MatterSim-5M。该比较用于检验“弱模型 + 更多冻结计算”能否接近更强模型。

### 4.2 第二优先级：MACE-MP-0 small

目的：在具有明确物理对称性结构的 backbone 上验证结论。

MACE 的基本计算单元定义为：

\[
H_l
\xrightarrow{\mathrm{interaction}}
(M_l,SC_l)
\xrightarrow{\mathrm{product\ basis}}
H_{l+1}.
\]

因此不能只重复 interaction block；必须重复 `interaction + product` 复合单元。

MACE-MP-0 small 的 latent 主要为 scalar irreps，优先检查 identity recursion。随后再考虑包含高阶 irreps 的 medium/large checkpoint。

### 4.3 第三优先级：CHGNet

目的：检查现象能否跨 invariant atomistic architecture 复现。

完整递归状态为：

\[
(A_l,B_l,\Theta_l),
\]

分别对应 atom、bond 和 angle features。循环应覆盖完整的 atom-bond-angle 更新段，避免只重复最后的 atom-only 层。

### 4.4 后续扩展：DPA-2

DPA-2 的递归状态至少包括：

\[
(g_1,g_2,h_2),
\]

以及 neighbor list、mask 和 switching weights。优先循环连续的 repformer layers。由于实现和部署接口更复杂，DPA-2 不进入首轮最小验证。

---

## 5. 实验中的递归路径

对于具有 \(L\) 个 block 的模型，至少比较以下四种执行路径。

### 5.1 Native depth

\[
B_1B_2\cdots B_L.
\]

这是 \(K=0\) 的原生基线。

### 5.2 Single-block repeat

\[
B_1\cdots B_L(B_L)^K
\]

或选择一个中间 block 重复。它是最严格但分布错位最大的基线。

### 5.3 Suffix cycling

\[
B_1\cdots B_{a-1}(B_a\cdots B_L)^{K+1}.
\]

该设置无需在循环后重新接入剩余 backbone，优先实现。

### 5.4 Middle-segment cycling

\[
B_1\cdots B_{a-1}
(B_a\cdots B_b)^{K+1}
B_{b+1}\cdots B_L.
\]

该设置可以系统寻找模型内部最稳定、最有用的递归计算段。

首轮递归深度：

\[
K\in\{0,1,2,3,4\}.
\]

如果没有数值发散且仍有改善，再扩展到 \(K=8\)。

---

## 6. 接缝接口与对齐方法

接缝接口按复杂度逐步引入。

### 6.1 Identity

\[
S(H)=H.
\]

仅当形状、通道含义、irreps 和其他完整状态均兼容时使用。

### 6.2 Damped seam

令原生计算段输入为 \(U_{a-1}^{(0)}\)，则阻尼接缝定义为

\[
U_{a-1}^{(k)}
=(1-\alpha)U_{a-1}^{(0)}
+\alpha S_\psi(V^{(k-1)}),
\qquad 0<\alpha\le 1.
\]

随后仍按

\[
V^{(k)}=F_{a:b}^{\theta}(U_{a-1}^{(k)};G)
\]

执行计算段。该方法仅在两项状态可逐分量相加时使用。扫描 \(\alpha\in\{0.25,0.5,1.0\}\)，判断递归发散是否主要来自接缝更新幅度过大。

### 6.3 Normalization-only

Normalization-only 接缝不使用训练集整体均值、方差或 running statistics。对当前结构，缓存计算段首次执行时的输入

\[
U_a^{\rm in}:=U_{a-1}^{(0)}.
\]

对其中一个状态分量 \(c\)，定义当前结构的 RMS 范数

\[
\rho(X_c)=\sqrt{\frac{1}{d_c}\|X_c\|_F^2},
\]

并将循环输出 \(V_c\) 缩放为

\[
S_{{\rm norm},c}(V_c;U_{a,c}^{\rm in})
=\gamma_cV_c,
\qquad
\gamma_c
=\frac{\rho(U_{a,c}^{\rm in})}{\rho(V_c)+\epsilon}.
\]

必要时只对 \(\gamma_c\) 做固定范围 clip。对于多状态模型，atom、edge、bond、angle 或 pair states 分别匹配各自的输入范数。对于 equivariant features，按 \((\ell,p)\) irrep block 计算覆盖全部磁分量的旋转不变量范数，并在该 block 内使用同一个标量缩放系数。该 adapter 不中心化、不添加 bias、不跨样本聚合，也不保存训练集统计量。

### 6.4 Linear adapter

用普通线性层或残差线性层将循环输出映射回计算段输入空间。

### 6.5 Equivariant adapter

对 MACE、SevenNet 等等变模型，adapter 必须按 irreps 分块：

\[
S=\bigoplus_l S^{(l)},
\]

不得任意混合不同 \(l\) 和 parity 的通道。

### 6.6 Adapter 训练目标与固定点风险

从原生前向获得配对表示：

\[
(H_b(x),H_{a-1}(x)).
\]

最直接的无标签逐样本回归为

\[
\mathcal L_{\mathrm{align}}
=D\left(S(H_b(x)),H_{a-1}(x)\right).
\]

但该目标存在重要的固定点退化。如果

\[
S(F(U_{a-1}))\approx U_{a-1},
\]

则

\[
F(S(F(U_{a-1})))\approx F(U_{a-1}),
\]

额外循环只会重建第一次计算段的输出，而不会产生新的有效计算。因此，逐样本回归只作为“最大稳定化”对照，不作为唯一主目标。

主实验优先使用分布级对齐。令

\[
Q_{\psi}=\operatorname{Law}(S_\psi(H_b(x))),
\qquad
P_{a-1}=\operatorname{Law}(H_{a-1}(x)),
\]

则可使用

\[
\mathcal L_{\mathrm{dist}}
=\|\mu(Q_\psi)-\mu(P_{a-1})\|_2^2
+\lambda_{\rm cov}
\|\Sigma(Q_\psi)-\Sigma(P_{a-1})\|_F^2,
\]

或 MMD：

\[
\mathcal L_{\mathrm{MMD}}
=\operatorname{MMD}^2(Q_\psi,P_{a-1}).
\]

分布级目标约束循环状态回到 block 熟悉的统计区域，但不要求每个样本恢复成原来的 \(H_{a-1}(x)\)。

task-supervised seam 单独定义为

\[
\min_{\psi,\phi}
\frac{1}{|\mathcal D_{\rm tr}|}
\sum_{(x,y)\in\mathcal D_{\rm tr}}
\ell(\hat y_{a:b}^{(K)}(x),y)
+\lambda\mathcal L_{\mathrm{dist}}.
\]

第一阶段冻结 backbone，并将 identity、latent-only distribution alignment、paired regression 和 task-supervised seam 严格分开报告。

---

## 7. 下游评估设计

### 7.1 第一轮任务

第一轮只选择两个结构输入的回归任务：

1. 一个小数据任务，用于快速检查递归曲线和实现正确性；
2. 一个中等数据量任务，用于确认结果不是小样本偶然现象。

具体任务在完成数据可用性检查后确定。优先从 phonon、elastic modulus、dielectric、formation energy 或 band gap 中选择，并确保结构和标签许可、划分方式及评估指标明确。

### 7.2 Readout 控制

所有递归深度使用相同容量的 readout。backbone 全部冻结，只训练：

- 相同的下游 readout；
- 如实验需要，轻量接缝 adapter。

首轮采用固定 pooling；避免同时搜索大量 pooling 和递归配置，防止混淆 Project I 与 Project II。

### 7.3 随机性控制

开发阶段使用一个固定 split 和一个 seed。主 pilot 使用三个随机种子。只有出现稳定正信号后，才进行完整 benchmark folds。

---

## 8. Baselines

首轮必须包含：

1. 原生弱 backbone，\(K=0\)；
2. 原生强 backbone，例如 MatterSim-5M 或 MACE medium；
3. 单层重复；
4. 连续段循环；
5. identity 接缝；
6. normalization-only 接缝；
7. 随机初始化的同形状 block 或随机 adapter；
8. 参数量和推理成本接近的 prediction ensemble；
9. 相同 readout 在不同 native layers 上的结果。

第二阶段再增加：

- linear/equivariant adapter；
- nonlinear adapter；
- task-supervised adapter；
- full fine-tuning；
- independently deeper model 或现成的大 checkpoint。

不在第一阶段从头预训练更深的通用原子基础模型。

---

## 9. 评价量与表示漂移诊断

每个递归深度保存循环接缝前后及计算段输出的统计量。

对测试集 \(\mathcal D_{\rm te}\)，任务误差定义为

\[
\mathcal E_{a:b,S}(K)
=\frac{1}{|\mathcal D_{\rm te}|}
\sum_{(x,y)\in\mathcal D_{\rm te}}
\ell\left(\hat y_{a:b}^{(K)}(x),y\right).
\]

相对原生模型的收益为

\[
\Delta\mathcal E_{a:b,S}(K)
=\mathcal E_{a:b,S}(0)-\mathcal E_{a:b,S}(K).
\]

正值表示额外循环带来改善。计算代价记录为实测延迟、峰值显存及理论 block 调用次数：

\[
C_{a:b}(K)
=C_{\rm native}+K\,C(F_{a:b})+K\,C(S).
\]

对第 \(k\) 次接缝输入，定义分布漂移

\[
D_k^{\mathrm{in}}
=D\left(
\operatorname{Law}(U_{a-1}^{(k)}),
\operatorname{Law}(U_{a-1}^{(0)})
\right),
\]

以及计算段输出漂移

\[
D_k^{\mathrm{out}}
=D\left(
\operatorname{Law}(V^{(k)}),
\operatorname{Law}(V^{(0)})
\right).
\]

为识别“adapter 把循环压成无效固定点”，同时记录单样本状态运动量

\[
M_k
=\mathbb E_x
\left[
\frac{\|V^{(k)}(x)-V^{(k-1)}(x)\|_2}
{\|V^{(k-1)}(x)\|_2+\epsilon}
\right].
\]

若 \(M_k\approx0\) 且性能没有变化，则递归已退化为固定点重复；这不能被解释为有效的额外计算。

第一优先级：

- feature norm 和最大绝对值；
- per-channel mean/std；
- covariance spectrum；
- CKA；
- 数值发散、NaN/Inf 和异常梯度；
- 下游误差与漂移指标的相关性。

第二优先级：

- Procrustes alignment；
- MMD；
- nearest-neighbor preservation；
- effective rank；
- oversmoothing 指标；
- MACE 的 irrep-specific norm、mean 和 covariance。

需要检验 \(D_k^{\mathrm{in}}\)、\(D_k^{\mathrm{out}}\) 和 \(M_k\) 是否能预测性能开始下降、发散或进入固定点的递归深度。

---

## 10. 工程实现

建议建立统一接口：

```python
class RecursiveBackbone:
    def encode_geometry(self, batch): ...
    def initial_state(self, batch, geometry): ...
    def native_block(self, block_id, state, geometry): ...
    def readout(self, state, batch): ...
    def state_spec(self, boundary): ...
```

递归执行器只处理抽象状态：

```python
state = backbone.run_prefix(batch, stop=a - 1)
state = backbone.run_segment(state, geometry, start=a, stop=b)

for _ in range(K):  # K is the number of extra segment executions
    state = seam_adapter(state)
    state = backbone.run_segment(state, geometry, start=a, stop=b)

output = backbone.run_suffix(state, geometry, start=b + 1)
```

不同 backbone 的状态结构：

```text
MatterSim: atom_features, edge_features
MACE:      node_features，外加固定 geometry/edge bases/node attrs
CHGNet:    atom_features, bond_features, angle_features
DPA-2:     g1, g2, h2，外加 neighbor/mask/switch data
```

必须提供以下正确性测试：

1. `K=0` 与官方原生 forward 数值一致；
2. batch size 1 与多结构 batch 一致；
3. atom permutation 不改变 invariant 输出；
4. 对等变模型进行旋转/反射测试；
5. adapter 初始化为 identity 时不改变结果；
6. 冻结 backbone 后没有 backbone 参数梯度或优化器更新；
7. 保存和加载递归配置后结果可复现。

---

## 11. 关键图表

每个 backbone 至少产生：

1. 下游误差 vs. 递归深度 \(K\)；
2. 下游误差 vs. 实际推理成本；
3. seam drift vs. \(K\)；
4. 下游误差 vs. seam drift；
5. single-block 与 multi-block segment 对比；
6. identity、normalization、linear adapter 对比；
7. 弱 backbone recursion 与强 backbone native 对比；
8. 不同 \((a,b)\) 计算段的 recursability heatmap。

定义计算段递归得分，例如：

\[
R_{a,b}
=\max_{K>0}
\frac{\mathcal E(0)-\mathcal E_{a,b}(K)}{C_{a,b}(K)-C(0)},
\]

用于综合表示性能收益与额外计算成本。

---

## 12. 风险与应对

### 风险 1：额外递归立即发散

应对：检查完整状态是否传递；使用 suffix segment；加入 damping、normalization；缩短计算段；测试不同接缝。

### 风险 2：性能改善只是参数或 ensemble 效果

应对：加入随机 block、随机 adapter、相同成本 ensemble 和强 checkpoint 对照。

### 风险 3：adapter 实际重新学习了任务

应对：优先使用无标签 paired-latent training，并与 task-supervised adapter 分开报告。

### 风险 4：扩大感受野但产生 oversmoothing

应对：同时记录 node-feature variance、pairwise similarity、effective rank 和 nearest-neighbor preservation。

### 风险 5：力预测不再保守或不连续

只要递归路径最终仍输出标量总能量，并通过坐标自动微分计算力，理论上仍保持保守形式；但必须数值验证能量、力、有限差分和结构扰动连续性。第一轮优先做结构属性 readout，能量/力递归作为后续验证。

### 风险 6：没有性能提升

负结果仍应区分：

- 单层失败但连续段成功；
- identity 失败但 alignment 成功；
- 所有 segment 都随深度单调退化；
- 漂移与退化高度相关或完全不相关。

这些情况分别对应不同的计算闭包结论。

---

## 13. 首轮停止条件

满足下列任一条件后结束首轮 pilot 并总结：

### 正向停止

- 至少一个连续计算段在两个任务之一上稳定优于 native weak backbone；
- 三个 seeds 趋势一致；
- 收益不能被相同成本 ensemble 完全解释；
- 漂移诊断或 adapter 提供了机制性证据。

### 负向停止

- 多个合理 segment、damping 和 normalization 均无法避免退化；
- 退化在多个任务和 seeds 上稳定出现；
- 已排除 forward 拆分、状态遗漏和数值错误。

### 工程停止

- 目标 checkpoint 无法可靠访问完整中间状态；
- 自定义 forward 无法复现 native 输出；
- 递归路径破坏对称性或梯度正确性且短期无法修复。

---

## 14. 首轮最终交付物

1. MatterSim recursive wrapper；
2. native-equivalence 和状态完整性测试；
3. 两个任务、三个 seeds 的实验配置和结果；
4. 单层重复与连续段循环的直接比较；
5. identity、damping、normalization 和 linear adapter 对比；
6. 表示漂移诊断报告；
7. 弱模型递归与强模型 native 的成本-性能比较；
8. 是否进入 MACE 主实验的明确决策。

首轮预期总周期为 2--4 周。推荐执行顺序为：

\[
\boxed{
\text{MatterSim-1M segment cycling}
\rightarrow
\text{distribution diagnostics}
\rightarrow
\text{seam alignment}
\rightarrow
\text{MACE-MP-0 small}
}
\]
