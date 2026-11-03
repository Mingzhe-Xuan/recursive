# 经验教训

## 2026-09-29：Windows Git 应复用已启用的回环代理

- 现象：浏览器网络已恢复，但 Git/curl 直连 `github.com:443` 仍连续出现连接重置、空响应和连接超时；Windows Internet Settings 实际启用了 `127.0.0.1:7897`，WinHTTP 与进程环境变量则仍显示直连。
- 判断：系统浏览器代理、WinHTTP 和命令行环境是三套独立配置，不能从浏览器可联网推断 Git 直连可用。SSH 备用路径也必须先核对官方主机指纹；本次端口 22 返回的 ED25519 指纹不匹配，因此不得接受或写入 `known_hosts`。
- 处理：先只读检查 Internet Settings，再对单次 Git 命令显式设置 `http.proxy`/`https.proxy` 为已启用的回环代理；HTTPS 证书验证保持开启。推送成功后不修改仓库 remote 或全局 Git 配置。
- 安全约束：代理只使用本机回环地址；未知或不匹配的 SSH 主机密钥一律拒绝，不能为绕过网络故障使用 `StrictHostKeyChecking=no` 或关闭 TLS 校验。

## 2026-09-28：Windows 环境直连 arXiv PDF 不稳定

- 现象：`Invoke-WebRequest` 可能长时间占用目标文件却留下 0 字节文件；切换到 `export.arxiv.org` 后仍可能发生文件锁；`curl.exe` 可能因 Schannel TLS 握手失败或极低速传输而中断。
- 判断：必须同时检查命令退出状态、文件大小和 `pdfinfo`，不能以文件名存在作为下载成功依据。
- 处理：论文内容优先通过 arXiv HTML、出版社页面、官方模型卡和官方仓库交叉核验；PDF 下载改在网络稳定环境或服务器执行，并使用临时文件下载、校验成功后再移动到最终路径。
- 安全约束：0 字节或未通过 `pdfinfo` 的文件不得作为研究依据，也不得进入数据或文献清单。

## 2026-09-28：固定反向 SOCKS 端口的多会话语义

- 现象：首个 SSH 会话占用 Guqq `127.0.0.1:1080` 后，后续会话再次申请同一 `RemoteForward` 会收到端口绑定失败；若设置 `ExitOnForwardFailure yes`，主 SSH 会话也会在执行远端命令前退出。
- 判断：端口处于 `LISTEN` 不等于代理可用，必须用带有限超时的 `curl --proxy socks5h://127.0.0.1:1080` 验证；同样，Git 只输出 `Cloning into` 不能证明 clone 完成，需检查目录、HEAD 和 remote。
- 处理：多连接共享固定端口时使用 `ExitOnForwardFailure no`。首个成功绑定的会话持有代理，后续会话可复用；持有者断开且代理失效后，新建 SSH 连接重新绑定。联网命令始终设置 SOCKS 环境变量与有限超时。
- 安全约束：诊断未知 1080 监听时只读检查，不擅自终止可能属于用户的远端会话，也不把端口暴露到非回环地址。

## 2026-09-28：新 venv 通过 SOCKS 引导 pip

- 现象：标准库创建的新 venv 中，pip/requests 可能尚未安装 PySocks；即使 `ALL_PROXY=socks5h://...` 正确，也会在联网前报 `Missing dependencies for SOCKS support`。
- 判断：这是 pip 客户端缺少 SOCKS extra，不是代理本身不可用。可先用支持 SOCKS 的 curl 下载 `PySocks-*-py3-none-any.whl`，再由 pip 从本地文件离线安装。
- 处理：先引导 PySocks，再直接安装任务依赖；不要把非必要的 pip/setuptools 全量升级放在关键路径前。长下载关闭进度条并设置显式 timeout/retry，完成后以 `pip show` 和实际导入分别验证。
- 安全约束：登录节点安装依赖时使用 `--only-binary=:all:`；若缺少 wheel，停止并转交 Slurm，不能在登录节点隐式源码编译。

补充：Vlab 会主动关闭纯 `ssh -N` 空闲 keeper，SSH protocol keepalive 不足以保证长下载期间代理存活。需要在远端运行轻量应用层心跳，或改用本地下载后 scp；不能仅凭本地 ssh 进程存在推断代理会持续可用。

再次验证表明，20 秒应用层心跳也不能阻止 Vlab 在数分钟后重置长连接。因此反向 SOCKS 只适合短时 Git/元数据访问，不用于多 GiB 依赖下载。长下载改为本地构建目标平台 binary wheelhouse、生成哈希清单，再通过 scp 传入任务 tmpfs，由 Slurm 离线安装。

## 2026-09-28：慢速直连下载的超时与断点策略

- 现象：网络重配后，登录节点和 Slurm 计算节点可以直连 PyPI，但带宽波动明显；`--speed-limit 1024 --speed-time 30` 会把慢而可用的连接连续判为失败，作业在同一 wheel 上耗尽少量重试。
- 判断：用于识别失效 SOCKS 隧道的激进低速阈值不能直接复用于独立的计算节点直连。连接超时、低速超时、重试总时长应分开配置，并由 Slurm 的总时限提供最终边界。
- 处理：wheel 始终写入 `.partial`，单文件哈希通过后才原子改名；直连默认使用更低的 128 B/s、120 秒低速阈值和最长 2 小时的有限重试，测试通过环境变量缩短重试。作业失败或超时后在同一节点重提，已校验 wheel 跳过、残片继续。
- 安全约束：不得把 `.partial` 当作 wheel 安装；只有完整清单全部通过后才能进入离线环境安装。

## 2026-11-02 00:41 +08:00：逐阶段特征循环的模块边界与缓存依赖

- 每轮训练新权重的 self-evolution 与冻结同一 backbone 的 block 递归具有不同的梯度和部署语义；新流程使用独立 self_evolution 包，接口和长期边界记录在模块 README，避免复用旧冻结约束导致当前阶段不可训练。
- 原子特征循环应显式区分静态原始几何和当前权重产生的边/角 embedding。缓存需绑定任务、seed、轮数、checkpoint、结构顺序及上游 manifest；不能只凭文件存在复用。
- 历史阶段链是新结构完整推理的组成部分，累计训练与串行推理成本应分别统计。长期 checkpoint 与缓存不能只保存在易失的 /dev/shm。
- Windows PowerShell 向 Python 管道传递中文文本前应显式设置 UTF-8 OutputEncoding；修改后复读检查，避免将问号替代字符写入开发记录。本轮检查发现后已修复新增记录，既有历史未改动。

## 2026-11-02T01:09+08:00：CGCNN 任务、源码和恢复身份

- ALIGNN 常用批量脚本不等于论文全部任务；原结果表的 29 项还包括 max_efg、avg_elec_mass、avg_hole_mass，必须按表核对。
- 固定第三方源码及原子描述符的字节哈希，并用 .gitattributes 禁止 EOL 转换，否则 Windows checkout 会破坏相同代码的 SHA-256 验收。
- 恢复身份使用实际计算代码/资源的内容 hash；Git commit 单独记录为来源。仅更新开发文档不能导致已完成训练因 HEAD 改变而失去恢复能力。
- Windows 原生 SSH 会丢失部分嵌套参数引号，PowerShell 文本管道还可能额外发送 CRLF；远程管理改用 Python subprocess 的 bytes stdin，保留固定 bash 脚本原始字节，不把源码在服务器上直接改写。

## 2026-11-02T01:17+08:00：Figshare 的空响应不是成功下载

三次相关网络故障后复查既有网络经验：反向 SOCKS 的 TLS 错误与 Figshare 主域 202/0-byte 响应均不能视为资源可用。已查明同一固定文件的官方 API /v2/file/download/29204826 返回真实 application/zip、31,911,815 bytes，并重定向到官方 S3；后续仅在官方 MD5 和字节数通过后发布。不要因 requests.raise_for_status 未报错就接受 202 或零字节文件。环境依赖改为本地下载缺失 wheel 后 scp，服务器 Slurm 离线安装。

## 2026-11-02T01:37+08:00：SFTP reput 的已完成文件语义

同一传输连续失败3次后查阅既有记录，未发现此语义：OpenSSH sftp batch 中 reput 对远端同大小文件会返回错误并中止后续命令，不能把它当作网络故障无限重试。管理助手改为允许该命令的已完成错误，随后逐项 ls 检查精确大小，最终仍由 Slurm SHA-256/MD5 验收；真正断线继续从已写入字节恢复。错误循环仅终止已识别的本任务 Python/SFTP 进程树，不触碰其他 SSH 或 Slurm。

- 2026-11-02T01:39+08:00 补充：OpenSSH reput 对不存在的目标也会失败；在任务资源目录中仅对缺失目标初始化空文件后再续传。SHA256SUMS 是会变化的小型元数据，必须完整 put 覆写，不能对旧清单 reput 拼接；普通同名 wheel 和固定 ZIP 才允许续传。最终大小和哈希都必须通过。

## 2026-11-02T01:44+08:00：预处理来源必须进入缓存身份

任务标签与图数据即使ID相同，也必须显式匹配dataset SHA。图恢复身份还需绑定构图代码、原子描述符与NumPy/pymatgen版本；修订来源协议后应使用新prepared目录，不能给旧图直接改写成新builder身份。后台传输助手可能提前提交下一作业，变更协议前需核查其提交状态并保留旧产物。

## 2026-11-02T01:52+08:00：论文样本数与原始归档去重必须分别审计

数据单元连续出现count门控失败后复查已有经验，未覆盖重复ID情形。Slurm886进一步证明固定官方归档包含重复JVASP-96735，严格select_labels因重复ID拒绝；不能直接用论文样本数约束raw行数或直接取第一条。后续只读审计先输出raw/unique计数、逐重复记录hash和变化字段，再判断完全一致去重或冲突处理，并保留官方checksum不变。

- 2026-11-02T01:58+08:00 规范化决策：本归档并非55722条唯一结构，而是55723行/55712个唯一ID。禁止直接first/last覆盖冲突标签；同ID同结构的不同有限标签按任务设为不可用，其他标签与结构继续保留。完全重复源记录只保留一份，记录所有原始索引/hash，避免重复样本跨split或增加不明权重。

## 2026-11-02T02:35:29+08:00：已有Slurm allocation的隔离诊断

srun --jobid=<owned-allocation> --overlap可共享本任务GPU做短时诊断，必须另存checkpoint副本与结果并记录共享GPU条件。固定批次原生pooling与segment mean即使前向/梯度通过容差，也不能据此静默改写运行中src或checkpoint身份；共享GPU计时不能推断完整训练加速。通过ssh bash -s传入管理脚本时，srun默认stdin可能消耗后续脚本文本；后续使用--input=none，权威结果以独立输出文件为准，不因管理端未打印尾部而重复启动。

- 2026-11-02T03:18:02+08:00：资源测量必须分清整轮训练统计与固定批次模型副本探测。隔离代理损失可在不读标签或改权重文件时测forward/backward/Adam内存，lr=0仍会改变副本BN/优化器状态；报告应记录批次、测量窗口与OS页缓存未知状态，不能把PyTorch allocator峰值或校验+反序列化耗时冒充整轮训练峰值/裸盘带宽。新增诊断仅置于scripts，避免使运行中核心身份失效。Windows pytest默认Temp ACL失败时复用workspace专用basetemp/cache_dir，不改断言。

- 2026-11-02T03:46:18+08:00：共享GPU的独立训练可保留单任务RNG/配置/顺序，但训练墙钟含资源争用；全部训练子进程必须退出后再逐个运行部署基准。资源门控应绑定真实验收、config/core/graphs和报告SHA，并测最大原子数批次而不只测随机批次；峰值余量仍不是绝对保证。21天单波时限用于容纳退回1进程的最多4任务，不增加每任务优化预算。MemAvailable而非MemFree用于Linux可用内存规划；本节点前者约228.5GiB、后者约2.8GiB。重跑前先保存旧报告/执行账本，防止硬中断时把旧结果当作新完成结果。

- 2026-11-02T04:05:23+08:00：生成嵌套Python/SSH管理脚本时，内层r"..."无法阻止外层普通字符串把\b变成退格。管理脚本执行前需检查不可打印控制字符，并用ast及regex样例检查日志/依赖门控；本轮错误在任何hold/提交/取消之前被日志门控拦截。pending迁移按hold旧数组→提交带验收依赖的新数组→重接并核验汇总afterany→取消旧pending的顺序执行，durable ledger保留阶段和ID。依据[Slurm scontrol](https://slurm.schedmd.com/scontrol.html)和[数组依赖说明](https://slurm.schedmd.com/job_array.html)，数组ID的afterany覆盖所有元素，避免取消旧数组后汇总提前运行。

- 2026-11-02T04:31:51+08:00：已经被下游checkpoint绑定的基础cache manifest不可为补字段而就地改写；用补充manifest引用其SHA、再由根链引用补充SHA，既保留训练输入身份又提供完整交付字段。发布前应验证所有阶段、在任务锁内原子发布且避免时间戳破坏幂等。评测不能等遍历主链测试后才发现缺对照，应在公开入口预先检查所有对照。多任务长Slurm allocation需要每个晚启动CUDA子进程复核环境，单次job启动检查不足；错误检查必须在训练前停止并留下failure。

- 2026-11-02T05:57:29+08:00：Slurm数组别名与实际job ID不同，当前895_0对应897，状态查询/环境文件应同时保留两者，不能把ID不同当作错误任务。CUDA缓存/链检查使用atol+rtol组合：本次最大节点绝对误差4.5776e-5虽大于atol2e-5，仍满足结合期望值大小的rtol1e-4；不得仅比较全局最大绝对差判定失败或放松容差。固定批次显存测量可用于保守并发规划，但不能冒充整轮峰值。长监控在本地原子写latest并追加JSONL，避免随历史增长反复重写大文件；远端只读小型管理元数据。


- 2026-11-02T06:17:54+08:00：按组等待全部任务结束的调度会受组内最长任务限制；可用固定数据审计的有效标签数作粗略工作量代理，仅重排未启动组。调度文件必须覆盖所有任务恰好一次、保持组容量并绑定来源/配置/图/审计SHA；发布前检查每一份已有wave ledger，保护已启动成员。运行中父进程可能已加载旧代码，故保留既有组并让未来进程读取外部不可变分组，不修改训练核心身份。工作量代理改善不能等同实测速度。


- 2026-11-02T22:29:34+08:00：暂停已提交训练要区分agent goal paused与Slurm实际停训。先hold afterany汇总，再验证/备份checkpoint并通过Slurm停止，最后核对队列与原训练PID消失；不能把scancel返回0当作停止证明。本次Guqq Slurm21.08.5对数字897的scancel返回0后895_0仍RUNNING，改用精确数组别名scancel --verbose 895_0才确认CANCELLED/ExitCode0:15；这是本次集群观测，勿泛化为所有Slurm的行为。保留last的model/optimizer/RNG/history以及best/config，原子保存使完整epoch断点可用。恢复时需先把held893的afterany依赖改到新作业，再release；旧895取消后其依赖可能已满足。暂停元数据应保存已发生的wave墙钟，避免恢复账本漏算成本。

- 2026-11-02T23:37:27+08:00：残差实验采用独立src/residual_scaling以保留旧checkpoint/core身份。节点缓存必须与累计物理单位预测成对归档；归一化固定R0，残差累加不能再次加均值。每轮仅从训练后的checkpoint选择，禁止用eta=0历史回退伪造单调曲线。匹配direct实际优化步数隔离预算，墙钟和投影参数差另行报告。

- 2026-11-03T09:48:56+08:00：纠错诊断必须同时检查方向和幅度：Pearson=1也可能因过量修正而全部样本变差；报告MSE cross term与delta²代价、改善人数和MAE贡献。历史train loss是参数/BN随batch变化的online MSE，不能与val MAE直接作泛化差距；最佳checkpoint缓存提供同eval口径的train/val MAE/RMSE。新增诊断包放到独立src/recursive_diagnostics，避免改变已完成训练实现hash。

- 2026-11-03T10:46:55+08:00：iComformer官方默认原生参数4966497；当前源包含comforemr import和MatformerConv父类名拼写错误，采用完整源SHA审计＋选择原始声明执行，只修复一个父类AST名称，不改数学。旧pydantic/eComformer依赖不应绑到不变分支。Jarvis Atoms.from_dict对缺props严格报错，使用同坐标/晶胞/元素的显式构造及props可选值保持数据兼容。本地未使用的PyG spline旧DLL可产生被捕获的Windows异常横幅，不能据此跳过实际使用的原生forward/grad/几何验收；服务器须另验ABI。

- 2026-11-03T11:18:36+08:00：资源curl在下载进度100%后也可能因TLS收尾unexpected EOF返回56。必须核对精确字节数和官方SHA；完整且匹配的partial可直接原子发布，不因传输收尾状态重复下载，也不因curl0就跳过文件校验。不匹配仍失败并保留断点，不能用放松TLS或校验规避。已用完整/损坏两类单测验证此路径。

- 2026-11-03T11:23:49+08:00：iComformer环境准备第三次阻塞后已复查已有网络经验：反向SOCKS长传输可在TLS收尾或中途断线。Jarvis大wheel已完整校验；剩余小wheel优先复用tmp/wheelhouse/cgcnn-inherited-bootstrap的相同SHA版本，并SFTP到新任务资源目录。未因网络失败放松哈希、不重新下载已完成资源、不改共享环境。

- 2026-11-03T12:49:15+08:00：CGCNNStage.encode_nodes在递归分支会对输入特征detach，这是缓存训练的正确边界，但直接串联该接口会静默截断端到端梯度。joint_cgcnn明确复用native embedding/convs与projection实现可微桥接，并用全部参数梯度及首段非零梯度测试守护；第一段无用readout不注册，避免参数虚增或无梯度参数。架构说明见src/joint_cgcnn/model/README.md。
