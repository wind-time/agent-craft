/**
 * AgentDemoButton — 交互式文章的可运行 Agent Demo 占位组件
 *
 * 用法（在 .mdx 文章中）：
 *   import AgentDemoButton from "@/_interactive/AgentDemoButton.tsx";
 *   <AgentDemoButton demoId="hello-tool-call" label="运行：最小 Tool Call Demo" />
 *
 * 说明：
 * - 这是骨架占位。真实实现时，点击按钮应向后端 Agent 运行时发起请求，
 *   流式渲染返回的 trace（tool calls / 中间思考 / 最终输出）。
 * - 后端运行时方案见 docs/ARCHITECTURE.md「交互式文章运行时」一节。
 * - demoId 用于后端路由匹配对应的 Agent 脚本（见 demos/ 目录）。
 */
import { useState, useCallback } from "react";

type Props = {
  demoId: string;
  label?: string;
};

type TraceStep = {
  type: "tool_call" | "thought" | "output" | "error";
  content: string;
};

const STATUS = {
  idle: "点击运行",
  running: "运行中…",
  done: "运行完成",
  error: "运行失败",
} as const;

export default function AgentDemoButton({
  demoId,
  label = "运行 Demo",
}: Props) {
  const [status, setStatus] = useState<keyof typeof STATUS>("idle");
  const [trace, setTrace] = useState<TraceStep[]>([]);

  const run = useCallback(async () => {
    setStatus("running");
    setTrace([
      {
        type: "thought",
        content: `[骨架占位] demoId="${demoId}" 已触发。后端 Agent 运行时尚未接入，此处将展示真实 trace。`,
      },
    ]);
    // TODO: 接入后端运行时后，替换为真实 fetch + 流式渲染
    // const res = await fetch(`/api/agent/run`, { method: "POST", body: JSON.stringify({ demoId }) });
    // const reader = res.body!.getReader(); ... 逐 chunk 解析 trace 事件
    setTimeout(() => setStatus("done"), 400);
  }, [demoId]);

  return (
    <div className="not-prose my-6 rounded-lg border border-border bg-background p-4">
      <div className="flex items-center gap-3">
        <button
          onClick={run}
          disabled={status === "running"}
          className="rounded bg-accent px-3 py-1.5 text-sm font-medium text-accent-foreground transition-opacity disabled:opacity-50"
        >
          {label}
        </button>
        <span className="text-xs text-muted-foreground">{STATUS[status]}</span>
      </div>
      {trace.length > 0 && (
        <ul className="mt-3 space-y-1.5 text-sm">
          {trace.map((step, i) => (
            <li
              key={i}
              className="rounded border border-border bg-muted/40 px-2 py-1 font-mono text-xs"
            >
              <span className="mr-2 text-accent">[{step.type}]</span>
              {step.content}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
