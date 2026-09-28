# Adaptive Test-Time Depth Scaling for Pretrained Atomistic Models

## 1. Motivation and Overview

Large pretrained atomistic models are increasingly becoming general-purpose representations for molecules and crystalline materials. Models such as MACE-MP and DPA-2 are pretrained on diverse atomic environments and can transfer to downstream systems with substantially less task-specific training. MACE-MP, for example, builds on the MACE architecture and was trained on roughly 150,000 inorganic crystal structures as a general-purpose atomistic model, while DPA-2 explicitly formulates large atomic modeling as multi-task pretraining followed by downstream adaptation.

Most existing work focuses on scaling the amount of training data, model size, architectural expressivity, or fine-tuning. In contrast, much less is known about whether a pretrained atomistic model can systematically benefit from **additional computation at inference time while keeping its pretrained backbone fixed**.

This question is motivated by recent developments in language models, where test-time computation can improve performance without modifying the underlying pretrained model. Importantly, recent studies show that the usefulness of additional inference computation depends strongly on the difficulty of individual inputs, motivating adaptive rather than uniform compute allocation.

We propose to investigate an analogous phenomenon in atomistic representation learning:

\[
\boxed{
\text{Can a pretrained atomistic model improve its predictions by “thinking deeper” at test time?}
}
\]

Specifically, we introduce additional recurrent equivariant computation on top of a frozen pretrained representation and study how prediction quality changes as a function of inference depth.

Our central hypothesis is not that more computation must monotonically improve performance. Instead, we hypothesize that pretrained atomistic representations possess a **structure-dependent useful computational depth**:

\[
\boxed{
K^*= K^*(x,y,\text{task}),
}
\]

where different crystal structures may benefit from different numbers of additional refinement steps.

Under this hypothesis, excessive recursion may degrade some representations, while difficult or structurally complex examples may benefit from substantially more computation. This naturally motivates **adaptive test-time compute allocation**.

A further objective is to determine whether the optimal computational depth is predictable from interpretable structural characteristics. Ultimately, we aim to identify empirical relationships of the form

\[
K^*
\approx
f(
\text{structural complexity},
\text{chemical complexity},
\text{graph topology},
\text{model uncertainty}
),
\]

potentially yielding an empirical scaling law relating crystal complexity to required inference computation.

---

# 2. Research Questions

The project is organized around four research questions.

### RQ1: Does test-time depth scaling exist in pretrained atomistic models?

Given a frozen pretrained atomistic backbone, does additional recurrent latent computation improve downstream prediction?

Formally, if \(C(K)\) denotes inference compute with \(K\) additional refinement steps, we ask whether there exist regimes in which

\[
C(K_2)>C(K_1)
\]

and

\[
\mathcal{E}(K_2)<\mathcal{E}(K_1).
\]

We do **not** initially require

\[
\frac{\partial \mathcal{E}}{\partial K}<0
\]

for every \(K\). Establishing the existence and shape of the scaling curve

\[
\mathcal{E}(K)
\]

is itself the first scientific question.

### RQ2: Is the useful amount of test-time computation structure-dependent?

For each structure \(x_i\), we study the sample-level loss

\[
\ell_i(K).
\]

We hypothesize that different structures have different optimal depths:

\[
K_i^*
=

\arg\min_K \ell_i(K).
\]

Consequently, a single globally fixed \(K\) may be intrinsically suboptimal.

A non-monotonic global scaling curve would therefore not necessarily constitute failure. Instead, it may result from averaging heterogeneous sample-level scaling curves.

### RQ3: Can additional computation be allocated adaptively?

Rather than assigning every structure the same inference depth, we aim to learn an estimator that predicts whether another refinement step is worth its computational cost.

The resulting model should preferentially allocate additional inference compute to structures that benefit from it and terminate early for structures whose representations have already converged or begin to degrade.

### RQ4: What determines the optimal computational depth?

We investigate whether \(K^*\) can be explained using interpretable properties of the input structure or intermediate model states.

The longer-term goal is to derive an empirical relation such as

\[
K^*
\simeq
f(D_{\mathrm{graph}},
S_{\mathrm{chem}},
C_{\mathrm{local}},
U,
\ldots),
\]

where \(D_{\mathrm{graph}}\) characterizes structural propagation distance, \(S_{\mathrm{chem}}\) chemical complexity, \(C_{\mathrm{local}}\) local-environment heterogeneity, and \(U\) model uncertainty or representation instability.

---

# 3. Relation to Existing Work

The proposed work sits at the intersection of pretrained atomistic models, recurrent/message-passing architectures, adaptive-depth graph neural networks, and test-time scaling.

MACE introduced higher-body-order equivariant messages and showed that increased local body order can reduce the number of message-passing iterations needed to achieve expressive atomistic representations. This distinction is important: the proposed recursion primarily changes **message-passing depth and effective receptive field**, rather than simply introducing higher explicit local body order.

NequIP similarly constructs E(3)-equivariant atomic representations through successive interaction blocks. These models establish that repeated equivariant interaction is a natural mechanism for propagating atomic information.

Recursive atomistic representations themselves are not new. REANN introduced recursively embedded atom representations to improve local completeness and nonlocal information propagation. However, recursion in REANN is part of the model architecture and its training procedure.

Adaptive graph depth has also been studied outside pretrained atomistic foundation models. Adaptive Message Passing, for example, explicitly learns graph-dependent message-passing depth to address underreaching, oversmoothing, and oversquashing.

The distinction we seek to study is therefore not simply “recursive atom embeddings” or “adaptive message passing.” The central setting is

\[
\boxed{
\text{pretrained atomistic representation}
+
\text{frozen backbone}
+
\text{additional inference-time computation}
}
\]

with explicit characterization of accuracy–compute scaling and structure-dependent compute allocation.

In the literature examined for this proposal, we have not identified work whose primary question is whether **a frozen pretrained atomistic foundation model can exploit computation beyond its standard inference depth as a test-time scaling mechanism**, followed by adaptive allocation of this compute and characterization of its relationship with crystal structure. A broader systematic novelty search should nevertheless be performed before publication.

---

# 4. Method

## 4.1 Base Representation

Let a crystal structure be

\[
x=(A,L,P),
\]

where \(A\) denotes atomic species, \(L\) the periodic lattice matrix, and \(P\) atomic positions.

A pretrained atomistic model \(M_{\theta^*}\) produces atom-wise representations

\[
H^{(0)}
=

M_{\theta^*}(A,L,P),
\]

where

\[
H^{(0)}
=

\{h_i^{(0)}\}_{i=1}^{N}.
\]

The pretrained parameters \(\theta^*\) remain frozen.

A downstream readout \(R_\phi\) produces

\[
\hat y^{(0)}
=

R_\phi(H^{(0)}).
\]

In this proposal, \(K=0\) therefore denotes the normal pretrained model with no additional test-time refinement.

---

## 4.2 Recurrent Equivariant Refinement

Directly applying the entire original model as

\[
M(H,L,P)
\]

is generally not mathematically well-defined because pretrained atomistic models map atomic identities and geometry into latent representations, whereas \(H\) already lives in a latent equivariant feature space.

Instead, we define a type-compatible equivariant transition operator

\[
\Phi_{\theta^*}(H,G),
\]

where \(G=G(L,P)\) contains the periodic neighbor graph and geometric edge information.

The recurrent representation becomes

\[
H^{(k+1)}
=

H^{(k)}
+
\alpha_k
\Phi_{\theta^*}(H^{(k)},G).
\]

The residual connection is included to reduce representation drift and improve stability at large \(K\).

The simplest implementation reuses an interaction block or compatible collection of blocks from the pretrained model while keeping their parameters frozen.

If dimensional or representation incompatibilities prevent direct recurrence, small equivariant input/output adapters may be introduced:

\[
H^{(k+1)}
=

H^{(k)}
+
A_{\mathrm{out}}
\left[
\Phi_{\theta^*}
\left(
A_{\mathrm{in}}(H^{(k)}),
G
\right)
\right].
\]

The main backbone remains frozen; only the adapters, downstream readout, and optional compute router are trained.

This distinction will be reported explicitly as two regimes:

\[
\text{Strict frozen recursion}
\]

and

\[
\text{Frozen backbone + lightweight recurrent adaptation}.
\]

---

## 4.3 Fixed-Depth Test-Time Scaling

We first study fixed additional inference depths

\[
K\in\{0,1,2,3,4,6,8,\ldots\}.
\]

Predictions are

\[
\hat y^{(K)}
=

R_\phi(H^{(K)}).
\]

For each \(K\), we measure both predictive performance and inference cost:

\[
\mathcal{E}(K),
\qquad
C(K).
\]

The primary scaling plot will therefore be

\[
C(K)
\quad\text{vs.}\quad
\mathcal{E}(K),
\]

rather than accuracy alone.

Possible outcomes include monotonic improvement, saturation, U-shaped behavior, and immediate degradation. Each outcome provides information about whether pretrained representations possess useful additional computational depth.

---

# 5. Sample-Dependent Optimal Depth

For sample \(i\), define

\[
\ell_i(k)
=

\ell(y_i,\hat y_i^{(k)}).
\]

A naïve oracle depth is

\[
K_i^{\mathrm{oracle}}
=

\arg\min_k \ell_i(k).
\]

However, small fluctuations in prediction error could make this quantity unstable and could favor unnecessarily expensive computation.

We therefore define a more meaningful **compute-aware optimal depth**:

\[
K_i^*(\lambda)
=

\arg\min_k
\left[
\ell_i(k)
+
\lambda C(k)
\right],
\]

where \(\lambda\) represents the cost assigned to additional inference computation.

This definition directly connects adaptive depth to a deployment budget.

Equivalently, the marginal utility of another computation step can be defined as

\[
\Delta_i(k)
=

\ell_i(k)-\ell_i(k+1).
\]

Additional computation is worthwhile whenever

\[
\Delta_i(k)
>
\lambda
\left[
C(k+1)-C(k)
\right].
\]

This leads to a natural interpretation:

\[
\boxed{
\text{continue computation while its expected marginal benefit exceeds its marginal cost}.
}
\]

---

# 6. Adaptive Test-Time Compute Allocation

Instead of directly predicting an integer \(K\), the main adaptive method will use sequential halting.

At refinement step \(k\), a lightweight estimator receives pooled information from the current representation:

\[
z_k
=

\mathrm{Pool}(H^{(k)}),
\]

possibly together with structural descriptors \(s(x)\), and predicts

\[
q_k
=

E_\psi(z_k,s(x),k),
\]

where \(q_k\) estimates the utility or probability of continuing computation.

Inference terminates when

\[
q_k < \tau
\]

or when \(K_{\max}\) is reached.

A differentiable alternative is to predict halting probabilities

\[
p_0,p_1,\ldots,p_{K_{\max}},
\]

and optimize

\[
\mathcal{L}
=

\mathcal{L}_{\mathrm{task}}
+
\lambda
\mathbb E[K].
\]

This explicitly learns an accuracy–compute tradeoff.

The principal comparison will be

\[
\text{Best fixed }K
\quad\text{vs.}\quad
\text{Learned adaptive }K
\quad\text{vs.}\quad
\text{Oracle adaptive }K.
\]

The gap between fixed and oracle depth measures the total available benefit from adaptive compute allocation, while the gap between learned and oracle depth measures how much of this potential the routing model captures.

---

# 7. Structural Determinants of Computational Depth

A central scientific component of the project is to explain why different structures require different amounts of computation.

We will correlate \(K_i^*\), marginal gains \(\Delta_i(k)\), and learned halting behavior with several families of descriptors.

| Category | Candidate descriptors | Hypothesis |
| --- | --- | --- |
| System size | number of atoms, cell volume, volume/atom | larger systems may require more propagation |
| Graph range | graph diameter, mean shortest-path distance, eccentricity | larger propagation distance may increase useful depth |
| Local topology | coordination mean/variance, neighbor-count heterogeneity | heterogeneous environments may require additional refinement |
| Chemical complexity | number of species, composition entropy | chemically diverse systems may require more computation |
| Symmetry | space group, number of inequivalent/Wyckoff environments | high symmetry may reduce effective complexity |
| Geometric anisotropy | lattice aspect ratios, directional neighbor statistics | anisotropic systems may have longer effective communication paths |
| Latent complexity | atom-wise embedding variance, representation entropy | heterogeneous latent states may require further refinement |
| Convergence state | \(\|H^{(k)}-H^{(k-1)}\|\), cosine similarity | representation stability may predict when computation should stop |
| Uncertainty | ensemble/readout uncertainty or calibration proxy | difficult/OOD samples may benefit from more computation |

A particularly attractive physical hypothesis is that optimal depth reflects an effective structural dependency length:

\[
K^*
\sim
\frac{\ell_{\mathrm{dep}}}{r_c},
\]

where \(r_c\) is the local interaction cutoff and \(\ell_{\mathrm{dep}}\) is an effective length scale over which information must propagate for the target property.

This relation should be treated as a hypothesis to test rather than an assumed law.

---

# 8. Empirical Depth Law

After collecting oracle or compute-optimal depths, we will first test whether \(K^*\) is statistically predictable at all.

Simple models should be preferred before complex neural estimators.

For example,

\[
K^*
\approx
\operatorname{clip}
\left[
a
+
b\log N
+
cD_G
+
dS_{\mathrm{chem}}
+
eU
\right].
\]

Here \(D_G\) denotes graph diameter and \(U\) a model-state difficulty indicator.

If significant predictable structure exists, symbolic regression can be used to search for a more compact relation such as

\[
K^*
\simeq
1+
\left\lceil
\alpha
\frac{D_G}{r_c}
+
\beta S_{\mathrm{chem}}
+
\gamma U
\right\rceil.
\]

The objective is not merely to maximize \(R^2\), but to identify a relation that generalizes across datasets, target properties, and ideally model backbones.

Three levels of predictability will therefore be compared:

\[
\text{structure-only}
\rightarrow
\text{model-state-only}
\rightarrow
\text{structure + model state}.
\]

If a simple structural equation approaches the performance of a neural router, this would provide evidence that optimal inference depth corresponds to an interpretable property of the atomic structure rather than an arbitrary learned routing behavior.

---

# 9. Experimental Design

## Phase I: Establish the Test-Time Scaling Phenomenon

The first experiments should use a single pretrained backbone, preferably MACE-MP, to minimize implementation complexity.

For each downstream property:

\[
H^{(0)},H^{(1)},\ldots,H^{(K_{\max})}
\]

will be generated with the same frozen backbone and evaluated using controlled downstream readouts.

The primary result is

\[
\mathrm{MAE/RMSE}
\quad\text{vs.}\quad
K
\]

together with

\[
\mathrm{MAE/RMSE}
\quad\text{vs.}\quad
\mathrm{FLOPs/latency}.
\]

MACE is particularly informative because its higher-body-order messages were explicitly designed to achieve high expressivity with relatively few message-passing iterations. Additional recurrent depth therefore tests whether useful semi-local computation remains beyond the architecture's standard depth.

---

## Phase II: Establish Heterogeneous Optimal Depth

For every validation/test structure, compute the complete loss trajectory

\[
\ell_i(0),\ell_i(1),\ldots,\ell_i(K_{\max}).
\]

We will measure the distribution of

\[
K_i^*(\lambda),
\]

the fraction of structures that benefit from additional computation, the magnitude of achievable oracle improvement, and the stability of optimal depths across random seeds.

A central diagnostic is whether different structures genuinely exhibit different loss minima.

If essentially all samples prefer the same \(K\), adaptive depth is unnecessary.

---

## Phase III: Learn Adaptive Compute Allocation

Train lightweight routers using only information available at inference time.

Performance will be evaluated at matched **average inference budgets**:

\[
\mathbb E[K]\le B.
\]

For every budget \(B\), compare adaptive allocation against a globally fixed-depth model with comparable mean computation.

The important object is therefore an accuracy–compute Pareto frontier rather than a single accuracy number.

---

## Phase IV: Explain Optimal Depth

Compute structural and latent descriptors and evaluate their association with

\[
K_i^*
\]

and

\[
\Delta_i(k).
\]

Analysis will include correlations, conditional distributions, simple regression/ordinal models, feature importance, partial dependence, and symbolic regression.

The key question is whether a stable relation survives across data splits and tasks.

---

## Phase V: Cross-Backbone and OOD Validation

After establishing the phenomenon on one model, test whether the findings transfer to another pretrained atomistic model such as DPA-2.

DPA-2 is particularly relevant because it is explicitly pretrained as a multi-task large atomic model over diverse chemical and materials systems.

A NequIP-family model can additionally serve as an architectural comparison, although NequIP itself should be described as an equivariant atomistic architecture rather than automatically as a pretrained foundation model.

OOD tests should investigate whether difficult structures consume systematically greater compute than familiar in-distribution structures.

---

# 10. Benchmarks

For the first stage, crystal-property prediction is preferable to force-field training because it provides a cleaner test of representation quality.

Matbench offers 13 standardized materials prediction tasks spanning electronic, thermodynamic, elastic, optical, and other materials properties, with dataset sizes ranging from hundreds to more than \(10^5\) examples.

We should select structure-based tasks covering properties with plausibly different degrees of locality.

This allows an additional task-level hypothesis:

\[
K^*_{\mathrm{task}}
\]

may systematically depend on the physical locality of the target property.

After establishing the method, energy/force prediction or catalyst benchmarks such as OC20 can be considered as a second-stage validation. OC20 provides large-scale catalyst energy/force and relaxation data and predefined distribution-shift evaluations.

---

# 11. Baselines and Ablations

The principal experimental controls should separate the value of **additional compute**, **recurrence**, and **adaptive allocation**.

The study should include the original frozen backbone at \(K=0\), multiple fixed values of \(K\), best fixed \(K\), learned adaptive depth, oracle adaptive depth, and random compute allocation at the same average \(K\).

Additional controls should include a larger downstream readout, parameter-matched lightweight refinement, an ensemble of predictions from different depths, and where feasible a non-recurrent deeper model or larger pretrained checkpoint with comparable compute.

A critical comparison is

\[
\text{adaptive }K
\quad\text{vs.}\quad
\text{fixed }K
\]

under equal average inference cost.

This is not intended to require that test-time scaling use no additional compute; additional compute is the mechanism being studied. Instead, the comparison determines whether that compute is allocated efficiently.

---

# 12. Representation-Dynamics Analysis

Prediction accuracy alone does not explain why recursion helps or fails.

We therefore analyze the latent trajectory

\[
H^{(0)}
\rightarrow
H^{(1)}
\rightarrow
\cdots
\rightarrow
H^{(K)}.
\]

Useful diagnostics include

\[
d_k
=

\frac{\|H^{(k)}-H^{(k-1)}\|}
{\|H^{(k-1)}\|},
\]

representation cosine similarity across depth, atom-wise feature variance, readout sensitivity, pairwise feature similarity, and prediction change

\[
|\hat y^{(k)}-\hat y^{(k-1)}|.
\]

These quantities can distinguish several possible mechanisms.

If

\[
d_k\rightarrow0,
\]

the recursion may be converging toward a fixed point.

If atom-wise representations become increasingly similar, degradation may be associated with oversmoothing.

If feature norms or representation distances grow rapidly, degradation may instead reflect latent distribution shift or instability.

These analyses are essential for interpreting non-monotonic scaling.

---

# 13. Main Hypotheses

**H1 — Existence of useful test-time depth.**

For at least a non-trivial subset of tasks and structures,

\[
\exists K>0:
\quad
\ell_i(K)<\ell_i(0).
\]

**H2 — Non-uniformity.**

Optimal depth varies substantially across samples:

\[
\mathrm{Var}(K_i^*)>0.
\]

**H3 — Adaptive allocation.**

At matched average inference compute,

\[
\mathcal E_{\mathrm{adaptive}}
<
\mathcal E_{\mathrm{best\ fixed}}.
\]

**H4 — Structural predictability.**

A non-trivial fraction of the variation in \(K_i^*\) or marginal computational utility can be predicted from structural or latent-state descriptors.

**H5 — Transferability of computational depth.**

Relationships between difficulty and optimal compute partially transfer across tasks, datasets, or pretrained backbones.

---

# 14. Possible Results and Their Interpretation

The most favorable outcome is not necessarily monotonic scaling.

A particularly interesting result would be

\[
\mathcal E(0)
>
\mathcal E(1)
>
\mathcal E(2)
<
\mathcal E(3)
<
\mathcal E(4),
\]

while adaptive depth outperforms every fixed value.

This would support the interpretation that

\[
\boxed{
\text{additional computation is useful, but its marginal value is sample-dependent}.
}
\]

The story would then become:

**More compute is not universally better; allocating the right amount of compute to the right structure is better.**

A monotonic curve would instead establish a direct atomistic test-time scaling phenomenon, with adaptive computation primarily improving efficiency.

If no \(K>0\) improves on \(K=0\), the central hypothesis would be falsified for that recurrent operator. Possible explanations would include depth distribution shift, oversmoothing, mismatch between pretrained layers and recurrent reuse, or the fact that the original backbone already extracts essentially all useful information for the chosen target.

Such a negative result should motivate changes to the recurrent operator rather than automatically being interpreted as evidence against all forms of atomistic test-time scaling.

---

# 15. Key Risks

The largest technical risk is that pretrained interaction blocks were not trained to operate recursively beyond their original architectural position. Repeated application may move representations outside their training distribution.

This motivates residual recurrence, normalization, lightweight adapters, and careful monitoring of feature statistics.

A second risk is that improvements could result merely from additional trainable parameters. This must be controlled by parameter-matched baselines and by a strict frozen-recursion experiment.

A third risk is that per-sample \(K^*\) may be noisy because the loss difference between adjacent depths is small. The compute-aware definition

\[
K_i^*(\lambda)
\]

and repeated-seed analysis should reduce this instability.

A fourth risk is that structural descriptors correlate with \(K^*\) in one dataset but fail to generalize. For this reason, any empirical depth law must be validated on held-out chemistry, structural families, and ideally different downstream properties.

---

# 16. Expected Contributions

If successful, the project would make three main contributions.

First, it would establish and characterize **test-time depth scaling in pretrained atomistic models**, measuring how frozen atomistic representations respond to additional inference computation.

Second, it would introduce **adaptive test-time compute allocation for crystal representations**, showing that sample-dependent halting can outperform globally fixed computation budgets when useful depth is heterogeneous.

Third, it would investigate the scientific relationship between **structural complexity and computational depth**, potentially deriving an interpretable empirical law predicting how much inference computation a structure requires.

The strongest version of the final result would therefore move beyond a new architecture and toward a broader observation:

\[
\boxed{
\text{the computational depth required by an atomistic model is itself a learnable and physically interpretable property of the input structure}.
}
\]

---

# 17. Minimal Viable Project

Before attempting multiple backbones or sophisticated adaptive routing, the project should first answer three simple questions on one pretrained model and a small number of crystal-property tasks:

\[
\text{(1) Does any }K>0\text{ improve over }K=0?
\]

\[
\text{(2) Do different samples prefer different }K?
\]

\[
\text{(3) Is the oracle adaptive gain substantially larger than the best fixed-}K\text{ gain?}
\]

If the answer to all three is yes, the adaptive-router and structural-depth components are strongly justified.

The four most informative initial figures would be:

\[
\mathrm{Error}\ \text{vs.}\ K,
\]

\[
\mathrm{Error}\ \text{vs. inference FLOPs},
\]

\[
P(K_i^*),
\]

and

\[
K_i^*
\ \text{vs. structural/model complexity}.
\]

These experiments can determine very early whether the project contains a genuine test-time scaling phenomenon or only an architectural refinement effect.

---

# 18. Working Title

A conservative title is:

**Adaptive Test-Time Depth Scaling for Pretrained Atomistic Models**

A more conceptual title is:

**How Deep Should an Atomistic Model Think? Adaptive Test-Time Computation for Crystal Representations**

If the structural relationship becomes a central result, a stronger final framing could be:

**Structure-Dependent Test-Time Scaling in Atomistic Foundation Models**

The latter emphasizes what is likely to be the most distinctive scientific claim: not merely that additional computation helps, but that the amount of useful computation systematically depends on the structure being modeled.
