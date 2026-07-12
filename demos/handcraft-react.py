"""生成「手搓 ReAct 多轮循环」执行轨迹，供第 3 章交互式按钮回放。

用一个需要多轮工具调用的任务（算两地温差），完整展示 ReAct 循环：
Thought → Action(tool_call) → Observation(工具结果) → Thought → ... → Final
用确定性桩模拟带工具的模型决策，保证回放稳定可复现。

运行：
    python demos/handcraft-react.py
无第三方依赖，无需 API key。
"""
from __future__ import annotations

import json
from pathlib import Path

# 配置
DEMO_ID = "handcraft-react"
REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_PATH = REPO_ROOT / "public" / "demos" / f"{DEMO_ID}.trace.json"

QUESTION = "北京和上海今天温差多少度？"
MAX_TURNS = 10  # 循环上限护栏，防死循环


# ---- 桩工具 ----
def get_weather(city: str) -> str:
    fake = {"北京": "晴，28°C", "上海": "多云，25°C"}
    return fake.get(city, f"{city}: 暂无数据")


def subtract(a: int, b: int) -> int:
    return a - b


# ---- 桩模型：模拟 ReAct 多轮决策（确定性）----
def model_turn(messages: list[dict], turn: int) -> dict:
    """按轮次给出确定性决策，复刻一个合理的 ReAct 推理过程。"""
    # 收集已有的工具结果
    tool_results = [m for m in messages if m["role"] == "tool"]

    if turn == 0:
        # 第 1 轮：分析任务，决定先查北京天气
        return {
            "kind": "tool_call",
            "thought": "要算温差，得先知道两地温度。先查北京。",
            "call": {"name": "get_weather", "args": {"city": "北京"}, "id": "call_1"},
        }
    if turn == 1:
        # 第 2 轮：北京有了，再查上海
        return {
            "kind": "tool_call",
            "thought": "北京 28°C。还差上海的温度。",
            "call": {"name": "get_weather", "args": {"city": "上海"}, "id": "call_2"},
        }
    if turn == 2:
        # 第 3 轮：两地温度齐了，算温差
        return {
            "kind": "tool_call",
            "thought": "北京 28°C、上海 25°C，现在算温差 28 - 25。",
            "call": {"name": "subtract", "args": {"a": 28, "b": 25}, "id": "call_3"},
        }
    # 第 4 轮：温差有了，给出最终答案
    return {
        "kind": "final",
        "thought": "温差是 3°C，可以回答了。",
        "content": "北京今天 28°C，上海 25°C，北京比上海高 3°C。",
    }


# ---- 手搓 ReAct 循环（对应文章里的 while 骨架）----
def run_react_loop(question: str) -> list[dict]:
    steps: list[dict] = []
    messages: list[dict] = [{"role": "user", "content": question}]

    for turn in range(MAX_TURNS):
        decision = model_turn(messages, turn)
        steps.append({"type": "thought", "content": f"[轮 {turn + 1}] {decision['thought']}"})

        if decision["kind"] == "tool_call":
            call = decision["call"]
            steps.append({
                "type": "tool_call",
                "toolName": call["name"],
                "content": f'{call["name"]}({", ".join(f"{k}={v!r}" for k, v in call["args"].items())})  # id={call["id"]}',
            })
            # 代码执行工具
            tool_fn = {"get_weather": get_weather, "subtract": subtract}[call["name"]]
            result = tool_fn(**call["args"])
            messages.append({
                "role": "tool",
                "content": str(result),
                "tool_call_id": call["id"],
            })
            steps.append({
                "type": "thought",
                "content": f"工具返回：{result}（作为 ToolMessage 回填进 messages）。",
            })
        else:
            steps.append({"type": "output", "content": decision["content"]})
            return steps

    # 走到这里说明达到循环上限仍未完成
    steps.append({"type": "error", "content": f"达到循环上限 {MAX_TURNS} 仍未完成。"})
    return steps


def build_trace() -> dict:
    steps = run_react_loop(QUESTION)
    return {
        "demoId": DEMO_ID,
        "variants": [
            {"id": "react", "label": "手搓 ReAct 多轮循环", "steps": steps},
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
