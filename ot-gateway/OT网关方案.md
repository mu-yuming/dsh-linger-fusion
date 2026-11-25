# P0：OT 只读遥测网关方案（DSH × 产线设备）

## 0. 关键实证修正（相对最初评估）
最初评估判定"Composio 接不了 OT，改造≈重建"。本轮核查发现：
DSH 的 MCP 连接器市场里虽无现成工业连接器（OPC UA/PLC/工业 三个关键词均 0 结果），
但**开源世界已有多个成熟的 OT→MCP 网关**，无需从零造轮子。
结论下调为：不需要改 Composio，也不需要从零写协议栈，而是**选一个现成网关接进 DSH 的连接器层**。
DSH 侧成本从"重建"降为"配置 + 安全策略"。

## 1. 现成网关盘点（均来自公开仓库/PyPI，非臆造）

| 项目 | 协议覆盖 | 安全特性 | 部署方式 | 适合场景 |
|---|---|---|---|---|
| OPCUA-MCP (IndustriAgents/theluckystrike) | OPC UA | **默认 read-only profile**；带模拟工厂（传感器/执行器/方法/历史/事件） | git clone + uv sync | **PoC 起步首选**：不碰真实设备即可验证 |
| opcua-mcp-server (PyPI) | OPC UA | 默认 read-only profile | `uvx opcua-mcp-server` | 轻量 OPC UA 接入 |
| plctap (PyPI) | Modbus TCP/RTU、FINS、MELSEC、Siemens S7comm、IEC 60870-5-104、EtherNet/IP | 读写 + 诊断 | `uvx plctap` | 多厂商存量 PLC（西门子/三菱等） |
| proxus-mcp (proxus-io) | Modbus TCP + OPC UA | **强制 read-only**，单一 Native AOT 二进制 | 单可执行文件 | 产线环境少依赖部署 |
| labmcp-modbus (PyPI) | Modbus TCP/RTU | `--read-only`、`raw_writes=false` 细粒度放行 | pip/uvx | Modbus 场景的安全加固 |
| opcua-mcp (kukapay) | OPC UA | 监控/分析/控制（含写，需自行约束） | pip install asyncua mcp | 需要控制能力时（慎用） |

## 2. 选型建议
- **PoC 阶段**：OPCUA-MCP（IndustriAgents）——默认只读 + 自带模拟工厂，可零真实设备验证。
- **真实设备（OPC UA）**：opcua-mcp-server 或 proxus-mcp（后者单二进制、强制只读，产线更稳）。
- **存量 PLC（非 OPC UA）**：plctap——覆盖西门子 S7、三菱 MELSEC、Modbus 等主流协议。
- 原则：先只读、先模拟、先单一设备点位；绝不一步到位接全产线。

## 3. 安全边界（产线红线，不可协商）
1. **默认只读**：网关侧选 read-only profile；禁用一切 write/call 方法工具。
2. **DSH 侧白名单**：用 `mcp_connector_policy` 只放行 `browse/read` 类工具，write 类显式 deny。
3. **写操作隔离**：任何对 PLC/伺服/加热炉的写入不走 Agent，必须硬联锁 + 人工审批 + 独立通道。
4. **scope 隔离**：连接器设为 project 级（仅产线 Workspace 可见），不 global 扩散。
5. **会话 TTL**：按需激活工具（`mcp_connector_session_tools`），设短 TTL，不常驻。

## 4. DSH 接入配置骨架（stdio 连接器）
本机 `mcp_connector_configure` 支持 stdio 连接（command/args/env），无需 GUI 授权。骨架如下（**字段以实际选型为准，此处为 OPCUA-MCP 示例**）：

```
mcp_connector_configure({
  name: "opcua-telemetry",
  transport: "stdio",
  command: "uvx",
  args: ["opcua-mcp-server"],
  envJson: '{"OPCUA_SERVER_URL":"opc.tcp://<设备地址>:4840"}',
  scope: "project"
})
```

接入后：
- `mcp_connector_health_check` 验证握手；
- `mcp_connector_tools_list` 看暴露了哪些工具；
- `mcp_connector_policy(action:"preview" ...)` 预览只读白名单，`apply` 落策略；
- `mcp_connector_session_tools` 按会话激活、设短 TTL。

## 5. 落地步骤（PDCA）
- **P0-a 模拟验证**：起网关的模拟工厂，DSH 接入后读一个模拟温度点。验收：能读到值、工具列表里无 write 工具。
- **P0-b 真实单点**：接一台设备的一个只读点位（如 1 号炉 PV），确认数据正确、延迟可接受。
- **P0-c 安全核验**：确认 policy 白名单生效——尝试调用 write 工具应被拒绝。
- **P1 联动**：把只读遥测接入上一轮的"双路交叉校验"，作为分析快照的数据源。

## 6. 诚实标注的边界
- 本会话无 shell 绑定：起模拟工厂/装 uvx 需本地终端执行，配置骨架中的命令需你本地跑通。
- 上述网关均为第三方开源项目，产线使用前需做供应链与安全评估（依赖、维护活跃度、CVE）。
- 未实测任何网关与本机定制版 DSH 的兼容性；配置骨架是接口形状示例，不是已验证配置。
- OPC UA 需设备侧开启 server 并配置权限；存量设备可能只有 Modbus/S7，需按设备实际协议选型。

## 7. 参考来源
- PyPI: opcua-mcp-server、opcua-mcp、plctap、labmcp-modbus
- GitHub: IndustriAgents/OPCUA-MCP、theluckystrike/OPCUA-MCP、kukapay/opcua-mcp、proxus-io/proxus-mcp
- MCP World: opcua-mcp-server 配置示例（含 plant mock + read-only profile）