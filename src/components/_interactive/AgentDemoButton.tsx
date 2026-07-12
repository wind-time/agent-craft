/**
 * AgentDemoButton — 交互式文章的可运行 Agent Demo 组件
 *
 * 用法（在 .mdx 文章中）：
 *   import AgentDemoButton from "@/components/_interactive/AgentDemoButton.tsx";
 *   <AgentDemoButton demoId="llm-vs-agent" label="运行：裸 LLM vs. Agent 循环" />
 *
 * 点击后从 `${BASE_URL}demos/${demoId}.trace.json` 拉取预录的执行轨迹，
 * 支持单轨迹（顶层 steps）与多轨迹对比（variants），逐条以 delayMs 间隔「流式」渲染。
 * 拉取失败时显示降级提示，不报错、不影响文章阅读。
 */
import { useCallback, useEffect, useRef, useState } from "react";

type Props = {
  demoId: string;
  label?: string;
  delayMs?: number;
};

type TraceStep = {
  type: "tool_call" | "thought" | "output" | "error";
  content: string;
  toolName?: string;
  note?: string;
};

type TraceVariant = {
  id: string;
  label: string;
  steps: TraceStep[];
};

// 顶层 steps（单轨迹）或 variants（多轨迹对比）皆可
type TraceFile = {
  demoId?: string;
  steps?: TraceStep[];
  variants?: TraceVariant[];
};

const STATUS = {
  idle: "点击运行",
  running: "运行中…",
  done: "运行完成",
  error: "运行失败",
} as const;

const TYPE_META: Record<TraceStep["type"], { label: string; chip: string }> = {
  thought: { label: "思考", chip: "bg-muted text-muted-foreground" },
  tool_call: { label: "工具调用", chip: "bg-accent/15 text-accent" },
  output: { label: "输出", chip: "bg-accent text-accent-foreground" },
  error: {
    label: "错误",
    chip: "bg-red-500/15 text-red-600 dark:text-red-400",
  },
};

const PLACEHOLDER_VARIANTS = (demoId: string): TraceVariant[] => [
  {
    id: "placeholder",
    label: "加载失败",
    steps: [
      {
        type: "thought",
        content: `未能加载该 Demo 的执行轨迹（${demoId}）。可稍后重试，或直接阅读下文文字说明。`,
      },
    ],
  },
];

/** 拉取并归一化执行轨迹；失败返回 null（由调用方降级提示）。 */
async function loadTrace(demoId: string): Promise<TraceVariant[] | null> {
  // BASE_URL 兼容子路径部署（如 用户名.github.io/agent-craft/）
  const url = `${import.meta.env.BASE_URL}demos/${demoId}.trace.json`;
  try {
    const res = await fetch(url);
    if (!res.ok) return null;
    const data = (await res.json()) as TraceFile;
    if (Array.isArray(data.variants) && data.variants.length > 0) {
      return data.variants.filter(v => Array.isArray(v.steps));
    }
    if (Array.isArray(data.steps) && data.steps.length > 0) {
      return [{ id: "default", label: "执行轨迹", steps: data.steps }];
    }
    return null;
  } catch {
    return null;
  }
}

export default function AgentDemoButton({
  demoId,
  label = "运行 Demo",
  delayMs = 450,
}: Props) {
  const [status, setStatus] = useState<keyof typeof STATUS>("idle");
  const [variants, setVariants] = useState<TraceVariant[] | null>(null);
  const [revealed, setRevealed] = useState<number[]>([]);
  const [isPlaceholder, setIsPlaceholder] = useState(false);
  const timers = useRef<number[]>([]);

  const clearTimers = useCallback(() => {
    timers.current.forEach(t => clearTimeout(t));
    timers.current = [];
  }, []);

  useEffect(() => () => clearTimers(), [clearTimers]);

  // 逐条「流式」回放：每个轨迹并行推进，每 tick 各露出下一步
  const stream = useCallback(
    (v: TraceVariant[]) => {
      clearTimers();
      const maxLen = Math.max(1, ...v.map(vr => vr.steps.length));
      // 立即露出每个轨迹的第一步，后续按 delayMs 逐条推进
      setRevealed(v.map(vr => Math.min(1, vr.steps.length)));
      let tick = 1;
      const step = () => {
        if (tick >= maxLen) {
          setStatus("done");
          return;
        }
        setRevealed(prev =>
          v.map((vr, i) => Math.min((prev[i] ?? 0) + 1, vr.steps.length))
        );
        tick += 1;
        timers.current.push(window.setTimeout(step, delayMs));
      };
      timers.current.push(window.setTimeout(step, delayMs));
    },
    [clearTimers, delayMs]
  );

  const run = useCallback(async () => {
    setStatus("running");
    setIsPlaceholder(false);
    // 首次运行或上次降级时，重新拉取；否则复用已加载轨迹做回放
    let v = variants;
    if (!v || isPlaceholder) {
      v = await loadTrace(demoId);
      if (!v) {
        const ph = PLACEHOLDER_VARIANTS(demoId);
        setVariants(ph);
        setRevealed(ph.map(vr => vr.steps.length));
        setIsPlaceholder(true);
        setStatus("done");
        return;
      }
      setVariants(v);
    }
    stream(v);
  }, [demoId, variants, isPlaceholder, stream]);

  return (
    <div className="not-prose my-6 rounded-lg border border-border bg-background p-4">
      <div className="flex flex-wrap items-center gap-3">
        <button
          onClick={run}
          disabled={status === "running"}
          className="rounded bg-accent px-3 py-1.5 text-sm font-medium text-accent-foreground transition-opacity disabled:opacity-50"
        >
          {label}
        </button>
        <span className="text-xs text-muted-foreground">
          {isPlaceholder ? "加载失败" : STATUS[status]}
        </span>
      </div>

      {variants && variants.length > 0 && (
        <div
          className={
            variants.length >= 2
              ? "mt-3 grid grid-cols-1 gap-4 md:grid-cols-2"
              : "mt-3 grid grid-cols-1 gap-4"
          }
        >
          {variants.map((vr, i) => {
            const count = revealed[i] ?? 0;
            const visible = vr.steps.slice(0, count);
            const streaming = status === "running" && count < vr.steps.length;
            return (
              <div
                key={vr.id}
                className="rounded-md border border-border bg-muted/20 p-2.5"
              >
                <div className="mb-2 text-xs font-medium text-muted-foreground">
                  {vr.label}
                </div>
                <ul className="space-y-1.5">
                  {visible.map((step, j) => {
                    const meta = TYPE_META[step.type];
                    return (
                      <li
                        key={j}
                        className="rounded border border-border bg-background px-2.5 py-1.5 font-mono text-xs"
                      >
                        <div className="mb-0.5 flex items-center gap-1.5">
                          <span
                            className={`rounded px-1.5 py-0.5 text-[10px] font-semibold ${meta.chip}`}
                          >
                            {meta.label}
                          </span>
                          {step.toolName && (
                            <span className="text-muted-foreground">
                              → {step.toolName}
                            </span>
                          )}
                        </div>
                        <div className="whitespace-pre-wrap break-words text-foreground">
                          {step.content}
                        </div>
                        {step.note && (
                          <div className="mt-1 text-[11px] text-muted-foreground">
                            注：{step.note}
                          </div>
                        )}
                      </li>
                    );
                  })}
                  {streaming && (
                    <li
                      className="inline-block animate-pulse font-mono text-xs text-accent"
                      aria-hidden="true"
                    >
                      ▍
                    </li>
                  )}
                </ul>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
