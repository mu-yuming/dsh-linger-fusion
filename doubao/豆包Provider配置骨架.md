# 豆包 Provider 配置骨架（待 ARK_API_KEY 启用）

## 状态
本机 ~/.dsh/.env 无 ARK_API_KEY，故**未实际注册**。以下为经官方文档核实的配置，填入 key 后即可启用。

## 参数（火山方舟 OpenAI 兼容端点）
- baseURL: https://ark.cn-beijing.volces.com/api/v3
- apiKeyEnv: ARK_API_KEY
- api: openai-completions
- model（轻量协同定位）: doubao-seed-2-1-lite-260915
- 备选: doubao-seed-2-0-lite-260215（更省）、doubao-seed-2-1-pro-260915（更强）

## 启用步骤（用户提供 key 后）
1. 在 ~/.dsh/.env 追加：`ARK_API_KEY=<火山方舟API Key>`（勿提交到仓库）
2. 在 cordis.patch.yml 的 llm-pi-ai providers 增加 doubao 条目（YAML 片段见下）
3. 在 subagent-model-selection.allowedModels 增加 `{provider: doubao, model: doubao-seed-2-1-lite-260915}`
4. 验证：`list_subagent_models({provider:'doubao'})` 应返回该路由；再跑一句问答确认连通

## provider YAML 片段（插入到 providers: 区块内）
```yaml
      doubao:
        displayName: 豆包 Doubao (火山方舟)
        apiKeyEnv: ARK_API_KEY
        api: openai-completions
        baseURL: https://ark.cn-beijing.volces.com/api/v3
        models:
          - id: doubao-seed-2-1-lite-260915
            name: Doubao Seed 2.1 Lite · 轻量协同
            contextWindow: 262144
            maxTokens: 32768
            input: [text]
```

## 与「三集群 + Room 协同」的定位
豆包作为 provider 路由注册后，可被三集群（Hermes/Codex/DeepSeek Harness）的任一 Agent 在 subagent 白名单内选用，
承担轻量协同角色（快速摘要、分类、初筛）。真正的 Room 协同由 team.md 式的任务编排实现（借鉴 Linger），不依赖豆包本身。

## 安全提示
- ARK_API_KEY 为敏感凭据，只写入本地 .env，绝不进入 GitHub 仓库或对话记录
- 火山方舟按 token 计费，轻量协同需设调用频次上限