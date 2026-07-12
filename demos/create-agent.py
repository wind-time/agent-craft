"""生成「手写 StateGraph vs create_agent 一键封装」对比型执行轨迹，供第 5 章回放。

用确定性桩对比两种构建 Agent 的方式，执行同一个任务（查资料→审批→写文件）：
- handcraft：第 4 章那种手写 StateGraph——定义 State、写 agent/tools 节点、写路由、连边、compile，30+ 行样板。
- create-agent：用 create_agent 一行创建，加 HumanInTheLoopMiddleware 做审批，interrupt 暂停、Command 恢复。

运行：
    python demos/create-agent.py
无第三方依赖，无需 API key。
"""
from __future__ import annotations

import json
from pathlib import Path

# 配置
DEMO_ID = "create-agent"
REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_PATH = REPO_ROOT / "public" / "demos" / f"{DEMO_ID}.trace.json"


# ---- 手写 StateGraph：30+ 行样板代码 ----
def handcraft_steps() -> list[dict]:
    return [
        {"type": "thought", "content": "第 1 步：定义 State（TypedDict + add_messages reducer）。"},
        {"type": "thought", "content": "第 2 步：写 agent 节点函数（调 model_with_tools）。"},
        {"type": "thought", "content": "第 3 步：写 tools 节点（或 import ToolNode）。"},
        {"type": "thought", "content": "第 4 步：写路由函数 should_continue（看 tool_calls 是否为空）。"},
        {"type": "thought", "content": "第 5 步：StateGraph(State).add_node().add_edge().add_conditional_edges()。"},
        {"type": "thought", "content": "第 6 步：compile(checkpointer=InMemorySaver())。"},
        {"type": "thought", "content": "第 7 步：还要审批？得自己加 interrupt_before + Command 恢复逻辑……"},
        {"type": "tool_call", "toolName": "行数统计",
         "content": "约 35 行样板代码，其中业务逻辑只占 5 行，其余全是图组装和路由样板。"},
        {"type": "output",
         "content": "跑通了，但每写一个 Agent 都要重复这套——可维护性差，且审批/HITL 要自己额外实现。",
         "note": "这正是 create_agent 要解决的：把样板抽掉，只留 model + tools + middleware。"},
    ]


# ---- create_agent：一行创建 + Middleware 审批 ----
def create_agent_steps() -> list[dict]:
    return [
        {"type": "thought",
         "content": "一行创建：agent = create_agent(model, tools, system_prompt=..., middleware=[...])。内部就是 StateGraph 的预组装。"},
        {"type": "tool_call", "toolName": "create_agent",
         "content": "create_agent(model, tools=[search, write_file], system_prompt='你是助手', middleware=[HumanInTheLoopMiddleware(...)])"},
        {"type": "thought",
         "content": "返回值是 CompiledStateGraph——所以第 4 章学的 checkpointer、get_state_history、作为子图嵌入，全都还能用。"},
        # 模型决定调 write_file
        {"type": "thought",
         "content": "[轮 1] 模型决定调 write_file('/tmp/note.md', 'LangGraph 很强')。"},
        {"type": "tool_call", "toolName": "write_file",
         "content": 'write_file(path="/tmp/note.md", content="LangGraph 很强")  # 待审批'},
        # HumanInTheLoopMiddleware 触发 interrupt
        {"type": "thought",
         "content": "HumanInTheLoopMiddleware 拦截 write_file：interrupt() 暂停图，把动作发给客户端等审批。",
         "note": "必须配 checkpointer——状态要持久化才能在 interrupt 后恢复。"},
        {"type": "output",
         "content": "⏸️ 暂停。result.interrupts 里有待审批动作（工具名、参数、description）。客户端拿到后展示给人工。"},
        # 人工审批后用 Command 恢复
        {"type": "thought",
         "content": "人工看完了，决定 approve。恢复用 Command(resume=...)——不是 invoke(None)。"},
        {"type": "tool_call", "toolName": "Command(resume=...)",
         "content": 'agent.invoke(Command(resume={"decisions": [{"type": "approve"}]}), config=config)'},
        {"type": "thought",
         "content": "图从断点续跑：write_file 真正执行，返回「已写入 12 字符」。"},
        {"type": "output",
         "content": "✅ 完成。整个审批流程：create_agent 一行 + 一个 Middleware，不用手写 interrupt 逻辑。"},
    ]


def build_trace() -> dict:
    return {
        "demoId": DEMO_ID,
        "variants": [
            {"id": "handcraft", "label": "手写 StateGraph（35 行样板）", "steps": handcraft_steps()},
            {"id": "create-agent", "label": "create_agent + Middleware", "steps": create_agent_steps()},
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
