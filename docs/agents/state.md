# 当前状态

用户最新范围：本阶段仅CGCNN seed123的形成能、带隙、总能、ehull四性质，各做0–5轮及既定必要对照；其余25性质明确延后，不能计为当前阶段失败或继续排队执行。科学配置/全库缓存仍保持原协议。

CGCNN seed123的真实两轮pilot已完成，890/891均经scontrol确认COMPLETED/ExitCode0:0。r0为222epoch、best验证MAE0.04822800 eV/atom；r1为164epoch/114308步、best验证MAE0.04402161、训练/验证5231.45秒、86813参数（含投影5980）。两轮均缓存完整55712结构/562055原子/64维float32；r1缓存8.13秒、147595808字节。第0轮权重/缓存未改变。

891真实CUDA验收passed：32结构native/wrapper最大差0、batch/single差4.172325e-7；0→1直接链/缓存在既定atol2e-5+rtol1e-4组合容差内通过（逐阶段最大绝对差1.7166e-5/4.5776e-5，不能只用绝对容差解读）。两份完整配置/分片字节/来源补充manifest SHA与验收引用一致，真实全分片审计通过。代码核心仍4379c88、入口896a171，核心验收时本地46项和Slurm896的19项CPU集成通过；当前入口4fb240b新增四性质范围，本地57项/Slurm899的30项通过。

完整矩阵895已运行第0组：alias895_0/实际Slurm job897，4个独立CUDA worker正在执行formation_energy_peratom 第1轮累计步数对照、optb88vdw_bandgap 第1轮原始输入对照、optb88vdw_total_energy 第1轮、ehull 第1轮原始输入对照。实际squeue、四个PID、日志/history均证实进展，不以ledger计划值替代运行证据。代表64结构699原子reserved峰值150MiB，最大原子批次64结构5238原子峰值672MiB；资源报告SHA cdf2f91b…绑定实际4并发决策。全部训练退出后才串行评测；其他波1–7按用户要求取消，893已释放，依赖仍afterany895_*。

带隙新增完成阶段：optb88vdw_bandgap r0为266epoch/185402步，best验证MAE0.15850093 eV（非测试值），训练/验证7784.60秒。全库55712结构/562055原子/64维float32/218分片缓存13.916秒，cache SHA e2820265…、checkpoint SHA 2beb0e53…；本地元数据/完整ID集合与身份核验通过，16结构链探针通过。服务器查询确认其r1已按patience结束139epoch/96883步，best验证MAE0.15119844 eV，第二份缓存已完成；当前original1对照继续，完整链/对照/测试尚未完成。

已核验新增结果：总能/ehull r0均300epoch完成（验证MAE分别0.05124270/0.11916633），全库缓存与身份覆盖通过；带隙r1完成139epoch（验证MAE0.15119844）且第二份全库缓存通过核验。形成能original1对照完成300epoch（验证MAE0.04533868），累计步数对照继续。上述均为验证指标，最终测试仍延后。

ehull新增完成阶段：r1为207epoch/143451步、验证MAE0.11350609；全库缓存与父身份/训练划分/投影参数核验通过，缓存9.729秒。其original1对照继续，完整0–5轮仍待完成。

正式work_root：/home/xmz/recursive/outputs/self_evolution/jarvis2021-seed123-final。
本地证据：outputs/self_evolution/cgcnn-seed123-evidence，已拉回real_acceptance/pilot_resources、两轮training/history/cache_timing、两份补充manifest、wave0/context与早期数据审计。全库55712构图/29任务划分此前已完成，原始重复ID/冲突标签已审计。生成证据均Git忽略。

完整研究实验尚未完成，goal保持active。已跑通真实r0→全库缓存→r1→全库缓存和串行链，尚无四性质完整r0–5/全部必要对照或最终测试曲线。资源口径与串行参照见 [资源记录](../plan/cgcnn_seed123_resources.md)，不能把短窗口并发吞吐当作完整实验加速承诺。

# 当前计划

已撤销尚未运行的895_1–7，保留当前四任务895_0/job897；四性质汇总入口已通过Slurm899并发布scope，893已释放。既有29性质长期计划保留为后续范围，当前验收以四性质完整六轮和对照为准。

历史待启动组均衡文件SHA 8c3cf7f…保留不改写；用户收敛范围后895_1–7已取消，当前仅wave000四任务继续。

1. 原pilot observer96216因完成标记正常退出；全矩阵只读observer工具会话26141每55秒查询实际squeue并读取活动wave/任务history，最多180轮。最新观测2026-11-02T09:54:58.007342+08:00，4任务均实际训练、无failure、0/4当前性质report完成。只读latest JSON/追加JSONL在本地outputs保存，不自动重启作业。
2. 继续当前895_0四性质、seed123、r0–5及原始输入/累计步数对照；formation energy复用已完成两阶段及缓存，不能重复训练或缩减目标。
3. 观察并发运行的实际吞吐/内存与失败；如worker失败，用源日志/Slurm终态定位并恢复，观察超时或本地monitor退出不代表计算失败。不得只凭计划文件宣称进度。
4. 893在895_0结束后按已启用四性质范围汇总MAE曲线/验证选轮/预算/覆盖；完成全部模型、控制、缓存/补充manifest、图表和失败审计后才可标记goal complete。不得以两轮pilot完成替代四性质完整矩阵完成。

# 变更记录

- 2026-09-29：完成 DPA-2 SSE-PBE-D 数据 manifest 与通用 MD5 校验支持；固定 Zenodo 10461723 的 17,073,396,886-byte 数据归档及官方 MD5，27 项回归、编译、元数据和格式检查通过。下一步提交推送；17 GB 归档后续仅在服务器任务目录由 Slurm 下载。
- 2026-09-29：作业 511 启动并进入首个新增 CUDA wheel 下载；等待期间开始 DPA-2 Zenodo 10461723 manifest 单元。下一步扩展下载器支持官方 MD5、补充测试与固定 17 GB 数据归档元数据，不在本地下载大文件。
- 2026-09-29：正确的 MatterSim 162 项增量下载已提交为 Slurm 作业 511；提交时同一账号作业 508 占用 node221，因此 511 为 PENDING。未干预 508，下一步只读监控 511 启动与下载日志。
- 2026-09-29：临时回环 1082 代理恢复服务器 Git，同步到 `3b27f13` 并成功 staging 162 项清单；查重命令在远端 shell 解析失败，未提交作业。下一步用简化队列门控重连提交正确的增量下载作业。
- 2026-09-29：错误作业 510 已在未运行时取消并退出队列；1080 pull 再次因本机直连 GitHub 路径失败。下一步以 Guqq 回环 1082 临时映射本机已验证的 7897 HTTP 代理恢复 pull，静态转发随单次 SSH 会话回收。
- 2026-09-29：服务器首次同步 162 项清单时代理 pull 失败，且命令条件边界错误导致提交了使用旧 144 项清单的作业 510；发现时作业仍为 PENDING。下一步先登记并连接取消 510，确认无错误下载作业后再恢复 Git 同步，保留全部既有 wheel。
- 2026-09-29：完成 MatterSim PyTorch 2.8.0/CUDA 12.8 闭包修复；setup 显式固定四项顶层版本并在安装后精确断言，本地 162/162 wheel 哈希、Linux/CPython 3.10 binary-only 离线解析、22 项回归、Python 编译与 Bash/whitespace 检查通过。下一步提交推送，再由服务器 pull 并通过 Slurm 增量下载新增 18 项 wheel。
- 2026-09-29：将 MatterSim 162 项 wheel URL/SHA-256 清单纳入 `data/manifests` 版本管理；二进制 wheel 仍保持忽略。清单计数、唯一性、安全路径、官方 PyPI 域、集合一致性和 162 项本地哈希均通过，服务器现在可在 pull 后直接 staging 到任务 tmpfs。
- 2026-09-29：进入论文数据 manifest 与下载器实现单元；先落地 MatterSim 的官方 `matbench_phonons` 来源和哈希，再以本地 HTTP 测试验证断点续传、原子落盘和错误保护。下一步完成实现与测试后提交，实际数据待 MatterSim wheel 作业释放网络后下载到任务数据目录。
- 2026-09-29：完成 `matbench_phonons` 官方 manifest 与通用标准库下载器；支持断点续传、Range 忽略时安全重启、SHA-256 门控和原子落盘，21 项测试及编译/格式/元数据检查通过。下一步提交推送；实际数据下载仍等待作业 507 释放 node221 网络，避免竞争。
- 2026-09-29：进入 MACE PhononDB 97 材料 manifest 单元；作者仓库提交 `480bc92d…` 的论文图目录已确认恰含 97 个唯一 MP ID，PBE 摘要对 97 项全覆盖且超胞信息完整。下一步固化 MP↔Togo 映射、来源 artifact 哈希和官方 ZIP URL 模板，并执行一致性检查。
- 2026-09-29：完成 MACE PhononDB 97 材料 manifest；固定 ffonons 提交、97 个唯一 MP↔Togo 映射、两项来源 artifact 哈希、0.01 THz 阈值和 NIMS 下载模板。22 项测试及来源树/PBE 摘要/超胞/哈希交叉检查通过；97 个原始 ZIP 待服务器下载后记录本地 SHA-256。
- 2026-09-29：作业 507 完成 144/144 wheel，独立全清单 SHA-256 为 0 且无残片；随后离线 setup 509 在 resolver 阶段安全失败，因为 Windows 跨平台解析遗漏 Linux 条件依赖，而自动选中的 torch 2.14 要求 PyPI 不存在的 NCCL 2.30.7。计划调整为显式固定已通过完整 dry-run 的 torch 2.8.0/torchvision 0.23.0/torchaudio 2.8.0 + CUDA 12.8 闭包，补齐后重新离线验收。
- 2026-09-29：MatterSim 下载作业 502 已退出队列，wheelhouse 停在 125/144；torch 的 0 字节 `.partial` 与连续连接超时表明计算节点公网中断，已完成 wheel 未受影响。下一步核对最终状态并在无重复作业时原地断点重提，不删除任何已有文件。
- 2026-09-29：确认队列无重复下载作业后，MatterSim wheelhouse 已在 node221 断点重提为作业 507；集群禁用 Slurm accounting，因此以普通队列、固定日志和文件校验验收。下一步核对 507 实际时限与续传位置。
- 2026-09-29：作业 507 已确认 node221、12 小时时限，PyPI 探针通过，torch 残片由 0 增长至 13,242,368 bytes；断点续传正常。下一步继续只读监控直至 144/144，不并发 MACE 下载。
- 2026-09-29：作业 507 运行 1 小时 31 分时仍为 RUNNING，完整 wheel 保持 125/144；清单中的 `torch-2.14.0-cp310-cp310-manylinux_2_28_x86_64.whl.partial` 已增长至 343,851,008 bytes，续传持续推进。下一步等待该作业完成后执行完整 SHA-256 校验；仍不并发启动 MACE 下载。
- 2026-09-28：MatterSim checkpoint 任务目录下载实现完成；node-local Slurm 入口支持 `.partial` 续传、原子落盘和大小/SHA-256 输出，K=0/K=1 只读取显式 tmpfs 文件。下一步随环境安装一起同步并在 node221 真实执行。
- 2026-09-28：跨 wheelhouse 哈希播种实现完成本地验收；脚本只为目标清单中源文件哈希精确匹配的缺失 wheel 创建硬链接，并拒绝覆盖错误目标。下一步提交推送并继续监控 MatterSim 502，完成后先离线安装 MatterSim，再用该脚本减少 MACE 重复下载。

- 2026-09-28：开始实现 Guqq 多连接共享反向 SOCKS；用户选择由首个成功绑定 1080 的会话提供代理，后续会话在转发绑定失败时仍正常登录并复用已有代理。下一步是修改本地 SSH 配置和 `AGENTS.md`，再执行静态检查。
- 2026-09-28：完成 Guqq 多连接共享反向 SOCKS 配置；本地 `ExitOnForwardFailure no` 已生效，固定动态反向转发仍为 Guqq `127.0.0.1:1080`。`AGENTS.md` 已同步记录首连接持有、后续连接复用以及持有者断开后新建连接恢复的行为。
- 2026-09-28：用户再次确认网络已重新配置并要求继续；已完整重读最新版 `AGENTS.md`。下一步按多连接共享规则继续存储检查，端口占用警告不再等同于登录失败。
- 2026-09-28：多连接规则验证成功使远端命令继续执行，但现有 1080 监听无法代理；存储检查确认唯一持久 ext4 分区仅余约 2.7 GiB、`~/.cache` 为 152 GiB。下一步不动未知监听或既有缓存，使用一次性回环 1081 代理并通过 Slurm 验证 tmpfs 可见性。
- 2026-09-28：一次性回环 1081 代理成功恢复 Git 和公网访问；Slurm 探针作业 `489` 在 `node221` 验证 `/dev/shm` 可写且约 126 GiB。确定使用 `/dev/shm/xmz-recursive` 作为可重建运行时根目录，下一步接入 sbatch 并创建 MatterSim 环境。
- 2026-09-28：首次 MatterSim 环境创建命令在 shell 解析阶段失败，未执行任何远端子命令、未留下半成品环境。下一步使用无内联 Python 的命令重试，并继续禁止源码编译。
- 2026-09-28：MatterSim venv 已创建，但其 pip 缺少 SOCKS extra，下载前即停止，尚未安装 MatterSim。下一步用 curl 下载 PySocks wheel并离线引导 pip；若第三次仍失败则按规范补充环境安装经验。
- 2026-09-28：PySocks 已成功离线引导，但非必要的 pip 升级下载中连接提前结束，MatterSim 尚未安装。连续三次环境建立未完成后已将原因和规避方法写入 `lessons.md`；下一步跳过安装器升级，直接安装 binary-only MatterSim。
- 2026-09-28：上一轮 pip 升级实际完成到 26.2.1，并在 SOCKS 索引请求中出现内部 urllib3 `PoolKey` 异常。下一步按已记录经验清理并重建仅属于本任务的 tmpfs MatterSim venv，保留 Python 3.10 自带 pip 22 后重试。
- 2026-09-28：MatterSim venv 已恢复为 pip 22 + PySocks；PyPI 版本核验发现原 1.2.5 pin 不可安装，现已根据官方 v1.2.3 API 审计校正并通过本地测试。下一步安装 1.2.3 并提交真实 Slurm K=0/K=1。
- 2026-09-28：短 SSH 会话中的长 pip 安装再次提前结束，MatterSim 仍未完成安装。策略调整为本地隐藏 SSH keeper 持续提供回环 1081，并先由 Slurm 网络探针验证路径，再通过专用 setup 作业安装环境；避免登录节点长任务和会话生命周期耦合。
- 2026-09-28：隐藏 1081 keeper 已运行且登录节点代理正常；inline Slurm 探针因跨 shell 引号拆分未提交，setup 也未提交。下一步改用仓库内固定 probe sbatch 文件，消除命令行 quoting 风险。
- 2026-09-28：固定 Slurm 网络探针 `490` 成功，确认计算作业的 1081 网络路径；已提交 MatterSim 环境安装作业 `491`。下一步监控该作业并在成功后提交真实推理。
- 2026-09-28：MatterSim setup `491` 因 keeper 退出导致 wandb wheel 哈希校验失败；未安装损坏内容。下一步由可轮询前台 keeper 保持代理，定向清除任务 cache 的 wandb 条目后重试。
- 2026-09-28：前台 keeper 会话 55766 已建立；网络复验 `492` 成功，setup 重试 `493` 已提交。下一步监控 493 并在成功后提交真实 K=0/K=1。
- 2026-09-28：纯转发 keeper 55766 被 Vlab 主动关闭；按经验调整为带应用层心跳的 keeper，下一步恢复代理并检查 setup 493。
- 2026-09-28：确认 setup 493 在新 keeper 启动前已因 atomate2 wheel 哈希不符失败；心跳 keeper 72062 当前稳定。下一步在该 keeper 下重新执行网络探针和 setup。
- 2026-09-28：心跳 keeper 下的网络探针 494 成功，已提交 MatterSim setup 495。下一步保持 keeper 并监控安装结果。
- 2026-09-28：心跳 keeper 72062 仍被 Vlab 重置，长代理下载方案判定不可用。下一步确认 495 后改为本地 wheelhouse + scp + Slurm 离线安装。
- 2026-09-28：确认 setup `495` 在下载 torch 2.14.0 wheel 时因代理中断导致 SHA-256 不匹配而失败，pip 拒绝安装；短时 keeper 已停止。当前进入本地 wheelhouse 实现阶段，setup 将支持 `--no-index --find-links`、安全重建专用 venv 和保存 freeze 清单。
- 2026-09-28：本地 MatterSim wheelhouse 已完成：144 个 Linux/CPython 3.10 wheel、离线依赖 dry-run 成功、SHA-256 144/144 一致；离线 setup 的语法、16 项回归、编译与 whitespace 检查均通过。下一步提交推送后传输到服务器 tmpfs。
- 2026-09-28：离线 setup 提交 `bf2c517` 已推送并在服务器成功 pull；整目录 scp 在约两分钟后被 Vlab 关闭。下一步按清单识别缺失/不完整文件，将大 wheel 分块短传、重组后再做完整哈希校验。
- 2026-09-28：scp 对照吞吐仅约 30 KiB/s，分块 scp 不可行；PyPI URL/官方哈希清单 144/144 生成成功，固定断点续传脚本已通过 CRLF、续传、跳过和失败保护测试。下一步经 Git 同步脚本并重复短会话续传。
- 2026-09-28：固定脚本首轮服务器下载有效，已完成从 aioitertools 到 boto3 等多个 wheel；botocore 中途 SSL EOF 后残片保留。因 curl 在死连接上重试过久，增加低速超时后再续传。
- 2026-09-28：独立 1081 的后续会话仍被跳板机快速重置，但登录节点无代理 PyPI HEAD 已成功。策略调整为固定 node221 的 Slurm 直连下载作业；下一步本地实现、测试、Git 同步后提交。
- 2026-09-28：固定 node221 的 Slurm 直连下载作业 `499` 已提交。下一步监控其 HEAD 探针、续传日志和最终 144 项哈希验收。
- 2026-09-28：作业 499 约 4 分钟时 botocore 残片已达 7,118,848 bytes，直连有效但按总量估算需 7–9 小时；调整 sbatch 时限为 12 小时，下一步尝试原地延长运行中作业。
- 2026-09-28：集群拒绝普通用户原地延长 499，作业未改变。下一步利用已验证的断点语义取消 499，并在同一 node221 以 12 小时时限立即重提。
- 2026-09-28：作业 499 已取消，12 小时续传作业 `500` 已提交到 node221。下一步核对实际时限和断点恢复日志。
- 2026-09-28：作业 500 已确认 node221、12 小时且从残片续传；等待期间并行进入 MACE 独立 wheelhouse 解析，继续保持 backbone 环境隔离。
- 2026-09-28：作业 500 在 35/144 的 h5py 因过严低速阈值失败；按 lessons 调整为慢速直连阈值和长有限重试。MACE 本地 wheelhouse 已完成 49 项离线解析/哈希验收，python-hostlist 纯 Python sdist 已单独审计构建。
- 2026-09-28：下载重试调整已同步，MatterSim 12 小时续传作业 `501` 已提交到 node221；下一步监控 35/144 之后的续传和最终哈希。
- 2026-09-28：作业 501 在前置 HEAD 的单次 15 秒连接超时处失败，未改变 wheelhouse；下一步为探针增加最多 10 分钟有限重试并重提。
- 2026-09-28：探针重试补丁已同步，MatterSim 下载重提为作业 `502`；下一步确认其通过探针并从 h5py 残片继续。
- 2026-09-28：MACE 独立离线 setup 已完成并通过 Bash、静态、16 项回归和编译检查；待 wheelhouse 同步后在 Slurm 中做真实安装。
- 2026-09-28：MatterSim 502 在大 wheel 上慢速运行；等待期间只 staging MACE 两个清单与 39 KiB 审计 wheel，不启动并发大下载。
- 2026-09-28：MACE 控制文件 staging 已完成，服务器行数 48/49、审计 wheel 哈希通过；MatterSim 502 同期推进到 `m` 段依赖并继续独占公网。
- 2026-09-28：MatterSim 离线 setup 补齐安装前完整 SHA-256 门控和代理清除；本地 Bash、16 项回归、编译与静态检查通过。
- 2026-09-28：进入 Guqq SSH 连接故障诊断阶段；用户报告配置反向 SOCKS 后无法连接。下一步是复现连接并根据详细 SSH 日志定位失败阶段。
- 2026-09-28：完成 Guqq SSH 连接故障诊断；ProxyJump 和两层公钥认证均成功，失败原因是 Guqq `127.0.0.1:1080` 已被其他会话占用，且 `ExitOnForwardFailure yes` 导致新 SSH 整体退出。对照连接确认该监听已失去代理能力，本机无残留 `ssh.exe` 进程；未终止任何可能属于用户的远端会话。
- 2026-09-28：进入 SSH 会话级反向 SOCKS 转发配置阶段；用户要求每次 `ssh Guqq` 自动转发、断开后自动停止，并明确跳过 `net.sh` 和 180 秒等待。下一步是备份并最小化修改本地 SSH 配置，然后执行连接生命周期测试。
- 2026-09-28：完成 SSH 会话级反向 SOCKS 配置和验证；Guqq 经 `127.0.0.1:1080` 获得的出口 IP 与本地一致，并在会话退出后拒绝连接。测试同时发现 Guqq 的 `/home/xmz/recursive` 已不存在；后续服务器实验需先恢复工作树。
- 2026-09-28：开始修订 Guqq 网络操作规范；原因是会话级反向 SOCKS 已实测可用，不再需要 `bash net.sh` 和固定 180 秒等待。下一步是修改 `AGENTS.md` 并检查命令、路径、Markdown 和旧流程残留。
- 2026-09-28：完成 Guqq 网络操作规范修订；`AGENTS.md` 现要求登录节点联网命令显式使用会话级 SOCKS，禁止运行 `bash net.sh` 和固定等待，并区分了登录节点与 Slurm 计算节点的网络边界。
- 2026-09-28：用户确认网络已重新配置并要求继续；已重读更新后的 `AGENTS.md`，SSH/反向 SOCKS 故障诊断阶段结束。下一步按新规范恢复服务器仓库并检查运行环境。
- 2026-09-28：服务器仓库同步成功并完成轻量资源检查；发现 `/` 仅余约 2.6 GiB，直接创建三个环境和下载模型有耗尽磁盘风险。下一步只读查找可用挂载点与任务相关占用，再确定环境布局。
- 2026-09-28：存储检查连接因 Guqq `127.0.0.1:1080` 被占用而被 `ExitOnForwardFailure` 提前终止；本地未发现存活 SSH 进程。下一步使用禁用新增转发的连接只读确认远端监听归属，不擅自终止未知进程。
- 2026-09-28：首次禁用新增转发的诊断连接在代理 pull 阶段无输出并超时，未取得端口归属信息。下一次将 pull 网络等待限制为 5 秒，保证后续只读诊断有机会执行；若仍失败则按连续三次失败规则查阅经验记录。

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
- 2026-09-28：用户确认 remote 为 `https://github.com/Mingzhe-Xuan/recursive.git`；已验证远端 `main` 存在、本地分支正在跟踪且工作区干净，进入服务器 Slurm 验收阶段。

- 2026-11-02 00:35 +08:00：进入三 backbone Sequential Self-Evolution 计划阶段。用户选定 CGCNN、Matformer、iComFormer，并允许额外线性层；下一步编写 plan_2.md，区分逐轮监督训练与推理计算量，保留旧 Goal 1 历史。

- 2026-11-02 00:41 +08:00：完成 docs/plan/plan_2.md，定义三个 backbone 的逐任务节点缓存、线性投影、新阶段训练、全任务覆盖、固定划分和预算对照；UTF-8、12 节标题、数学/围栏、8 个本地链接及历史保留检查通过。下一步为后续实施的数据与官方接口审计，本轮未运行训练。

- 2026-11-02T00:45+08:00：开始用户授权的 CGCNN 单 seed 完整实施，seed 123；下一步固定数据任务和原生模型，并实现可验收的循环流程，不缩小为仅 mock 验证。

- 2026-11-02T01:09+08:00：完成本地实现阶段与 35 项测试、静态检查；服务器确认空闲 RTX 5090 和 246 GiB 持久可用空间，已制定独立 venv 计划。下一步提交、push、服务器 pull 后运行 setup/prepare 和真实两轮 pilot。

- 2026-11-02T01:33+08:00：进入真实环境/数据阶段，879通过GPU/8项测试，880因代理断线失败且仅留下1.9MiB数据残片。下一步固定构建工具并采用SFTP断点上传完整ZIP，再恢复真实预处理和单seed pilot；不以测试通过代替全任务完成。

- 2026-11-02T01:58+08:00：源审计发现并解决raw计数/重复ID与冲突标签问题，所有29任务保留，形成能歧义标签按规则排除。884因旧count门控失败，885依赖任务已取消；887审计完成。下一步以新manifest规范化55712结构后构图，固定协议运行seed123形成能两轮pilot。

- 2026-11-02T02:12+08:00：进入真实训练阶段：888环境和889数据均通过，890 RUNNING并已产生4个epoch验证指标。新增只读CUDA验收与全任务扩展门控，下一步等待两轮pilot完成，再自动扩展全部任务；实现完成不等于目标已完成。

- 2026-11-02T02:21+08:00：全库和29任务准备已验收，890 RUNNING到epoch32；scontrol逐项证实891/892/893依赖条件，单seed完整矩阵已耐久排队。小型审计、环境和训练history已SFTP回本地并核验忽略规则。下一步持续监控实际训练/验收/全矩阵，目标未完成且保持active。

- 2026-11-02T02:27+08:00：继续轮首先核实890 RUNNING到epoch44、best验证MAE0.06514559，891/892/893仍为正确依赖等待。进入短执行开销诊断以评估完整矩阵成本，只新增外部脚本且不修改现有核心/配置/权重；下一步记录测量证据再决定是否存在可用优化。

- 2026-11-02T02:35:29+08:00：完成890.0隔离执行诊断，native及segment候选前向/梯度均通过固定容差；共享GPU计时19.316/10.133ms，仅保留候选，不修改原生生产路径。890已完成62个epoch、best验证MAE0.05821373；依赖链891/892/893仍有效，小型证据已拉回。下一步等待pilot及真实两轮验收，无最终测试曲线。

- 2026-11-02T02:37:09+08:00：本轮为verified wait：squeue确认890仍RUNNING（34:14），远程history实测完成66epoch、46002步、best验证MAE0.05821373，无failure.json；891/892/893仍PENDING(Dependency)。未新增或重启计算，下一步等待原生第0轮结束及第1轮缓存链验收。

- 2026-11-02T02:42:59+08:00：建立本地低频持久observer（工具session4846，SSH字节stdin，远端仅短管理查询，本地等待），实测890 RUNNING39:59，r0epoch78、无失败，r0训练/缓存和r1尚未完成。此前text模式CRLF导致观察失败，已只停止自有本地observer树并修正，未重启/改动890。下一步续查同一observer及阶段转换，观察失败不等于计算失败。

- 2026-11-02T03:09:35+08:00：本轮连续verified wait到r0epoch131、best验证MAE0.05133525，仍无失败/训练完成/缓存标记。完成资源估算记录：31个阶段预算=6演化+5原始+20累计对照，真实62epoch均值30.72秒、全任务有效标签801007，未早停标签同比例外推47.5天；未改变协议，显存和IO分项列为待验证。持久observer4846仍活跃，可继续原handle。

- 2026-11-02T03:18:02+08:00：完成scripts级pilot_resources资源测量实现，已有891入口在数值验收后使用两阶段独立副本采样，记录全库缓存字节数、校验读取/传输、代理步骤时间及PyTorch显存峰值。全部39项CPU回归通过（扩展原三阶段测试，移除标签文件、checkpoint/manifest/所有缓存分片SHA不变、异协议拒绝、CPU显存None）；真实GPU结果尚未运行。src/config未改，890恢复身份不变，下一步提交同步后继续等待原作业。

- 2026-11-02T03:21:00+08:00：资源实现ee775bc已成功push并由Guqq代理git pull同步；远端HEAD/accept入口引用核对通过，git diff 4379c88 HEAD -- src/self_evolution configs/self_evolution为空，证明运行中核心/训练配置未变。891仍afterok890，890 RUNNING1:17:39，最新observer r0epoch155。本地直接push一度网络失败，使用已验证仅回环7897 HTTP代理单次git配置重试成功，未改全局代理。下一步继续等待pilot并验证真实资源结果。

- 2026-11-02T03:29:04+08:00：进入scripts级独立任务并行调度实现阶段。原因：完整矩阵串行估算约47.5天；实际节点48核/257787MiB，890 RSS约3GB，计划依据真实两阶段最大批次资源测量在同一GPU allocation内并行独立任务，同时串行评测以保留部署计时口径。现有890–893队列不变，先实现/测试可审查入口，资源门控满足后再替换pending数组。

- 2026-11-02T03:46:18+08:00：独立任务pool实现/测试完成：45项完整本地回归通过，最终账本/预算元数据改动后6项调度测试再次通过；覆盖29任务无遗漏、实际子进程并发/失败隔离/全训练退出后串行评测/恢复档案、资源config/core/graph/SHA门控。补充代表及最大原子数批次测量，OOM明确记录并退回1。旧observer4846已正常到期，新17629实测890仍运行，r0epoch205。调度计划细化为在job入口读取实际891资源再启用并行；允许此前排队afterok891以避免旧数组启动竞态，实际测量前不启动worker。下一步提交同步并通过Slurm CPU检查，再审查并替换pending队列。

- 2026-11-02T04:02:53+08:00：完成Linux894验收及pending调度迁移：18项CPU测试通过，895八波pool afterok891、893 afterany895_*经scontrol确认，旧892全PENDING取消，当前890未改。进入第1轮阶段：r0训练222epoch/154734步、best验证MAE0.04822800，全库55712/562055节点缓存已完成并通过16结构链一致性；r1已实际训练。小型训练/缓存/链/迁移证据已拉回，新observer96216续查第1轮，真实完整两轮及29任务循环仍待完成。

- 2026-11-02T04:12:44+08:00：进入缓存交付元数据补全阶段：基础缓存已有严格SHA身份，但计划要求的完整配置和分片字节数仍缺内联字段。使用受基础manifest SHA绑定的外部补充manifest并在chain_manifest引用，避免改变正在消费的缓存身份/权重；将通过CPU与Slurm检查并接入891及完整任务。当前主计算继续第1轮，任务范围不变。

- 2026-11-02T04:31:51+08:00：缓存交付审计实现完成，基础manifest/权重/分片保持不变，补充manifest含完整配置、源/图/原子顺序绑定、全部成功/失败ID与逐片SHA/字节，并由根chain以SHA引用。公开evaluate入口在测试前校验所有对照；CUDA每个run/evaluate复用已验证的精确环境检查，覆盖pool晚启动进程。46项本地测试通过，包含缺标签、幂等、错来源/配置/跨任务对照/分片损坏/缺对照拒绝、环境失败不训练；下一步提交推送并Slurm CPU复核后同步已排队入口。当前r1epoch69、best验证MAE0.04456512，目标仍active。

- 2026-11-02T04:40:34+08:00：896a171已由Guqq代理pull同步，现有prepared源manifest SHA和graph_config轻量复核通过，核心src/config diff为空。Slurm896完成当前19项CPU集成（ExitCode0:0，6.95秒），包括真实Linux任务锁/完整元数据/对照预检和环境失败阻断；真实全库补充审计将随891/正式任务执行，当前890继续原第1轮无重启。observer96216仍确认RUNNING，r1epoch85、best验证MAE0.04418608。下一步等待两轮完成和891真实CUDA/资源验收，再审计895并发决策及完整矩阵结果。

- 2026-11-02T05:02:38+08:00：本轮为verified wait，续查原observer96216，连续确认原890 RUNNING；第1轮推进到128epoch、best验证MAE0.04402161，train_done/cache_done仍false且无failure。未改源码/配置/预算/队列，未重启计算；下一步继续等待第1轮及891实际验收。

- 2026-11-02T05:49:31+08:00：进入全任务矩阵阶段：890/891均成功结束，r1完整164epoch/114308步、best验证MAE0.04402161，全库缓存完成；真实CUDA32结构native/batch/两阶段cache-chain验收和两份补充manifest/全分片审计通过。资源报告最大批次672MiB reserved支持4并发，895_0/job897四个worker已由PID/训练日志/history证实运行，剩余波待队列。证据已拉回并本地核验SHA/完整配置，observer8154继续全矩阵，目标仍active。

- 2026-11-02T06:07:17+08:00：进入pending分组均衡实现阶段。依据实际四并发约30秒/epoch及固定任务标签计数，拟保留已有第0组，将其余任务按标签量排序减少barrier等待；静态代理指标降低22.5%，不承诺实际同幅加速。只新增受SHA/配置校验的运行时分组文件和读取接口，不动模型/训练预算或当前wave，测试/Slurm复核后再发布。


- 2026-11-02T06:14:57+08:00：pending分组实现/文档完成，本地49项完整回归和最终接口3项重验通过。仍未启用运行时计划；下一步提交同步并Slurm CPU复核，再校验所有实际已启动wave后原子发布。observer8154继续证实首组正常训练，无failure。


- 2026-11-02T06:17:54+08:00：调度入口aae5124已推送并Guqq代理pull；Slurm898固定日志确认22 passed in 6.92s。候选runtime分组经SHA/来源/配置/全部既有ledger校验后原子发布，SHA 8c3cf7f017ccf2794584db01c8dc55dcd8c5d54c86a3904736cbb5f2048ebfcb；唯一已有wave000成员原样保护，895不取消/不重提，未来wave读取新分组，893依赖不变。最新实际观测2026-11-02T06:17:30.378172+08:00四任务持续训练、无failure、0/29报告完成；完整目标仍active。


- 2026-11-02T06:21:42+08:00：上一goal turn为progress（aae5124调度及运行时分组发布）；本轮为verified wait，通过工具会话8154重复读取实际SSH/squeue与训练history，最新2026-11-02T06:21:10.398471+08:00确认895_0/job897仍RUNNING。formation_energy_peratom controls/original/round_001 epoch117/steps81549；optb88vdw_bandgap round_000 epoch120/steps83640；optb88vdw_total_energy round_000 epoch115/steps80155；ehull round_000 epoch116/steps80388。无failure、0/29报告完成，895_1–7仍PENDING；未重启/重提/改预算，完整29项r0–5及对照目标继续active。下一步等待现有训练阶段结束并核验缓存/控制转换。


- 2026-11-02T06:32:17+08:00：上一goal turn为verified wait；本轮继续通过原工具会话8154连续12次有界轮询（约9分钟），实际squeue/history确认895_0/job897持续RUNNING。最新2026-11-02T06:32:10.491264+08:00：formation_energy_peratom epoch139、optb88vdw_bandgap epoch142、optb88vdw_total_energy epoch136、ehull epoch139；无failure，0/29完整报告。单次无输出后续查同一handle得到新进展，未重启/重提/改配置。当前阶段未转换，继续等待既有训练并核验完成后的缓存/对照；完整目标仍active。


- 2026-11-02T06:41:36+08:00：上一轮为verified wait，本轮续查原observer8154并核对真实资源；Slurm897仍RUNNING，最新2026-11-02T06:41:20.594669+08:00为formation_energy_peratom epoch157、optb88vdw_bandgap epoch161、optb88vdw_total_energy epoch154、ehull epoch157，无failure、0/29报告。短时Slurm srun元数据查询实测GPU利用率90%、NVML显存4423/32607MiB，节点CPUAlloc16/48、CPULoad5.65；单点利用率不能证明更高并发收益，因此保持已验证4并发、8波和已发布不可变分组，不改预算或重提作业。下一步等待阶段完成和缓存/对照转换，完整目标仍active。


- 2026-11-02T07:01:24+08:00：上一goal turn为verified wait及资源核查；本轮通过原observer8154连续24次有界轮询、约18分钟verified wait，实际squeue/history持续确认895_0/job897 RUNNING。最新2026-11-02T07:00:35.745747+08:00：formation_energy_peratom controls/original/round_001 epoch195/steps135915；optb88vdw_bandgap round_000 epoch202/steps140794；optb88vdw_total_energy round_000 epoch192/steps133824；ehull round_000 epoch196/steps135828。无failure、0/29完整报告，阶段尚未转换；未改模型、配置、预算或队列。下一步等待既有训练结束并核验全库缓存/对照转换，完整29项r0–5与必要对照目标仍active。


- 2026-11-02T07:32:57+08:00：进入带隙r0阶段转换核验。持续verified wait后，07:31:45实际监控显示其cached_rounds=1、r0不再活动；其他三任务仍在训练且无failure。下一步先核对实际训练/缓存/链元数据和r1衔接，不把监控计数当作完整缓存验收或全部矩阵完成。


- 2026-11-02T07:37:47+08:00：完成带隙r0阶段转换核验（本轮为持续verified wait后的实际实验progress）。r0按validation patience结束于266epoch/185402步、最佳验证MAE0.1585009272 eV、训练/验证7784.60秒；缓存13.916秒，55712唯一ID集合与已验收全库完全一致、562055原子/64维float32/218分片。checkpoint SHA 2beb0e53…、cache SHA e2820265…与training/timing/root chain/16结构一致性记录相互匹配，config/core/graph身份一致。16结构直接链/缓存最大节点差1.7166e-5，通过固定atol2e-5+rtol1e-4；第1轮已实际训练（拉回初始7epoch历史）。小型证据及本地metadata核验JSON保持Git忽略。最新2026-11-02T07:37:16.037377+08:00四worker仍训练、无failure、0/29完整报告；全29项r0–5/对照/最终测试仍未完成，目标继续active。下一步续查带隙r1、形成能对照及总能/ehull的r0→缓存→r1转换。


- 2026-11-02T09:26:24+08:00：进入观察恢复阶段。原code-mode轮询host超时后失效；重查8154得到SSH远端关闭，本地watch进程缺失。该证据仅证明观察停止，计算终态尚未知；下一步重新只读核对Slurm及真实产物，不因观察失效重启训练。


- 2026-11-02T09:27:19+08:00：观察恢复核查完成：Guqq实际squeue确认895_0/job897 RUNNING4小时04分，893和剩余组仍等待，无failure。总能/ehull r0均300epoch完成并缓存，r1继续；带隙r1为139epoch完成、第二份缓存已生成并训练original1对照；形成能original1完成300epoch、当前累计步数对照继续。下一步恢复原只读观察器流程并核验新增metadata，不改变训练。


- 2026-11-02T09:29:37+08:00：按用户明确新指示调整当前范围为首组四性质0–5轮，其他25项以后开展；这是用户范围变更，保留全部已有结果及科学配置。下一步仅撤销pending其他组并适配汇总，不能停止当前897四worker。


- 2026-11-02T09:40:21+08:00：四性质范围入口/汇总实现完成，本地57项完整回归通过。其他pending组895_1–7已逐一撤销、895_0仍RUNNING、893 held；待提交同步并Slurm CPU复核后发布execution_scope.json并release893。源src/config不变，原始29性质计划保留为后续范围。


- 2026-11-02T09:51:16+08:00：完成用户四性质范围调整。4fb240b已Guqq pull并通过Slurm899全部30项CPU集成（12.01秒），本地57项和最终8项均通过。runtime execution_scope.json SHA ef3595e2a3d20845dca44d5386a0eee5e6bbcb0082c588e65c09041de13ef3a0已校验config及wave000四成员后原子发布，895_1–7取消、895_0/job897继续、893已release且仍afterany895。其他25性质明确deferred，训练核心/预算/seed/全库55712结构缓存不变；当前验收仅四性质0–5轮及必要对照。


- 2026-11-02T09:51:16+08:00：新增真实metadata核验通过：总能r0 300epoch/209100步、best验证MAE0.05124270436、缓存14.027秒；ehull r0 300epoch/207900步、best验证0.11916632863、缓存14.113秒；带隙r1 139epoch/96883步、best验证0.15119843529、缓存9.329秒/86813参数（投影5980）。三份缓存均55712唯一ID/562055原子/64维float32/218分片，完整ID集合、cache/timing/chain/checkpoint/config/core/graph及父缓存身份匹配，固定16结构组合容差检查记录一致。形成能original1为300epoch/209100步、best验证0.04533867818，独立原始输入/相同训练ID与归一化核验通过；累计对照继续，目标269042步。数据/审计JSON均保持Git忽略；最新2026-11-02T09:50:22.941194+08:00四任务仍训练、无failure，本阶段完整结果尚未完成。


- 2026-11-02T09:53:32+08:00：上一goal turn完成用户四性质范围调整，为progress。当前进入ehull r1产物核验；原观察器26141实际确认895_0仍RUNNING，ehull cached_rounds=2/original1对照继续，其余三任务正常，无failure。下一步拉回并核验r1完整ID覆盖、父缓存/权重/config/core/graph身份、训练归一化及固定组合容差记录；不将两轮完成当作本阶段六轮实验完成。


- 2026-11-02T09:55:54+08:00：完成ehull r1产物核验（本轮progress）。r1按patience结束207epoch/143451步，best验证MAE0.11350609162，训练/验证6198.72秒；全库第二份缓存9.729秒、55712唯一结构/562055原子/64维float32/218分片。checkpoint SHA c7a4f7d3ab6cf44da47d95f7d43839977e642890fffe46b089a8697c4eb27be9、cache SHA 7bfefe867e79e963ca1d58820e0195c6dc2b5431c60a4ba7429c2b4b8f722cc4、父缓存SHA 520e75542644a8881e0e0132de5faa042c8107c108fdf1166816c14aa177e994与chain/timing/config/core/graph匹配；与r0相同训练归一化/ID hash，新增投影5980参数（总86813），累计主链351351步。16结构链探针两阶段最大节点差2.6703e-5/2.8610e-5，按固定atol2e-5+rtol1e-4组合容差通过，不能只与绝对容差比较。小型metadata及审计JSON已拉回并Git忽略。最新2026-11-02T09:54:58.007342+08:00当前四worker仍训练、无failure，四性质完整0–5轮/对照/最终曲线仍未完成。下一步等待总能r1与现有对照，并核验后续转换。
