"""生成「无工具瞎答 vs 有工具正确调用」对比型执行轨迹，供第 2 章交互式按钮回放。

用确定性桩模拟 LangChain 1.x 的 tool call 闭环，保证回放稳定可复现：
- baseline：模拟未 bind_tools 的模型，遇到需要实时信息的问题直接瞎编。
- agent：模拟 bind_tools 后的模型——先输出 tool_calls，代码执行工具拿到真实结果，
  再基于结果给出有依据的答案。完整复刻文章里的单轮 tool call 闭环。

运行：
    python demos/langchain-foundation.py
无第三方依赖，无需 API key。
"""
from __future__ import annotations

import json
from pathlib import Path

# 配置
DEMO_ID = "langchain-foundation"
REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_PATH = REPO_ROOT / "public" / "demos" / f"{DEMO_ID}.trace.json"

QUESTION = "北京今天天气怎么样？"
WEATHER_RESULT = "晴，28°C，北风 3 级"


# ---- 桩工具 ----
def get_weather(city: str) -> str:
    # 真实场景换成联网 / 数据库查询
    return WEATHER_RESULT


# ---- 桩模型：未 bind_tools，直接生成文字（会瞎编）----
def bare_model_answer(question: str) -> str:
    # 没有工具，凭参数生成一段像答案的文字
    return "北京今天晴，气温约 20°C。"


# ---- 桩模型：bind_tools 后的单轮决策 ----
def model_with_tools_step(messages: list[dict], turn: int) -> dict:
    """第 0 轮输出 tool_calls；之后基于工具结果给出最终答案。"""
    if turn == 0:
        return {
            "kind": "tool_calls",
            "calls": [
                {"name": "get_weather", "args": {"city": "北京"}, "id": "call_1"}
            ],
        }
    # 找到工具返回结果，基于它作答
    return {"kind": "final", "content": f"北京今天{WEATHER_RESULT}。适合户外活动。"}


# ---- 单轮 tool call 闭环（对应文章三步法）----
def run_tool_call_loop(question: str) -> list[dict]:
    steps: list[dict] = []
    messages: list[dict] = [{"role": "user", "content": question}]

    # 第 0 轮：模型输出 tool_calls
    decision = model_with_tools_step(messages, 0)
    steps.append({
        "type": "thought",
        "content": "模型识别出需要实时天气信息，决定调用 get_weather 工具，而非直接编造答案。",
    })
    for call in decision["calls"]:
        steps.append({
            "type": "tool_call",
            "toolName": call["name"],
            "content": f'{call["name"]}(city="{call["args"]["city"]}")  # tool_call_id={call["id"]}',
        })

    # 代码执行工具，构造 ToolMessage 塞回 messages
    for call in decision["calls"]:
        result = get_weather(call["args"]["city"])
        messages.append({"role": "tool", "content": result, "tool_call_id": call["id"]})
        steps.append({
            "type": "thought",
            "content": f"代码执行 {call['name']} → 返回：「{result}」，作为 ToolMessage 回填进 messages。",
        })

    # 第 1 轮：模型基于工具结果给出最终答案
    final = model_with_tools_step(messages, 1)
    steps.append({"type": "output", "content": final["content"]})
    return steps


def build_trace() -> dict:
    baseline_steps = [
        {
            "type": "thought",
            "content": "模型未绑定工具，遇到「北京今天天气」只能凭训练数据概率生成一段文字。",
        },
        {
            "type": "output",
            "content": bare_model_answer(QUESTION),
            "note": "无数据依据，模型概率生成——气温、天气都可能完全错误。",
        },
    ]
    agent_steps = run_tool_call_loop(QUESTION)
    return {
        "demoId": DEMO_ID,
        "variants": [
            {"id": "bare", "label": "未绑定工具的模型", "steps": baseline_steps},
            {"id": "with-tools", "label": "bind_tools 后的模型", "steps": agent_steps},
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
