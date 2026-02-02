# agent-governance-gate

[![测试: 42 通过](https://img.shields.io/badge/tests-42%20passing-brightgreen)]()
[![版本: 0.1.1](https://img.shields.io/badge/version-0.1.1-blue)]()
[![许可证: MIT](https://img.shields.io/badge/license-MIT-blue)]()

[English](README.md) | [简体中文](README_zh.md)

一个 Agent 系统的治理网关，基于风险和责任（而非仅仅是意图）来决定是否允许、限制、升级或停止某个操作。

本项目专注于为概率性 AI 系统提供工程化控制能力，
而非模型能力、提示设计或用户体验优化。

---

## 快速开始（2 分钟）

### 安装

```bash
# 核心库
pip install -e .

# 包含 HTTP API
pip install -e ".[api]"

# 验证安装
govgate --version
```

### 试用案例

```bash
# 运行欺诈检测案例（返回 STOP，final_gate="safety"）
cd examples/case_law
PYTHONPATH=../../src govgate eval cases/011_fraud_detection/input.json \
  --policy ../../policies/presets/customer_support.yaml
```

输出：
```json
{
  "action": "STOP",
  "final_gate": "safety",
  "rationale": "Fraud request detected: 'payment system' - Refusing to process...",
  "trace_id": "ff69b873-7b5a-4bc1-a18e-d0814a87cacb"
}
```

### 启动 HTTP API

```bash
# 启动服务
govgate serve --port 8000

# 在另一个终端测试
curl -X POST http://localhost:8000/decision \
  -H "Content-Type: application/json" \
  -d '{
    "intent": {"name": "test", "confidence": 0.9},
    "context": {},
    "evidence": {}
  }'
```

### 集成（Python）

```python
from governance_gate.core.pipeline import GovernancePipeline
from governance_gate.gates import SafetyGate, ResponsibilityGate
from governance_gate.core.types import Intent, Context, Evidence

pipeline = GovernancePipeline(gates=[SafetyGate(), ResponsibilityGate()])
decision = pipeline.evaluate(intent, context, evidence)

print(f"决策: {decision.action}")        # ALLOW/RESTRICT/ESCALATE/STOP
print(f"拦截者: {decision.final_gate}")  # "safety", "responsibility" 等
```

---

## 集成方式

根据你的架构选择合适的集成方式：

### 方式 1: Python 库（推荐）

**适用场景：** 原生 Python 应用、自定义 agent、单体系统

**性能：** 最低延迟（~1-2ms），无网络开销

**文档：** [集成指南](docs/integration.md)

**快速开始：**
```python
from governance_gate.core.pipeline import GovernancePipeline
from governance_gate.gates import SafetyGate, ResponsibilityGate
from governance_gate.core.types import Intent, Context, Evidence

pipeline = GovernancePipeline(gates=[SafetyGate(), ResponsibilityGate()])
decision = pipeline.evaluate(intent, context, evidence)

if decision.action == DecisionAction.ALLOW:
    return execute_tools()
elif decision.action == DecisionAction.ESCALATE:
    return escalate_to_human(decision.rationale)
```

### 方式 2: HTTP API

**适用场景：** 微服务、多语言系统、外部部署

**性能：** 网络开销（~10-50ms）

**文档：** [API 参考](docs/api.md)

**快速开始：**
```bash
# 启动服务
govgate serve --port 8000

# 发送请求
curl -X POST http://localhost:8000/decision \
  -H "Content-Type: application/json" \
  -d '{
    "intent": {"name": "refund_request", "confidence": 0.9},
    "context": {"user_id": "user_123", "channel": "web"},
    "evidence": {"facts": {...}, "rag": {...}}
  }'
```

### 方式 3: LangGraph / LangChain

**适用场景：** Agent 框架用户、工作流编排

**文档：** [框架集成](docs/integration.md#langgraph-integration)

**示例：** [starter-kits/customer_support/](starter-kits/customer_support/)

**需要帮助选择？** → 查看 [集成指南](docs/integration.md#choosing-a-method)

---

## 为什么存在这个项目

现代 Agent 和 RAG 系统本质上是概率性的。

即使拥有高精度的意图识别，系统在生产环境中仍然会失败，因为：

- 它们回答依赖于无法验证或过时事实的问题
- 它们在不确定的情况下继续执行
- 它们跨越责任边界（承诺、金钱、权限）
- 失败不明确、不可追踪、无法停止

大多数实现尝试通过以下方式解决这些问题：

- 提高模型准确率
- 添加提示或启发式规则
- 调优检索策略

本项目采取不同的立场：

这些失败不是模型问题。
它们是治理问题。

**核心原则：** 概率性系统需要确定性的责任边界。工程系统必须知道何时不行动。

---

## 这个项目是什么和不是什么

本项目是：

- Agent 系统的治理层
- 放置在意图识别之后的决策网关
- 将"不行动"作为显式系统决策的机制
- 风险和责任控制的可复用工程骨架

本项目不是：

- 另一个 Agent 实现
- 聊天机器人或演示应用
- 提示工程框架
- 业务流程引擎

---

## 核心思想

意图识别回答的问题：

用户想要做什么？

治理回答的是另一个问题：

系统现在被允许做这个吗？

这是两个根本不同的问题。

本项目将治理作为一等工程关注点。

---

## 决策流程

用户输入
  ->
意图识别（语言理解）
  ->
风险和责任网关（本项目）
  ->
ALLOW / RESTRICT / ESCALATE / STOP
  ->
Agent 执行（如果被允许）

意图识别可以是概率性的。
责任边界必须是确定性的。

---

## 治理原则

网关使用三个正交维度来评估请求。

### 1. 事实可验证性

- 响应是否依赖于当前或外部事实
- 这些事实是否可用、权威且可信
- 系统是否有权访问它们

如果事实无法验证，系统必须不得得出结论。

---

### 2. 不确定性暴露

- 检索置信度是否低
- 多个工具是否产生冲突结果
- 知识版本是否过时或不完整

绝不能静默吸收不确定性。

---

### 3. 责任边界

- 响应是否会被解释为组织承诺
- 是否影响金钱、权限或不可逆决策
- 政策或法规是否要求人工判断

如果涉及责任，系统必须不得决策。

---

## 决策结果

治理网关始终产生明确的决策。

ALLOW
  可以安全地自主执行

RESTRICT
  仅在约束、免责声明或建议下响应

ESCALATE
  需要人工审查或批准

STOP
  由于权限或信息不足而不继续

每个决策包括：

- 决策背后的推理
- 支持决策的证据
- 用于审计的可追溯标识符

---

## 示例：相同意图，不同结果

意图：order_status_query

用户问题：
我如何查看订单状态？
决策：
ALLOW
原因：
仅规则解释

用户问题：
为什么我的订单还没发货？
决策：
RESTRICT
原因：
依赖实时事实

用户问题：
你们搞砸了，应该赔偿我
决策：
ESCALATE
原因：
财务责任

意图没有改变。
风险和责任改变了。

---

## 集成理念

这个网关是框架无关的。

它可以嵌入到：

- 基于 LangGraph 的 agent 流程
- Dify 工作流
- 自定义 agent 管道
- 基于 API 的 AI 服务

网关不关心意图是如何产生的。
它不执行操作。

它只决定是否允许执行。

---

## 项目状态

本仓库提供：

- 最小化的治理决策引擎
- 策略驱动的风险规则
- 规范化的失败案例
- 确定性的决策行为

它有意避免：

- 特定领域的业务逻辑
- 模型优化
- UI 或产品功能

目标是工程清晰度，而非完整性。

---

## 适合谁

本项目面向负责以下工作的工程师和架构师：

- 构建生产级 Agent 或 RAG 系统
- 对系统故障负责，而不仅仅是演示
- 设计必须安全停止的 AI 系统
- 将 AI 视为基础设施，而非功能

---

## 范围与非目标

**本项目是：**

- 治理网关（ALLOW/RESTRICT/ESCALATE/STOP 决策）
- 确定性、可审计的决策逻辑
- 策略驱动的规则评估（YAML）
- 框架无关的集成层
- 生产系统的参考实现

**本项目不是：**

- 工作流引擎（使用 LangGraph、Temporal 等）
- 规则引擎（我们使用简单的 YAML 策略，而非 Drools/OPA）
- LLM agent 框架（我们与任何框架集成，不竞争）
- 工具执行（我们在工具调用之前治理，不执行）
- 数据库/持久化层（审计导出是可选的）
- 监控/可观测性平台（我们提供决策，不提供仪表板）

**为什么这种区分很重要：**

本项目是一个**治理原语**。
它被设计为嵌入到现有系统中，而不是替换它们。

如果你需要：
- 工作流编排 → 使用 LangGraph/Dify/Temporal
- 复杂规则管理 → 在我们的 YAML 策略之上构建
- 完整的 agent 平台 → 将我们的网关集成为预执行检查
- 监控基础设施 → 消费我们的决策事件

**反模式（不要这样做）：**
```
"向治理网关添加功能 X"
```
功能蔓延会破坏清晰度。

**正确模式：**
```
"使用治理网关保护功能 X"
"在监控系统中消费治理决策"
"在 YAML 策略之上构建策略管理 UI"
```

---

## 许可证

MIT
