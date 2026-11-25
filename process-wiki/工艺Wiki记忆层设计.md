# 工艺 Wiki 记忆层设计（DSH 真实能力版）

## 0. 实测：DSH 记忆到底是什么（本节基于工具实查，非推断）

本会话 magpie-memory 版本 0.1.4738，实测能力：
- **7 种条目类型**：profile / preference / rule / reference / fact / procedure / episode
- **3 种作用域**：project（某项目）/ global（全局继承）/ agent（单 agent）
- **每条含**：正文、tags、why（为何成立/来源）、时间戳、可搜索、可 forget
- **现有内容**：3 条，全是 reference/fact 级小条目（GitHub 仓库位置、CLI 安装路径、TTY 限制事实）
- **当前可用的 scope 只有 global**：agent scope 因客户端未命名不可用；project scope 因当前目录未注册为项目不可用

关键判断：DSH 记忆是「小条目 + 标签 + 溯源」结构，
**不是** Linger Wiki 那种「有来源的长页面 + 后台分阶段自动整理」，更不是时序库。
所以 Linger Wiki **不能原样搬**，但它的思路可以用 DSH 现有结构近似实现。

## 1. 三层记忆映射（产线工艺数据的正确分层）

| 数据层次 | 例子 | 存哪里 | 理由 |
|---|---|---|---|
| L1 原始数据 | 报警日志、PV/SV 时序、设备状态流 | **时序库/日志文件**（DSH 记忆之外） | 高频、带时间戳、量大；magpie 小条目装不下也不该装 |
| L2 处置经验 | "1号炉低温多为炉门异常+装料偏多，先查联锁" | **magpie-memory**（procedure/episode + tags） | 归纳后的结论，可搜索、可迁移、带 why 溯源 |
| L3 工作上下文 | 当前正在分析的报警、本轮裁决结论 | **fact_register**（working context，≤12条） | 短期锚定，跨步引用，会话级 |
| L0 项目约定 | "产线端只读、写入需人工审批" | **AGENTS.md**（项目指令文件） | 稳定规则，属于项目而非记忆 |

这张表就是"工艺 Wiki"在 DSH 里的真实形态：它不是一个新系统，
而是把 L2 这一层用 magpie-memory 认真组织起来。

## 2. 用 magpie-memory 近似 Linger Wiki 的四个特性

Linger Wiki 特性 → DSH 对应做法：
1. **自动分类沉淀** → 用 tags 体系：`#工艺/加热炉` `#报警/低温` `#设备/1号炉` `#处置/已验证`
2. **带来源的页面** → 每条 memory 的 `why` 字段写清来源（哪次报警、哪次交叉校验裁决）
3. **所有 Agent 可搜** → global scope + memory_search 按 tag/query 检索（当前只有 global 可用）
4. **可迁移** → memory 是服务端持有、可搜索的结构化条目；迁移方式需用 magpie 的导出/备份机制（待查，见边界）

差异（必须承认）：DSH 没有 Linger 那种"后台 Dreaming 自动整理成页面"，
沉淀需要**人工或 Agent 主动触发** memory_save，不是全自动。

## 3. 与交叉校验 PoC 的串接（核心链路）

这正是前面三块拼图的意义所在：

```
OT 网关只读遥测(L1 时序) 
   ↓ 固化为快照
双路 subagent 交叉校验(PoC已验证) 
   ↓ 主 Agent 裁决 verdict.md
人工审核确认 
   ↓ memory_save(kind=procedure/episode, tags, why=来源)
L2 工艺 Wiki(magpie-memory) 
   ↓ memory_search 检索
下次同类报警 → 作为先验知识喂给双路分析
```

闭环价值：每处理一次报警，工艺 Wiki 增长一条带来源的经验；
下次同类报警时，这条经验作为上下文进入交叉校验，形成"越用越准"的积累。
这是 Linger Wiki "从对话/文件提取事实→沉淀→可搜" 思路在 DSH 上的落地形态。

## 4. 落地设计：条目模板

一条合格的经验条目长这样：
- kind: procedure（处置方法）或 episode（一次事件）
- scope: global（当前唯一可用；产线项目注册后可改 project 隔离）
- text: "1号炉低温报警（PV跌破820）先查炉门联锁与装料量；炉门异常开窗是高频主因"
- tags: [工艺, 加热炉, 低温报警, 炉门, 已验证]
- why: "2026-xx-xx 双路交叉校验裁决一致(置信度88%/85%)，来源 crosscheck-poc/verdict.md"

## 5. 前置问题（决定能否做产线隔离）
project scope 目前不可用——memory_context 显示当前目录未注册为项目。
若要把产线工艺知识隔离在产线 Workspace（而非 global 全共享），需先：
- 让 magpie 识别产线目录为 project（在产线目录运行 magpie mcp memory，或用 project 参数传目录/键）；
- 之后 memory_save(memory_context) 即可 scope=project。
这一步需本地环境配合，本会话无法代做（无 shell 绑定、当前目录未注册）。

## 6. 诚实标注的边界
- magpie-memory 是本机 magpie 插件提供的服务，非 DSH 核心内置；换环境需确认该插件随行
- 迁移/备份机制未实测（memory_context 只说服务端持有，导出方式待查）
- 无自动生成：沉淀依赖人工或 Agent 主动 memory_save，不是 Linger 式的后台自动整理
- 当前只能 global scope，产线数据隔离需先解决 project 注册
- 本方案是设计文档，未写入任何真实产线经验条目（避免污染记忆库）

## 7. 下一步可选
1. 写一条示例经验条目到 global memory 验证检索链路（会真实写入记忆库，需你同意）
2. 查 magpie memory 的导出/备份方式，补上"可迁移"这一环
3. 解决 project scope 注册，实现产线数据隔离