# 社区 Bot 群聊插件评估报告

## 结论：暂不安装，先用原生原语方案；观察名单里 @nanmicoder/dsh-agent-teams 最优
理由：五个候选全是单人维护的第三方包，无 repository 登记、下载量数据缺失（新/小众），
供应链风险实打实；而原生方案（workgroup.py + subagent/task_board）已能覆盖 80% 需求且零风险。
若将来确需真实群聊 UI，优先评估 @nanmicoder/dsh-agent-teams（零依赖、DSH 版本兼容宽）。

## 候选插件一手元数据（npm registry，2026-11-25 实测）
| 包名 | 版本 | 发布 | 维护者 | engines.dsh | 依赖 | 本机兼容(0.2.3-alpha.2) |
|---|---|---|---|---|---|---|
| dsh-botgroup | 0.7.4 | 11-24 | mj-cjm(单人) | >=0.2.1-rc.2 <0.3.0 | zod/js-yaml/MCP server-memory 等 | 是 |
| dsh-bot-team | 1.3.0 | 10-28 | shper87(单人) | ^0.2.1-rc.3 | semver/fontkit | 是 |
| @nanmicoder/dsh-agent-teams | 0.1.31 | 11-18 | relakkes(单人) | >=0.1.2-alpha.2 | **无依赖** | 是 |
| roundtable-bots | 0.4.6 | 11-17 | lonelycrab888(单人) | >=0.2.2-rc.2 | zod/mammoth/pdfjs-dist | 是 |
| mino-bot | 0.1.2 | 11-06 | wuyangji(单人) | >=0.2.1-rc.2 <0.3.0 | zod/js-yaml/MCP server-memory | 是 |
| huxint/dsh-team (GitHub) | - | 更新10-26 | 个人 | - | - | MIT / 14 stars |

## 评估维度与评分（1-5，5最好）
| 维度 | dsh-botgroup | dsh-bot-team | nanmicoder | roundtable | mino-bot |
|---|---|---|---|---|---|
| 可审计性(有repo) | 1 | 1 | 2 | 1 | 1 |
| 依赖清洁度 | 2 | 4 | 5 | 3 | 2 |
| 版本兼容 | 5 | 5 | 5 | 5 | 5 |
| 近期活跃 | 5 | 3 | 4 | 4 | 3 |
| 省钱契合(可配模型/@唤醒) | 4 | 4 | 4 | 3 | 3 |
| 供应链安全 | 1 | 2 | 3 | 2 | 1 |
| **综合** | **18** | **19** | **23** | **18** | **15** |

## 关键风险
1. 全部单人维护、无 repository 字段、下载量 API 无数据 → 出问题无社区兜底、无法审计源码。
2. dsh-botgroup / mino-bot 引入 @modelcontextprotocol/server-memory，会给工作区加一个常驻 MCP server（额外权限面）。
3. bot 群成员若默认各自带完整工具集（这些插件的共同设计），与「省 token」冲突——成员会把工具 schema 反复塞进上下文。
4. 群聊记忆随轮次膨胀，长期看必然推高 token，与本项目核心目标对冲。

## 契合度分析
- 契合：这些插件的 bot 都能各自配模型/人格，@mention 派发 → 与四方角色分工、按需唤醒付费模型一致。
- 不契合：真实群聊 UI 鼓励多人自由讨论、上下文滚雪球；我们的省钱路线要求简报先行+@才发言+单轮。
- 结论：能力上契合，使用方式上冲突。若装，必须配套群规，且给每个 bot 配免费模型。

## 推荐路径
1. **现在**：不装。继续用 workgroup.py 原生方案（零依赖、已实测省76%）。
2. **观察**：若坚持要真实群聊 UI，再评估 @nanmicoder/dsh-agent-teams（零依赖最佳），安装前先用 npm pack 解包审计源码、在隔离 profile 试装。
3. **永不**：不在产线/工作主 profile 直接装这类插件；第三方的凭据编解码工具（mino-bot 描述里提到）尤其要隔离。

## 与已有原生方案对照
| 能力 | 原生 workgroup.py | 社区 bot 群插件 |
|---|---|---|
| 群聊 UI / 持久 bot | 无（脚本式） | 有 |
| @mention 派发 | 由参数模拟 | 真实 |
| 供应链风险 | 零 | 中高 |
| 省钱可控性 | 高（群规写死） | 中（需自行约束） |
| 已实测 | 是（省76%） | 否 |