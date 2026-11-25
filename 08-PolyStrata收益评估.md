# PolyStrata 部署收益评估（基于本机实测）

## 一、结论先行：收益为负，不建议部署

上一轮我推荐部署 PolyStrata 作「长文前处理专机」，理由是「它 prefill 极快（755–821 tok/s），而本地前处理正需要读得快」。
**本轮实测推翻了那个前提**：本机 llama.cpp 的 prefill 实测 892–958 tok/s，**比 PolyStrata 官方 Windows 实测更快**。
在速度这一维度上，PolyStrata 对这台机器没有收益，反而是净损失。

## 二、同尺度实测对比（关键证据）

本机 llama.cpp + qwen3-35b-a3b（Radeon 8060S gfx1151，128G 统一内存，BIOS 已划 64G）：
| 场景 | 实测 prefill | 实测 decode |
|---|---|---|
| 852 token 简报级 | 932 tok/s | 59.8 tok/s |
| 3,036 token（~4K） | **958.3 tok/s** | - |
| 10,596 token（~16K） | **892.3 tok/s** | - |

PolyStrata 官方 STRIX_HALO_WINDOWS.md 同一机型（Ryzen AI Max+ 395 / 128G / Windows 11）实测：
| 场景 | 官方实测 prefill | 官方实测 decode |
|---|---|---|
| 4K prompt | 755 tok/s | 44.0 tok/s（短聊） |
| 16K prompt | 821 tok/s | 47 tok/s（编码会话） |
| 32K prompt | 792 tok/s | - |

**逐项对比结论**：
- prefill：本机 892–958 > PolyStrata 755–821（本机快约 10–27%）
- decode：本机 59.8 > PolyStrata 44–47（本机快约 27–36%）
- 首 token：本机 852 token 1.22s 出结果；PolyStrata 短聊 0.60s、16K 需 19.6s——量级相当

## 三、逐项收益盘点

| 维度 | PolyStrata 相对本机 | 收益判断 |
|---|---|---|
| Prefill 速度 | 更慢（755–821 vs 892–958） | ❌ 负收益 |
| Decode 速度 | 更慢（44–47 vs 59.8） | ❌ 负收益 |
| 上下文长度 | 131K vs 64K | ✅ 唯一实收益 |
| 模型质量 | Qwen3.8-Flash-Next（新一代）vs qwen3-35b | ⚠️ 未实测，不敢断言 |
| 本地 API | OpenAI/Anthropic 兼容 | ➖ 本机 llama.cpp 也是 OpenAI 兼容，无增量 |
| 部署成本 | 70–120GB 下载 + experimental 软件 | ❌ 纯成本 |
| 稳定性 | 官方标注 experimental | ❌ 风险 |
| 运维复杂度 | 多一套引擎、多一个端口、内存争抢 | ❌ 负收益 |

## 四、唯一可能的收益点：上下文与模型

1. **131K 上下文 vs 64K**：如果你确实需要一次性吞下超过 64K 的产线文档/长日志，这才是 PolyStrata 的唯一硬优势。
   但注意：你的省钱流水线设计本来就是「先压缩成简报」，简报通常几百到几千 token——64K 完全够用。
2. **Qwen3.8-Flash-Next 质量**：模型确实更新，但**没有任何实测证明它对「产线报警分析/简报生成」比当前 qwen3-35b 更好**。
   若要评估质量收益，正确做法是先换模型（llama.cpp 也能跑其它 GGUF 模型），而不是换引擎。

## 五、成本核算（部署要付出的）

| 成本项 | 量级 |
|---|---|
| 模型下载 | 70–120 GB（当前网络下载 443MB 的 Linger 都很慢，120GB 不现实） |
| 磁盘占用 | 70–120 GB |
| 内存占用 | 进程约 49GB（IQ3_S），与 llama.cpp 争抢统一内存 |
| 稳定性风险 | experimental，可能与现有工作流冲突 |
| 时间成本 | 安装 + 调试 + A/B 验证，至少数小时到一天 |
| 维护成本 | 多一套引擎要跟版本、多一个端口要管 |

对比之下，收益：速度更慢、上下文多 67K（但用不上）、模型质量未验证。**投入产出比明显为负。**

## 六、修正后的推荐

**不建议部署 PolyStrata。继续用当前 llama.cpp + qwen3-35b-a3b。**

如果未来出现以下任一情况，再重新评估：
1. 你确实需要处理超过 64K 的单份文档（那时 131K 才有意义）。
2. 出现实测证明 Qwen3.8-Flash-Next 在产线任务上显著优于当前模型（此时优先在 llama.cpp 里换模型，不必换引擎）。
3. PolyStrata 脱离 experimental、且官方实测速度追上或超过 llama.cpp。

## 七、这次评估本身的教训

上一轮推荐基于「PolyStrata prefill 755–821 很快」这一条官方数据，误以为本机 llama.cpp 的 prefill 更慢——
**因为当时没有实测本机 prefill**。实测后发现本机更快，整个推荐的前提就不成立了。
教训：跨方案对比必须同尺度实测双方，不能拿一方的官方数据对比另一方的未测项。

## 数据来源
- 本机实测（2026-11-25）：llama.cpp @127.0.0.1:11434，qwen3-35b-a3b，通过 /v1/chat/completions timings 字段取官方计时
- PolyStrata 官方 docs/STRIX_HALO_WINDOWS.md：0.2.7 + Qwen3.8-Flash-Next IQ3_S，Ryzen AI Max+ 395 / 128GB / Windows 11
- 本机环境：Radeon 8060S gfx1151、Windows 可见内存 63.6G、BIOS 已设 64G carve-out、驱动 32.0.32029