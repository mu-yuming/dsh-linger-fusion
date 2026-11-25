# 豆包 Provider —— 已注册并验证

## 状态：✅ 已完成（本次会话实测）
- ARK_API_KEY 已写入本地 ~/.dsh/.env（**密钥不进入仓库，仅本地保存**）
- 豆包 provider 已加入 cordis.patch.yml，并进入 subagent-model-selection 白名单
- 端到端验证：subagent 显式 pin `doubao / doubao-seed-2-1-turbo-260628` 实跑成功（返回「收到」）
- 首次派发曾临时失败一次，重试成功；判断为瞬时故障，非适配问题

## 模型可用性实测（账号 2100683002，key 有效）
| 模型 ID | 状态 |
|---|---|
| doubao-seed-2-1-turbo-260628 | ✅ 可用（已选为协同路由，成本友好） |
| doubao-seed-2-0-pro-260215 | ✅ 可用（备选） |
| doubao-seed-2-1-pro-260915 | ❌ 达账号用量上限 |
| doubao-seed-2-1-lite-260915 | ❌ 账号未开通该模型 |
| doubao-seed-evolving | ❌ 账号未开通 |

## 配置参数
- baseURL: https://ark.cn-beijing.volces.com/api/v3
- apiKeyEnv: ARK_API_KEY（本地 .env）
- api: openai-completions
- model: doubao-seed-2-1-turbo-260628（轻量协同定位）
- 能力核实：支持 tool call（实测返回 finish_reason=tool_calls），可作为 subagent 使用

## 回滚
- 停用：`~/.dsh/profiles/desktop/cordis.patch.yml.bak-doubao-20261125-172050` 覆盖回原文件；.env 备份为 `.env.bak-doubao-20261125-172050`
- 或仅从白名单移除 doubao 条目即可停止 subagent 调度

## 安全提示
- ARK_API_KEY 为敏感凭据，只存在于本地 .env，不提交仓库、不进入文档
- 火山方舟按 token 计费，轻量协同需设调用频次上限
- tool call 实测响应含 reasoning_content / encrypted_content 字段，属豆包特性，DSH 已兼容（subagent 实跑通过）