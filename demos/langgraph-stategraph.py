"""生成「手搓循环状态丢失 vs StateGraph 可恢复」对比型执行轨迹，供第 4 章回放。

用确定性桩模拟两种 Agent 执行同一个多轮任务（算两地温差），对比状态管理能力：
- bare-loop：模拟手搓 ReAct，跑到第 3 轮「进程崩溃」，内存里的 messages 全丢，只能从头再来。
- stategraph：模拟 StateGraph + InMemorySaver，跑到第 3 轮「中断」，用 thread_id 恢复续跑，
  并演示 get_state_history 列出全部 checkpoint、回到第 2 步 fork 重跑。

运行：
    python demos/langgraph-stategraph.py
无第三方依赖，无需 API key。
"""
from __future__ import annotations

import json
from pathlib import Path

# 配置
DEMO_ID = "langgraph-stategraph"
REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_PATH = REPO_ROOT / "public" / "demos" / f"{DEMO_ID}.trace.json"

QUESTION = "北京和上海今天温差多少度？"


def _weather(city: str) -> str:
    return {"北京": "晴，28°C", "上海": "多云，25°C"}[city]


# ---- 手搓循环：跑到第 3 轮崩溃，状态全丢 ----
def bare_loop_steps() -> list[dict]:
    return [
        {"type": "thought", "content": "[轮 1] 查北京天气。messages 列表现在 4 条，全在内存里。"},
        {"type": "tool_call", "toolName": "get_weather",
         "content": 'get_weather(city="北京")  → 晴，28°C'},
        {"type": "thought", "content": "[轮 2] 查上海天气。messages 现在 6 条，仍在内存。"},
        {"type": "tool_call", "toolName": "get_weather",
         "content": 'get_weather(city="上海")  → 多云，25°C'},
        {"type": "thought", "content": "[轮 3] 算温差 28-25。messages 8 条，准备调 subtract……"},
        {"type": "error",
         "content": "💥 进程崩溃：subtract 抛了 TypeError，异常没被捕获，循环挂了。",
         "note": "内存里的 messages 列表随进程一起消失。用户只能从头再问一遍，重新跑 3 轮、重新烧 token。"},
    ]


# ---- StateGraph + InMemorySaver：可中断恢复 + 时间旅行 ----
def stategraph_steps() -> list[dict]:
    return [
        # 正常跑前两轮，每步都被 Checkpointer 自动存档
        {"type": "thought",
         "content": "[轮 1] agent 节点 → 模型决定查北京。Checkpointer 自动存档 checkpoint-1。"},
        {"type": "tool_call", "toolName": "get_weather",
         "content": 'tools 节点 → get_weather(city="北京")  → 晴，28°C'},
        {"type": "thought",
         "content": "[轮 2] agent 节点 → 查上海。存档 checkpoint-2。"},
        {"type": "tool_call", "toolName": "get_weather",
         "content": 'tools 节点 → get_weather(city="上海")  → 多云，25°C'},
        # 第 3 轮「中断」——但状态已持久化
        {"type": "thought",
         "content": "[轮 3] 准备算温差……服务这时被重启了，进程退出。"},
        {"type": "error",
         "content": "⚠️ 进程中断。但与手搓循环不同：每个 checkpoint 都已落盘（InMemorySaver 演示用，生产换 PostgresSaver）。",
         "note": "messages 不会丢——它们存在 thread_id 对应的 checkpoint 链里。"},
        # 用 thread_id 恢复
        {"type": "thought",
         "content": "恢复：用同一个 thread_id 再次 invoke，Checkpointer 读回 checkpoint-2 的状态，从断点续跑。"},
        {"type": "tool_call", "toolName": "subtract",
         "content": 'tools 节点 → subtract(a=28, b=25)  → 3'},
        {"type": "output",
         "content": "agent 节点 → 北京今天 28°C，上海 25°C，北京比上海高 3°C。"},
        # 时间旅行
        {"type": "thought",
         "content": "时间旅行：get_state_history(thread_id) 列出全部 5 个 checkpoint，最新的在前。"},
        {"type": "tool_call", "toolName": "get_state_history",
         "content": "checkpoint-5(完成) → 4(subtract后) → 3(中断点) → 2(上海后) → 1(北京后)"},
        {"type": "thought",
         "content": "回到 checkpoint-2 fork：update_state 写入「把上海结果改成 多云，30°C」，生成新分支。"},
        {"type": "output",
         "content": "从 fork 点续跑：subtract(28, 30) → -2，得到不同结论「北京比上海低 2°C」。原 thread 不受影响。",
         "note": "这就是「时间旅行」——回到任意一步改输入重跑，探索 if-else，原对话完好。"},
    ]


def build_trace() -> dict:
    return {
        "demoId": DEMO_ID,
        "variants": [
            {"id": "bare", "label": "手搓循环（状态全丢）", "steps": bare_loop_steps()},
            {"id": "stategraph", "label": "StateGraph + Checkpointer", "steps": stategraph_steps()},
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
