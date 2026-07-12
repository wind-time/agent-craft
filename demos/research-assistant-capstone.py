"""生成「个人研究助理」综合案例的执行轨迹，供第 10 章回放。

这个 demo 综合演示前 6-8 章的能力：虚拟文件系统外置资料 + write_todos 规划 +
子 Agent 委派隔离 + 记忆用户偏好 + Skills 按需加载。用确定性桩跑一个完整的多步任务：
「记住用户偏好 TypeScript → 调研两个主题 → 用 TypeScript 风格写报告」。

运行：
    python demos/research-assistant-capstone.py
无第三方依赖，无需 API key。
"""
from __future__ import annotations

import json
from pathlib import Path

# 配置
DEMO_ID = "research-assistant-capstone"
REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_PATH = REPO_ROOT / "public" / "demos" / f"{DEMO_ID}.trace.json"


def build_steps() -> list[dict]:
    return [
        # 启动：记忆自动加载
        {"type": "thought",
         "content": "Agent 启动：MemoryMiddleware 从 StoreBackend 加载 /memories/AGENTS.md，用户偏好「TypeScript、回复简短」自动进 system prompt。"},
        # 接任务，write_todos 规划
        {"type": "thought",
         "content": "用户：「调研 LangGraph 和 Deep Agents，写一份对比报告，用 TypeScript 风格。」Agent 识别为复杂任务，write_todos 拆解。"},
        {"type": "tool_call", "toolName": "write_todos",
         "content": 'write_todos(todos=[{content:"调研 LangGraph",status:"in_progress"},{content:"调研 Deep Agents",status:"pending"},{content:"写对比报告",status:"pending"}])'},
        # 委派子 Agent 1（上下文隔离）
        {"type": "thought",
         "content": "主 Agent 委派：task(description='调研 LangGraph 核心特性', subagent_type='research-agent')。子 Agent 内部跑 3 轮 search（2000+ token 中间消息）全隔离。"},
        {"type": "tool_call", "toolName": "task",
         "content": 'task(description="调研 LangGraph 核心特性", subagent_type="research-agent")  → 隔离运行'},
        {"type": "output",
         "content": "ToolMessage 回传：『LangGraph：StateGraph + Checkpointer + 条件边，适合需要持久化和时间旅行的场景...』（200 token 摘要）"},
        # 委派子 Agent 2
        {"type": "thought",
         "content": "write_todos 更新进度，委派第二个子 Agent 调研 Deep Agents。"},
        {"type": "tool_call", "toolName": "task",
         "content": 'task(description="调研 Deep Agents 核心特性", subagent_type="research-agent")  → 隔离运行'},
        {"type": "output",
         "content": "ToolMessage 回传：『Deep Agents：虚拟文件系统 + 子 Agent + 记忆 + Skills，生产级 Harness...』（200 token 摘要）"},
        # 文件系统外置资料
        {"type": "thought",
         "content": "主 Agent 把两份摘要 write_file 外置到 /research/ 目录，主上下文保持干净。"},
        {"type": "tool_call", "toolName": "write_file",
         "content": 'write_file(path="/research/langgraph.md", content=<摘要>)  → 资料外置'},
        {"type": "tool_call", "toolName": "write_file",
         "content": 'write_file(path="/research/deepagents.md", content=<摘要>)  → 资料外置'},
        # Skills 按需加载（写报告有个 skill）
        {"type": "thought",
         "content": "要写报告了——启动时已加载 report-writer skill 的元数据（L1）。现在 skill 被激活。"},
        {"type": "tool_call", "toolName": "read_file",
         "content": 'read_file(path="/skills/report-writer/SKILL.md", limit=1000)  → L2 加载完整指令'},
        {"type": "thought",
         "content": "SKILL.md 指令要求：先 read_file 取回资料，按对比表结构组织。Agent 按指令执行（L3 按需）。"},
        {"type": "tool_call", "toolName": "read_file",
         "content": 'read_file(path="/research/langgraph.md")  → 按需取回'},
        {"type": "tool_call", "toolName": "read_file",
         "content": 'read_file(path="/research/deepagents.md")  → 按需取回'},
        # 输出
        {"type": "output",
         "content": "对比报告生成完毕（TypeScript 风格、简短——偏好生效）。整个过程中：偏好靠记忆、资料靠文件系统、调研靠子 Agent 隔离、写报告靠 Skill 指令，主上下文始终干净。",
         "note": "这就是前 9 章学的全部能力，在一个真实任务里协同工作。"},
    ]


def build_trace() -> dict:
    return {
        "demoId": DEMO_ID,
        "variants": [
            {"id": "capstone", "label": "个人研究助理（综合案例）", "steps": build_steps()},
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
