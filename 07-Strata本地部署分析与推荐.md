# Strata / PolyStrata 本地部署分析与推荐

## 一、先厘清：两个项目，别搞混
- **Niko1221/Strata**：底层推理引擎（C++ / HIP / Vulkan），MoE 专家卸载。最新 v0.2.21（2026-11-24）。
- **vecszn/polystrata → simplexai-labs/PolyStrata**：建立在 Strata 之上的产品化封装（MIT），一键安装、本地 OpenAI/Anthropic API。最新 v0.2.20-poly.4-hotfix（2026-11-24），有 Windows x64 安装包。
- 关系：Linger 桌面版把 PolyStrata 当本地引擎；PolyStrata 又是 Strata 引擎的封装。三者都在昨天/今天更新，非常活跃。

## 二、你的硬件恰好是 PolyStrata 的「主场机型」
- 实测确认：Ryzen AI Max+ 395 + Radeon 8060S（gfx1151, RDNA 3.5）+ 128GB 统一内存、AVX-512。
- 官方专门为这个平台写了 STRIX_HALO.md 和 STRIX_HALO_WINDOWS.md；Windows 用现成 `rdna3` HIP 包（内含 gfx1151）。
- 状态标注：**experimental（实验性）**——能装、有实测，但不是稳定主线。

## 三、收益对比（关键，反直觉）

| 指标 | 本机现状 llama.cpp + qwen3-35b-a3b | PolyStrata + Qwen3.8-Flash-Next IQ3_S（同款机 Windows 实测） | 差异 |
|---|---|---|---|
| Decode 生成速度 | **67 tok/s** | 44 tok/s（40.6–59.5，代码类更快） | ❌ llama.cpp 更快 |
| Prefill 读提示词 | 未单独测 | **755–821 tok/s**（4K–32K） | ✅ PolyStrata 极强 |
| 首 token 延迟 | 未测 | 0.6 s（短聊）/ 4.5 s（6轮编码会话） | 良好 |
| 模型规模/质量 | 35B A3B | **新一代更强 MoE**（Qwen3.8-Flash-Next） | ✅ 模型更新 |
| 上下文 | 64K | 131K（int8 KV） | ✅ 翻倍 |
| 部署方式 | 已在跑，零成本 | 需装包+BIOS 固定 64GB carve-out | ❌ 有成本 |

**反直觉结论**：PolyStrata 的卖点不是「生成更快」——本机 llama.cpp 的 67 tok/s 已经超过它的 44 tok/s。
它的真正优势是 **prefill 极快（755–821 tok/s）+ 能在消费级硬件上跑更大的新一代 MoE 模型 + 131K 上下文**。

## 四、这恰好命中你的工作流
你的省钱流水线里，本地模型干的活是：**前处理、摘要、分类、生成简报**——这些任务的特征是：
- 输入长（原始材料动辄上千 token）→ prefill 快 = 直接受益（PolyStrata 755–821 vs llama.cpp 未测但远低于此）
- 输出短（简报只有几百 token）→ decode 慢一点影响很小（44 tok/s 生成 300 token 也只要 ~7 秒）
- 批量/并发 → PolyStrata 的专家缓存常驻（IQ3_S 全部 24K 专家进内存）适合反复调用

换句话说：**你不需要它跑得快，你需要它「读得快」——而 PolyStrata 正是读得极快。**

## 五、部署哪个收益最大：明确推荐

**推荐：部署 PolyStrata + Qwen3.8-Flash-Next IQ3_S，作为「长文本前处理专机」，与现有 llama.cpp 并存。**

理由（收益排序）：
1. **同款机型 Windows 实测数据现成**（44 tok/s + 755–821 prefill），不是纸上推测，风险可控。
2. **IQ3_S 是官方在 Strix Halo Windows 上唯一实测过的档位**——照抄配置成功率最高；进程占 ~49GB，128G 机器余量充足。
3. **与你的省钱流水线精确互补**：它负责「读长文出简报」（prefill 强），llama.cpp 负责「快速短答」（decode 强），各取所长。
4. **本地 API 兼容**：PolyStrata 提供本地 OpenAI/Anthropic API，可直接替换 auto_route.py 里的 LOCAL_URL，无需改架构。
5. **模型更新**：Qwen3.8-Flash-Next 比当前 qwen3-35b 新一代，前处理质量有提升空间。

**不推荐**：
- UD-Q4_K_XL / 125B 大模型：要 72GB+ 内存、预填更慢，对「出简报」场景收益递减。
- 替换掉 llama.cpp：它的 decode 更快，短答/对话场景更合适，删了是损失。
- 现在装在产线主环境：experimental 状态 + 需要 BIOS 改 carve-out，先在测试会话验证。

## 六、部署前置条件与风险
- **BIOS 固定 64GB carve-out 给显卡**（实测机这么做）——这是唯一硬件改动，需重启进 BIOS，属不可逆配置，需你确认。
- 关闭 WSL（AMD 引擎在 WSL 会挂）。
- 装 AMD Adrenalin 驱动（已有 32.0.32029，满足）。
- 下载量约 70–120GB（模型 pack + experts），磁盘空间要够。
- experimental 状态：可能遇到 bug；先只读验证、不做产线关键路径。
- 与现有 llama.cpp 共存的端口/内存冲突：两者都吃 128G 统一内存，别同时满载。

## 七、落地步骤（若采纳）
1. 确认 BIOS carve-out 方案（64GB 显卡 / 64GB 系统）。
2. 下载 strata-poly-windows-x64 ZIP + 跑 START-HERE.bat setup（自动选 rdna3 HIP 包）。
3. `strata launch --family qwen --model iq3_s` 起服务，跑官方 strata_bench.py 复现实测数字。
4. 把 auto_route.py 的 LOCAL_URL/LOCAL_MODEL 指向 PolyStrata 本地 API，A/B 对比前处理质量与速度。
5. 验证稳定后再决定是否让它承担日常简报生成。

## 八、一句话结论
部署 PolyStrata + Qwen3.8-Flash-Next IQ3_S 作为长文前处理专机，与 llama.cpp 并存互补——
因为你的活是「读长文出短文」，而它读得极快（821 tok/s）、生成够用（44 tok/s）、同款机已有实测、模型更新；
代价是一次 BIOS carve-out 和 experimental 风险，建议测试会话先验证。

## 数据来源（均为一手/官方）
- GitHub releases：vecszn/polystrata v0.2.20-poly.4-hotfix；Niko1221/Strata v0.2.21（2026-11-24/25）
- docs/STRIX_HALO_WINDOWS.md：0.2.7 + Qwen3.8-Flash-Next IQ3_S 在 Ryzen AI Max+ 395 / 128GB / Windows 11 实测
- docs/STRIX_HALO.md、docs/AMD_HIP.md：gfx1151 Windows 支持与 HIP 包
- 本机实测：GPU=Radeon 8060S gfx1151、RAM=63.6G可见、llama.cpp qwen3-35b-a3b 67 tok/s