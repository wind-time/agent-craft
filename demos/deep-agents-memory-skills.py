"""生成「无记忆 Agent 每次从头 vs 有记忆+Skills 越用越聪明」对比型轨迹，供第 8 章回放。

用确定性桩对比两种 Agent 跨会话的表现：
- amnesia：无记忆，每次对话从头开始，用户偏好得每次重说，能力靠 system_prompt 写死。
- growing：有长期记忆（StoreBackend）+ Skills 能力包（Progressive Disclosure），

  会话1 记下用户偏好（edit_file 写 AGENTS.md）→ 会话2 启动自动加载偏好 + 按需加载 skill。

运行：
    python demos/deep-agents-memory-skills.py
无第三方依赖，无需 API key。
"""
from __future__ import annotations

import json
from pathlib import Path

# 配置
DEMO_ID = "deep-agents-memory-skills"
REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_PATH = REPO_ROOT / "public" / "demos" / f"{DEMO_ID}.trace.json"


# ---- 无记忆 Agent：每次从头 ----
def amnesia_steps() -> list[dict]:
    return [
        {"type": "thought",
         "content": "【会话 1】用户：「我喜欢 TypeScript，回复尽量简短。」Agent 回答了，但没记住——下次又得重说。"},
        {"type": "output",
         "content": "好的，记住了。（实际上什么也没存，进程结束就忘）"},
        {"type": "thought",
         "content": "【会话 2】用户：「给我写个 hello world。」Agent 不知道用户偏好 TypeScript，默认用 Python，还写了一大段解释。"},
        {"type": "output",
         "content": "好的，这是 Python 版的 hello world：print('Hello, World')……（附带 200 字解释）"},
        {"type": "error",
         "content": "❌ 偏好没记住，每次都从默认行为开始，用户得反复纠正。能力也只靠 system_prompt 写死，加新能力要改代码。",
         "note": "这是前 7 章所有 Agent 的通病：跑完就忘。"},
    ]


# ---- 有记忆 + Skills：越用越聪明 ----
def growing_steps() -> list[dict]:
    return [
        # 会话 1：用户告知偏好，Agent 用 edit_file 写进 AGENTS.md
        {"type": "thought",
         "content": "【会话 1】用户：「我喜欢 TypeScript，回复尽量简短。」MemoryMiddleware 引导 Agent：该写记忆了。"},
        {"type": "tool_call", "toolName": "edit_file",
         "content": 'edit_file(path="/memories/AGENTS.md", old="(待补充)", new="用户偏好：TypeScript，回复简短")  → 写入 StoreBackend'},
        {"type": "output",
         "content": "好的，已记下你的偏好。下次对话会自动用 TypeScript、回复简短。"},
        # 会话 2：启动自动加载记忆
        {"type": "thought",
         "content": "【会话 2】Agent 启动：MemoryMiddleware.before_agent 从 StoreBackend 下载 /memories/AGENTS.md，把内容塞进 system prompt 的 <agent_memory> 块。偏好自动生效。"},
        {"type": "output",
         "content": "（用户问 hello world）Agent 直接用 TypeScript、一句话回答：console.log('Hello, World')"},
        # Skills 按需加载
        {"type": "thought",
         "content": "【会话 2 续】用户问「怎么用 LangGraph 建状态图」。启动时只加载了 skill 的元数据（L1），现在 skill 被激活。"},
        {"type": "tool_call", "toolName": "read_file",
         "content": 'read_file(path="/skills/langgraph-docs/SKILL.md", limit=1000)  → L2：加载完整指令',
         "note": "Progressive Disclosure：L1 启动装元数据 → L2 用到才读指令 → L3 指令要才装资源"},
        {"type": "thought",
         "content": "SKILL.md 指令要求先 fetch 文档索引——agent 按指令执行（L3：按需加载 references/ 下的参考）。"},
        {"type": "output",
         "content": "基于 LangGraph 文档给出准确答案。整个过程中：偏好靠记忆自动生效、能力靠 skill 按需加载，主上下文始终干净。",
         "note": "记忆=启动全量加载的事实/偏好；Skills=按需加载的操作能力。两者互补，Agent 越用越聪明。"},
    ]


def build_trace() -> dict:
    return {
        "demoId": DEMO_ID,
        "variants": [
            {"id": "amnesia", "label": "无记忆 Agent（每次从头）", "steps": amnesia_steps()},
            {"id": "growing", "label": "记忆 + Skills（越用越聪明）", "steps": growing_steps()},
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
