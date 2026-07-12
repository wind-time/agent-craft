"""生成「普通 agent 上下文越堆越爆 vs Deep Agent 外置到文件系统」对比型轨迹，供第 6 章回放。

用确定性桩对比两种 Agent 执行同一个多步研究任务（查 3 个主题→汇总），展示上下文管理差异：
- plain-agent：普通 create_agent，每个工具结果都堆进 messages，跑几轮上下文膨胀、token 飙升。
- deep-agent：create_deep_agent，中间结果 write_file 到虚拟文件系统，主上下文只留最终汇总。

运行：
    python demos/deep-agents-context.py
无第三方依赖，无需 API key。
"""
from __future__ import annotations

import json
from pathlib import Path

# 配置
DEMO_ID = "deep-agents-context"
REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_PATH = REPO_ROOT / "public" / "demos" / f"{DEMO_ID}.trace.json"

TASK = "调研 LangGraph / Deep Agents / MCP 三个主题，各查要点后汇总成报告"


# ---- 普通 agent：结果全堆进 messages ----
def plain_steps() -> list[dict]:
    return [
        {"type": "thought",
         "content": "[轮 1] 查 LangGraph 要点。工具返回 800 token 的资料，全部 append 进 messages。"},
        {"type": "tool_call", "toolName": "search",
         "content": 'search("LangGraph 要点")  → 800 token 资料塞进 messages'},
        {"type": "thought",
         "content": "[轮 2] 查 Deep Agents 要点。又 750 token 进 messages，现在 messages 累计 ~1600 token。"},
        {"type": "tool_call", "toolName": "search",
         "content": 'search("Deep Agents 要点")  → 750 token 再塞进 messages'},
        {"type": "thought",
         "content": "[轮 3] 查 MCP 要点。再 700 token。messages 现在 ~2400 token，且这些原始资料后面每轮都要重发给模型。"},
        {"type": "tool_call", "toolName": "search",
         "content": 'search("MCP 要点")  → 700 token 又塞进 messages'},
        {"type": "thought",
         "content": "[轮 4] 开始汇总。模型要把 2400 token 的资料全读一遍才能写报告——这一轮就烧 2400 输入 token。"},
        {"type": "error",
         "content": "💥 上下文膨胀：每轮都把全部历史资料重发，token 成本随轮次线性飙升。",
         "note": "如果再多查几个主题，messages 很快超模型上下文窗口，直接 400 报错。"},
    ]


# ---- Deep Agent：中间结果外置到虚拟文件系统 ----
def deep_steps() -> list[dict]:
    return [
        {"type": "thought",
         "content": "Deep Agent 默认启用虚拟文件系统（StateBackend），自带 write_file / read_file / ls / grep 等工具，无需配置。"},
        {"type": "thought",
         "content": "[轮 1] 查 LangGraph 要点。和普通 agent 一样调 search，但拿到结果后立刻 write_file 外置。"},
        {"type": "tool_call", "toolName": "search",
         "content": 'search("LangGraph 要点")  → 800 token 资料'},
        {"type": "tool_call", "toolName": "write_file",
         "content": 'write_file(path="/research/langgraph.md", content=<800 token 资料>)  → 资料外置到文件'},
        {"type": "thought",
         "content": "关键：这 800 token 的资料不再留在 messages 里，主上下文只多了一条「已写入 langgraph.md」。"},
        {"type": "thought",
         "content": "[轮 2] 查 Deep Agents 要点，同样 write_file 外置。主上下文还是只有几条短消息。"},
        {"type": "tool_call", "toolName": "write_file",
         "content": 'write_file(path="/research/deepagents.md", content=<750 token>)  → 外置'},
        {"type": "thought",
         "content": "[轮 3] 查 MCP 要点，write_file 外置。三个主题的资料都在文件系统里，messages 始终很短。"},
        {"type": "tool_call", "toolName": "write_file",
         "content": 'write_file(path="/research/mcp.md", content=<700 token>)  → 外置'},
        {"type": "thought",
         "content": "[轮 4] 汇总。模型 read_file 逐个读取需要的片段（或用 grep 只取关键行），主上下文只装载真正需要的内容。"},
        {"type": "tool_call", "toolName": "read_file",
         "content": 'read_file(path="/research/langgraph.md")  → 按需取回，不堆历史'},
        {"type": "output",
         "content": "报告生成完毕。整个过程中主上下文始终保持在低水位——资料按需读写，不累积。",
         "note": "这就是 Context Engineering：把上下文当工作台，资料分类放进抽屉（文件系统），需要时再取，而不是全摊在台子上。"},
    ]


def build_trace() -> dict:
    return {
        "demoId": DEMO_ID,
        "variants": [
            {"id": "plain", "label": "普通 agent（上下文膨胀）", "steps": plain_steps()},
            {"id": "deep", "label": "Deep Agent（外置到文件系统）", "steps": deep_steps()},
        ],
    }


def main() -> None:
    trace = build_trace()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(trace, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"已写入 {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
