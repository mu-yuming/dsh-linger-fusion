---
name: local-first-routing
description: "用本地大模型先压缩长材料再派发在线模型，节省在线 token。当用户给出长日志/文档/报告需要分析总结，或明确提到省 token、省钱、本地优先时使用。"
---

# 本地优先省钱流水线

把长任务交给本地免费模型先压缩，再派给在线模型只做核心判断，降低在线 token 消耗。

## 何时使用
- 用户给了一段长材料（日志/文档/报告/对话记录），要求分析、总结、诊断、处置建议
- 用户明确提到省 token / 省钱 / 本地优先
- 任务材料预计超过 1500 token 时收益显著

## 关键规则：1500 token 阈值（实测得出，必须遵守）

| 原文规模 | 节省率 | 做法 |
|---|---|---|
| < 1500 token | -3% ~ -14%（亏） | **跳过简报，直接派发** |
| 1500–3000 token | +30% ~ +45% | 可选简报 |
| > 3000 token | +78% ~ +89% | **必须简报** |

原因：简报输出稳定在约 1100 token（不随原文增长），原文短时简报开销反而超过原文。
auto_route.py 已内置该阈值判断，低于 1500 会自动跳过。

## 三条可执行命令

所有脚本位于 `C:\AI\github-sync\routing-pipeline\`，Python 用 `D:\hermes\tools\python-3.14.9+20261021-win32-x64\python.exe`。

### 1. 端到端自动路由（最常用）
```
python C:/AI/github-sync/routing-pipeline/auto_route.py <任务文件>
```
流程：本地判断长度 → (够长才做简报) → 解析【建议派发】→ 自动选模型 → 输出结果 + 节省报告。

### 2. 纯本地前处理（只想压缩、不派发）
```
python C:/AI/github-sync/routing-pipeline/pipeline.py prepare <文件>
```
输出结构化简报（背景/目标/关键数据/建议派发），存为 .brief.md。

### 3. 豆包轻量协同（摘要/分类，便宜）
```
python C:/AI/github-sync/doubao/doubao_assist.py summarize <文件或文本>
python C:/AI/github-sync/doubao/doubao_assist.py classify <文件或文本>
```

### 4. 工作小组（调度bot + 专家bot，带群规）
```
python C:/AI/github-sync/workgroup/workgroup.py <任务文件> <auto|local|doubao|expert|codex>
```

## 模型角色与成本

| 角色 | 端点 | 成本 | 用途 |
|---|---|---|---|
| 本地 Qwen3 35B | llama.cpp @127.0.0.1:11434 | 免费 | 简报、初筛、汇总 |
| 免费强模型 | magpie 网关 @127.0.0.1:3425，`opencode-zen-free/hy4-flash-free` | 免费 | 深度推理（需 reasoning_effort=none 才输出干净） |
| 豆包 | 火山方舟 API，`doubao-seed-2-1-turbo-260628` | 低 | 摘要/分类（需 thinking disabled） |
| Codex | `~/.codex/config.toml` 已配 deepseek-flash | 低 | 编码（CLI 未入 PATH） |

## 前置条件（缺失会失败）
- llama.cpp 在 127.0.0.1:11434 运行（`curl 127.0.0.1:11434/v1/models` 应返回模型列表）
- magpie 网关在 127.0.0.1:3425 运行
- `~/.dsh/.env` 含 `MAGPIE_GATEWAY_KEY`、`ARK_API_KEY`（脚本从该文件读取，勿硬编码）

## 已知坑（踩过的）
1. **不要无条件做简报**——短材料会亏（见阈值规则）。
2. **magpie 网关偶发 502**——脚本已有 3 次退避重试，若仍失败重跑一次即可。
3. **部分网关模型把 token 全花在 reasoning上导致 content 为空**——必须传 `reasoning_effort: none`。
4. **豆包需 `thinking: {type: disabled}`** 才快且省。
5. **Windows 中文乱码**——脚本已 `sys.stdout.reconfigure(encoding='utf-8')`，自己写脚本时记得加。
6. **别让豆包做 subagent**——实测 6 次派发 5 次完成失败（reasoning_content 字段与 DSH 不兼容），只走 API 直连。

## 质量保障
实测证明简报不损质量（细节/数字/因果三类任务均不输原文直给），前提是简报模板强制保留【关键数据】段。
复杂或高风险场景，建议人工复核本地生成的简报。

## 详细文档
`C:\AI\github-sync\09-AB质量验证与成本阈值.md`（阈值实测数据）
`C:\AI\github-sync\04-分层任务路由省钱方案.md`（完整方案）
