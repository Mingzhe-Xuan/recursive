# Recursive embeddings for crystal representation models

## Introduction

1. Atomic Foundation Model like MACE, DPA, NequIP have shown that large scale pretraining on various structures and tasks can lead to better generalization and transferability of the learned representations.

2. Similarly, in the field of natural language processing, large language models like GPT-3 and BERT have demonstrated that pretraining on massive text corpora can lead to improved performance on downstream tasks. Simultaneously, researchers find test-time scaling (e.g. CoT, Multi-agent reasoning, latent reasoning) can further improve the performance of these models without additional training.

3. Inspired by these findings, we propose to explore the idea of recursive embeddings for crystal representation models. The goal is to leverage the power of large-scale pretraining and test-time scaling to enhance the performance of crystal representation models on various tasks.

## Related Work

1. **Atomic Foundation Models**: MACE, DPA, and NequIP are examples of atomic foundation models that have shown the benefits of large-scale pretraining on various structures and tasks. These models have demonstrated improved generalization and transferability of learned representations.

2. **Test-time Scaling in NLP**: In the field of natural language processing, large language models like GPT-3 and BERT have shown that pretraining on massive text corpora can lead to improved performance on downstream tasks. Additionally, test-time scaling techniques such as Chain-of-Thought (CoT) and multi-agent reasoning have been found to further enhance the performance of these models without additional training.

3. **Recursive Transformer**: Recursive transformers have been explored in various domains, including natural language processing and computer vision. These models leverage recursive structures to capture hierarchical relationships in data, leading to improved performance on tasks that require understanding of complex dependencies.

## Method

1. Choose a base crystal representation model (e.g., MACE, DPA, NequIP) that has been pretrained on a large dataset of crystal structures, which is hereafter referred to as the M. Input structures (A, L, P) are atomic numbers, lattice matrix, and positions within the cell respectively.

H = M(A, L, P)
Y = Readout(H)

where H is the atom-wise embedding of the input structure, and Y is the target property prediction. Note that M is frozen and Readout finetuned on the downstream task.

2. Let "recursive embedding" denotes that the atom-wise embedding H is fed back into M to generate a new embedding H_1, and the process is repeated for K iterations. The final embedding H_K is then used for property prediction. Here K is predicted by another estimator model E.

K = E(H)
H_k = M(H_{k-1}, L, P) for k = 1, 2, ..., K
Y = Readout'(H_K)

where E and Readout' are finetuned on the downstream task. M stays frozen.

3. We hypothesize that this recursive embedding process can capture higher-order interactions and dependencies among atoms in the crystal structure, leading to improved performance on property prediction tasks.

## Experiments

1. **Backbones**: MACE, DPA, NequIP

2. **Benchmarks and Metrics**: Follow the backbones respectively, e.g. Matbench, Open Catalyst, etc.

3. **Baselines**:
   - Non-recursive embedding (K=1)
   - Fixed K (e.g., K=2, 3, 4)

4. **Analysis**:
   - Case studies on specific crystal structures to visualize the effect of recursive embeddings on the learned representations.
   - Varying the number of recursive iterations K to study its effect on performance.
   - Analyzing the impact of freezing vs. fine-tuning the base model M during the recursive embedding process.
