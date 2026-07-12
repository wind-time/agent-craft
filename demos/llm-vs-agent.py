"""生成「裸 LLM vs. 带工具 Agent」对比型执行轨迹，供开篇文章的交互式按钮回放。

用确定性桩（stub）模型跑两条轨迹，保证回放稳定可复现：
- baseline：模拟裸 LLM 调用，无工具，直接生成一段像答案的文字。
- agent：模拟带工具的 ReAct 循环——第 1 轮请求工具，工具返回后第 2 轮给出有依据的答案。
带 MAX_TURNS 护栏，达到上限仍未完成则报错（呼应文章里「失败恢复」的护栏）。

运行：
    python demos/llm-vs-agent.py
无第三方依赖，无需 API key。
"""
from __future__ import annotations

import json
from pathlib import Path

# 配置
DEMO_ID = "llm-vs-agent"
REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_PATH = REPO_ROOT / "public" / "demos" / f"{DEMO_ID}.trace.json"
MAX_TURNS = 4  # 循环次数上限，对应文章「失败恢复」里的护栏


# ---- 桩工具 ----
def get_weather(city: str) -> str:
    # 真实场景换成联网 / 数据库查询
    return "晴，气温 28°C"


# ---- 桩模型：模拟裸 LLM 调用（无工具）----
def baseline_model(question: str) -> str:
    # 没有工具，凭参数生成一段像答案的文字（写死以稳定复现）
    return "北京今天晴，气温约 25°C。"


# ---- 桩模型：模拟带工具的 Agent 单轮决策 ----
def agent_model_turn(messages: list[dict], turn: int) -> dict:
    """第 0 轮请求工具；之后根据工具结果给出最终答案。"""
    if turn == 0:
        return {"kind": "tool_call", "name": "get_weather", "args": {"city": "北京"}}
    tool_msg = next(m for m in messages if m["role"] == "tool")
    # 基于工具结果生成有依据的回答
    return {"kind": "final", "content": "北京今天晴，气温 28°C。"}


# ---- 手搓 ReAct 循环（对应文章伪代码）----
def run_agent_loop(question: str) -> list[dict]:
    steps: list[dict] = []
    messages: list[dict] = [{"role": "user", "content": question}]

    for turn in range(MAX_TURNS):
        decision = agent_model_turn(messages, turn)
        if decision["kind"] == "tool_call":
            steps.append({
                "type": "thought",
                "content": "我无法知道实时天气，需要调用工具查询北京当前天气。",
            })
            steps.append({
                "type": "tool_call",
                "toolName": decision["name"],
                "content": f'{decision["name"]}(city="{decision["args"]["city"]}")',
            })
            result = get_weather(decision["args"]["city"])
            messages.append({"role": "tool", "content": result})
            steps.append({
                "type": "thought",
                "content": f"工具返回：{result}。现在可以给出有依据的回答了。",
            })
        else:
            steps.append({"type": "output", "content": decision["content"]})
            return steps

    # 走到这里说明达到循环上限仍未完成——对应文章「循环管不了的三件事」之失败恢复
    steps.append({"type": "error", "content": "达到最大循环次数仍未完成。"})
    return steps


def build_trace() -> dict:
    question = "北京今天天气怎么样？"
    baseline_steps = [
        {
            "type": "thought",
            "content": "用户问：「北京今天天气怎么样？」我没有工具，直接凭参数生成一段像答案的文字。",
        },
        {
            "type": "output",
            "content": baseline_model(question),
            "note": "无任何数据依据，模型概率生成——可能完全错误。",
        },
    ]
    agent_steps = run_agent_loop(question)
    return {
        "demoId": DEMO_ID,
        "variants": [
            {"id": "baseline", "label": "裸 LLM 调用（无工具）", "steps": baseline_steps},
            {"id": "agent", "label": "带工具循环的 Agent", "steps": agent_steps},
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
