# 经验教训

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
