"""生成「同一任务在三个框架里的代码风格对比」轨迹，供第 9 章回放。

不教某个框架的执行轨迹，而是展示「客服 triage 路由」这个同一任务，在不同框架里
用什么抽象表达。每个 variant 是一个框架，steps 是它的关键 API 调用序列，
让读者直观对比各框架的抽象差异。

运行：
    python demos/framework-comparison.py
无第三方依赖，无需 API key。
"""
from __future__ import annotations

import json
from pathlib import Path

# 配置
DEMO_ID = "framework-comparison"
REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_PATH = REPO_ROOT / "public" / "demos" / f"{DEMO_ID}.trace.json"

TASK = "客服 triage：把用户路由到 billing / refund 两个专用 Agent"


# ---- OpenAI Agents SDK：Handoff 原语 ----
def openai_sdk_steps() -> list[dict]:
    return [
        {"type": "thought",
         "content": "OpenAI Agents SDK 的核心是 Handoff——Agent 间委派，对模型表现为一个 tool（transfer_to_X_agent）。"},
        {"type": "tool_call", "toolName": "Agent(billing)",
         "content": 'billing_agent = Agent(name="Billing", instructions="处理账单", tools=[get_balance])'},
        {"type": "tool_call", "toolName": "Agent(refund)",
         "content": 'refund_agent = Agent(name="Refund", instructions="处理退款")'},
        {"type": "tool_call", "toolName": "Agent(triage)+handoffs",
         "content": 'triage_agent = Agent(name="Triage", handoffs=[billing_agent, refund_agent])  # 声明可委派给谁'},
        {"type": "tool_call", "toolName": "Runner.run_sync",
         "content": 'result = Runner.run_sync(triage_agent, "我要退款")  # 模型自己决定 handoff 给谁'},
        {"type": "output",
         "content": "风格：5 个原语（Agent/Tool/Handoff/Guardrail/Runner），轻量，默认绑 OpenAI Responses API。",
         "note": "适合已选 OpenAI 模型栈、客服式 triage、voice agent。"},
    ]


# ---- CrewAI：Crew + Flow 角色协作 ----
def crewai_steps() -> list[dict]:
    return [
        {"type": "thought",
         "content": "CrewAI 的核心是角色化 Agent + Crew 团队 + Flow 流程编排，为「研究→写作→评审」这类分工流程设计。"},
        {"type": "tool_call", "toolName": "Agent(role=)",
         "content": 'billing_agent = Agent(role="Billing Specialist", goal="处理账单问题", backstory="...")'},
        {"type": "tool_call", "toolName": "Task(agent=)",
         "content": 'billing_task = Task(description="处理账单", expected_output="...", agent=billing_agent)'},
        {"type": "tool_call", "toolName": "Crew(process=)",
         "content": 'crew = Crew(agents=[billing_agent, refund_agent], tasks=[...], process=Process.sequential)'},
        {"type": "tool_call", "toolName": "crew.kickoff()",
         "content": 'result = crew.kickoff()  # 按顺序/层级跑完所有 task'},
        {"type": "output",
         "content": "风格：角色驱动（role/goal/backstory），Crew+Flow 双抽象，与 LangChain 完全独立。",
         "note": "适合角色分工明确的多 Agent 流程、企业自动化。单 Agent 简单循环抽象过重。"},
    ]


# ---- LangChain + Deep Agents：subagents 声明式 ----
def langchain_steps() -> list[dict]:
    return [
        {"type": "thought",
         "content": "我们前 8 章用的这套：LangGraph 基建 + create_agent 框架 + Deep Agents harness，子 Agent 声明式注册。"},
        {"type": "tool_call", "toolName": "SubAgent(billing)",
         "content": 'billing = SubAgent(name="billing-agent", description="处理账单", system_prompt="...", tools=[get_balance])'},
        {"type": "tool_call", "toolName": "SubAgent(refund)",
         "content": 'refund = SubAgent(name="refund-agent", description="处理退款", system_prompt="...")'},
        {"type": "tool_call", "toolName": "create_deep_agent(subagents=)",
         "content": 'agent = create_deep_agent(model=..., subagents=[billing, refund])  # 主 Agent 自动获得 task 工具'},
        {"type": "tool_call", "toolName": "agent.invoke()",
         "content": 'result = agent.invoke({"messages": "我要退款"})  # 主 Agent 用 task(description, subagent_type) 委派'},
        {"type": "output",
         "content": "风格：三层栈最完整，子 Agent 上下文隔离（Context Quarantine），厂商中立。",
         "note": "适合深度上下文工程、长任务、要自己掌控图编排。学习曲线最陡。"},
    ]


def build_trace() -> dict:
    return {
        "demoId": DEMO_ID,
        "variants": [
            {"id": "openai", "label": "OpenAI Agents SDK（Handoff）", "steps": openai_sdk_steps()},
            {"id": "crewai", "label": "CrewAI（Crew + Flow）", "steps": crewai_steps()},
            {"id": "langchain", "label": "LangChain + Deep Agents（subagents）", "steps": langchain_steps()},
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
