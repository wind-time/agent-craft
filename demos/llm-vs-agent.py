"""llm-vs-agent 预录 trace 生成脚本（方案 C 的「录」）。

用途：
- 生成 public/demos/llm-vs-agent.trace.json，供文章 from-llm-to-agent 的交互式按钮回放。
- 这是一个 *对比型* demo：用确定性桩（stub）模型跑两条轨迹，保证回放稳定可复现。
- 真正接入 LLM 的自由输入型 demo 见第 10 章（方案 A）。

运行：
    python demos/llm-vs-agent.py
无第三方依赖，无需 API key。

桩模型说明：
- baseline_model：模拟裸 LLM，直接「幻觉」一个答案（无工具）。
- agent_model_turn + run_agent_loop：模拟 ReAct Agent 的 while 循环——
  第 1 轮请求工具，工具返回后第 2 轮给出最终答案；带 max_turns 护栏。
这复刻了文章里的伪代码 while 循环，只是大脑换成了确定性的桩。
"""
from __future__ import annotations

import json
from pathlib import Path

# 配置（按需修改）
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
    # 没有工具，凭概率生成一段像答案的文字（写死以稳定复现）
    return "北京今天晴，气温约 25°C。"


# ---- 桩模型：模拟带工具的 ReAct Agent 单轮决策 ----
def agent_model_turn(messages: list[dict], turn: int) -> dict:
    """第 0 轮请求工具；之后根据工具结果给出最终答案。"""
    if turn == 0:
        return {"kind": "tool_call", "name": "get_weather", "args": {"city": "北京"}}
    tool_msg = next(m for m in messages if m["role"] == "tool")
    # 桩：基于工具结果生成有依据的回答
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
