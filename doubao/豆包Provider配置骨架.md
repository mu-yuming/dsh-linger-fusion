# 豆包 Provider —— 已注册，API 可用；subagent 完成率异常

## 状态（诚实版，纠正先前误判）
- ✅ ARK_API_KEY 已写入本地 ~/.dsh/.env（已轮换为新 key，长度 46，**不进仓库**）
- ✅ 豆包 provider 已注册并进入 subagent 白名单；`list_subagent_models({provider:'doubao'})` 显示 provider 存在（模型目录快照滞后，显示 no advertised models，但显式 pin 可用）
- ✅ 火山方舟 API 层稳定可用：新 key 直连 chat/completions 实测返回「收到」，tool call 也实测支持
- ⚠️ **DSH subagent 层不稳定**：显式 pin `doubao/doubao-seed-2-1-turbo-260628` 派发 6 次，activation 均成功，但完成阶段失败 5 次（仅 1 次早期成功）。继承路由（实际走 workbuddy）返回「收到」不能算豆包验证。

## 关键教训
曾把「继承路由 subagent 返回收到」误记为豆包端到端成功——错误，已纠正。
provider 注册成功 ≠ subagent 可稳定调度；二者要分开验证，且不能把继承路由结果当被 pin provider 的结果。

## 失败原因推断（未证实，日志无内部错误可查）
豆包响应含 `reasoning_content` / `encrypted_content` 等非标准字段，可能与 DSH subagent 完成处理不兼容；
表现为 activation 成功、模型侧 API 正常，但 subagent 完成通知丢失。需 DSH 侧适配或换用行为更标准的模型验证。

## 当前可用状态
- 豆包 API 直连：✅ 可用于轻量协同脚本/工具（不经 DSH subagent）
- 豆包作为 subagent 路由：⚠️ 不稳定，生产使用前需进一步适配
- 三集群日常协同：不受影响（workbuddy / local-llama 双路稳定）

## 模型可用性实测（账号 2100683002，新 key 有效）
| 模型 ID | 状态 |
|---|---|
| doubao-seed-2-1-turbo-260628 | ✅ API 可用（当前配置） |
| doubao-seed-2-0-pro-260215 | ✅ API 可用（备选，可尝试改善 subagent 兼容性） |
| doubao-seed-2-1-pro-260915 | ❌ 达用量上限 |
| doubao-seed-2-1-lite-260915 / evolving | ❌ 未开通 |

## 回滚
- cordis.patch.yml.bak-doubao-20261125-172050 覆盖回原文件；.env.bak-doubao-20261125-172050 为旧 env 备份
- 或从白名单移除 doubao 条目即可停止调度

## 安全
- key 仅存本地 .env，不提交仓库；已轮换一次（旧 key 作废）
- 火山方舟按 token 计费，设调用频次上限