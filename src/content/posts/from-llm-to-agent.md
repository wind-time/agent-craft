---
title: "从 LLM 调用到 Agent：差的不只是 while 循环"
pubDatetime: 2026-07-11T10:00:00Z
featured: true
draft: true
tags: [agent, 认知]
description: "很多人以为 Agent 就是「LLM 套个循环 + 工具」，但这忽略了上下文工程、状态管理与失败恢复。本文讲清 Agent 到底比裸 LLM 调用多了什么。"
---

import AgentDemoButton from "@/components/_interactive/AgentDemoButton.tsx";

> 这是一篇草稿示例，用来验证文章发布流程。正式内容持续更新中。

## 一个常见误解

如果你写过最简单的 LLM 调用：

```python
from langchain.chat_models import init_chat_model

llm = init_chat_model()
response = llm.invoke("今天天气怎么样？")
```

那你大概也听过「Agent 就是把它放进一个 `while` 循环里，让它反复调用工具直到任务完成」。这句话对，但只对了一半。

## 缺的不只是循环

真正生产可用的 Agent，至少还要解决三件事：

1. **上下文工程**——工具调用结果如何进入下一轮 prompt，而不撑爆上下文窗口。
2. **状态与记忆**——一次对话失败后如何恢复，跨会话如何沉淀。
3. **失败恢复**——工具抛错、模型幻觉调用不存在的工具，怎么办。

后续文章会逐一拆开讲。本文先建立心智模型。

## 交互式预览

下一篇《最小可运行 Agent》会嵌入一个可以点击运行的 Demo，你会看到 Agent 的真实 trace：

<AgentDemoButton demoId="hello-tool-call" label="运行：最小 Tool Call Demo" />

（当前为骨架占位，真实 trace 待后端运行时接入。）

---

*本文将持续更新，欢迎在 GitHub 提 Issue 交流。*
