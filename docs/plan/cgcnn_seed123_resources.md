# CGCNN seed 123：实测耗时与资源估算

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
