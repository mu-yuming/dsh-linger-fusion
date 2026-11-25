# 豆包轻量协同 —— 最终定位：API 直连（非 subagent）

## 最终决策与理由
豆包从 DSH subagent 白名单移除，**保留 provider 配置**，改走 API 直连轻量协同。
理由：显式 pin 豆包的 subagent 6 次派发完成阶段失败 5 次（响应含 reasoning_content/encrypted_content，与 DSH 完成处理不兼容）；
而 API 直连稳定可用。利益最大化=让豆包做它擅长的廉价杂活（摘要/分类/初筛），不挤占主力协同链路。

## 状态
- ✅ ARK_API_KEY 已轮换并写入本地 ~/.dsh/.env（不进仓库）
- ✅ provider 块保留在 cordis.patch.yml（随时可恢复 subagent 路由：`bak-rmdoubao-` 备份可回滚）
- ✅ subagent 白名单已移除 doubao，三集群回归纯净（workbuddy + local-llama 双路稳定）
- ✅ API 直连协同脚本已落地并实测通过

## 轻量协同脚本：doubao_assist.py
用途：对产线文本（报警日志/工艺记录/文档）做摘要与分类初筛，作为异构双路之外的低成本杂活工具。

用法（key 从 ~/.dsh/.env 自动读取，不硬编码）：
```bash
python doubao_assist.py summarize <文本或文件路径>   # 压缩成3条要点
python doubao_assist.py classify   <文本或文件路径>   # 分类：报警处置/工艺参数/设备故障/其他
```

关键实现：
- 模型 doubao-seed-2-1-turbo-260628
- `thinking: {type: disabled}` 关闭深度思考——轻量协同要快且省
- 超时 120s + 清晰错误处理；stdout 强制 UTF-8（Windows 中文不乱码）

实测结果（对 crosscheck-poc/snapshot.md）：
- summarize → 1号炉温848→803℃触发报警8分钟恢复 / 主因炉门异常开启+装料偏多功率饱和 / 建议规范炉门管控调整装料量
- classify → 报警处置（理由：1号炉低温报警记录，含炉门异常与装料偏多，处置方向明确）

## 模型可用性（账号 2100683002）
| 模型 | 状态 |
|---|---|
| doubao-seed-2-1-turbo-260628 | ✅ 当前使用，API 稳定 |
| doubao-seed-2-0-pro-260215 | ✅ 备选 |
| lite-260915 / pro-260915 / evolving | ❌ 未开通 / 达上限 |

## 恢复为 subagent 路由（如需，待 DSH 适配后）
把 `      - provider: doubao / model: doubao-seed-2-1-turbo-260628` 加回 subagent-model-selection.allowedModels 即可；
provider 块已在配置中，无需重建。建议先换 seed-2-0-pro 试兼容性。

## 回滚与安全
- 配置回滚：cordis.patch.yml.bak-rmdoubao-20261125-173527（移除白名单前）、.bak-doubao-20261125-172050（注册前）
- key 仅存本地 .env，不提交仓库；已轮换一次
- 按 token 计费，脚本单次调用 max_tokens=512 + 关思考，成本可控