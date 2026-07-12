"""生成「单 Agent 一把梭 vs 主 Agent 调度子 Agent」对比型轨迹，供第 7 章回放。

用确定性桩对比两种方式执行同一个复杂任务（调研三个主题→写对比报告），展示上下文隔离差异：
- solo：单个 Agent 把三个主题的调研全揽了，每个 search 结果都堆进主上下文，三轮后膨胀。
- coordinator：主 Agent 把三个主题各委派给一个研究子 Agent，子 Agent 中间消息隔离，
  只回传最终摘要给主 Agent，主上下文始终干净。

运行：
    python demos/deep-agents-subagents.py
无第三方依赖，无需 API key。
"""
from __future__ import annotations

import json
from pathlib import Path

# 配置
DEMO_ID = "deep-agents-subagents"
REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_PATH = REPO_ROOT / "public" / "demos" / f"{DEMO_ID}.trace.json"

TASK = "调研 LangGraph / Deep Agents / MCP 三家子 Agent 机制，写一份对比报告"


# ---- 单 Agent：三个主题全揽，上下文膨胀 ----
def solo_steps() -> list[dict]:
    return [
        {"type": "thought",
         "content": "[轮 1] 主 Agent 自己调研 LangGraph 子 Agent 机制。"},
        {"type": "tool_call", "toolName": "search",
         "content": 'search("LangGraph 子 Agent")  → 800 token 资料进主上下文'},
        {"type": "thought",
         "content": "[轮 2] 自己调研 Deep Agents 子 Agent 机制。主上下文现在 ~1600 token。"},
        {"type": "tool_call", "toolName": "search",
         "content": 'search("Deep Agents 子 Agent")  → 750 token 再进主上下文'},
        {"type": "thought",
         "content": "[轮 3] 自己调研 MCP。主上下文 ~2400 token，且这些原始资料每轮都要重发。"},
        {"type": "tool_call", "toolName": "search",
         "content": 'search("MCP 子 Agent")  → 700 token 又进主上下文'},
        {"type": "thought",
         "content": "[轮 4] 写报告。模型要把 2400 token 原始资料全读一遍才能对比——这一轮烧 2400 输入。"},
        {"type": "output",
         "content": "报告生成。但主上下文被原始资料塞满，后续任何追问都要背着这几千 token。",
         "note": "单 Agent 的瓶颈：什么都自己干，上下文随子任务数线性增长。"},
    ]


# ---- 主 Agent + 子 Agent：委派隔离，主上下文干净 ----
def coordinator_steps() -> list[dict]:
    return [
        {"type": "thought",
         "content": "主 Agent 接到任务，先 write_todos 拆成三项子任务。"},
        {"type": "tool_call", "toolName": "write_todos",
         "content": 'write_todos(todos=[{content:"调研 LangGraph",status:"in_progress"},{content:"调研 Deep Agents",status:"pending"},{content:"调研 MCP",status:"pending"},{content:"写对比报告",status:"pending"}])  → 存 state，不进 messages prompt'},
        # 委派第一个子 Agent
        {"type": "thought",
         "content": "主 Agent 调 task 工具委派：task(description='调研 LangGraph 子 Agent 机制', subagent_type='research-agent')。"},
        {"type": "tool_call", "toolName": "task",
         "content": 'task(description="调研 LangGraph 子 Agent 机制", subagent_type="research-agent")  → 同步阻塞，等子 Agent 跑完'},
        {"type": "thought",
         "content": "⚡ 子 Agent 内部跑了 3 轮 search（共 2000+ token 中间消息），但这些全隔离在子 Agent 自己的上下文里，不进主 Agent。主 Agent 只收到一条 ToolMessage：最终摘要 200 token。",
         "note": "这就是 Context Quarantine：子 Agent 中间几十次 tool calls 对主 Agent 不可见，只回传最终结果。"},
        {"type": "output",
         "content": "ToolMessage 返回：『LangGraph 子 Agent 机制摘要：SubAgentMiddleware + task 工具...』（200 token）"},
        # 委派第二、三个
        {"type": "thought",
         "content": "write_todos 更新进度，然后委派第二个子 Agent。"},
        {"type": "tool_call", "toolName": "task",
         "content": 'task(description="调研 Deep Agents 子 Agent", subagent_type="research-agent")  → 又隔离一轮'},
        {"type": "tool_call", "toolName": "task",
         "content": 'task(description="调研 MCP 子 Agent", subagent_type="research-agent")  → 隔离三轮'},
        # 主 Agent 汇总
        {"type": "thought",
         "content": "三个子 Agent 都回了摘要（各 200 token，共 600 token），主上下文只有这三条摘要，干净。"},
        {"type": "output",
         "content": "主 Agent 基于三份摘要写对比报告。整个过程中主上下文始终低水位——子 Agent 的中间过程全被隔离。",
         "note": "主 Agent 只看到『我委派了什么 + 最终结果』，看不到子 Agent 中间的几十次 tool calls。"},
    ]


def build_trace() -> dict:
    return {
        "demoId": DEMO_ID,
        "variants": [
            {"id": "solo", "label": "单 Agent 一把梭（上下文膨胀）", "steps": solo_steps()},
            {"id": "coordinator", "label": "主 Agent + 子 Agent（隔离）", "steps": coordinator_steps()},
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
