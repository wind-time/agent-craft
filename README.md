# Agent Craft

> 记录 Agent 开发实战与思考的技术博客。文章不只是文字，关键篇章还嵌可运行的 Agent Demo。

[![Astro](https://img.shields.io/badge/Astro-7-FF5D01?logo=astro&logoColor=white)](https://astro.build/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind-4-06B6D4?logo=tailwindcss&logoColor=white)](https://tailwindcss.com/)
[![License: MIT](https://img.shields.io/badge/代码-MIT-black)](./LICENSE)
[![Content: CC BY-NC-SA 4.0](https://img.shields.io/badge/内容-CC%20BY--NC--SA%204.0-lightgrey)](https://creativecommons.org/licenses/by-nc-sa/4.0/deed.zh)

## 这是什么

**Agent Craft** 是一个聚焦 Agent 开发实战的中文技术博客。内容围绕如何基于 LLM 构建真正可用的 Agent——模型调用、工具编排、任务规划、记忆系统、生产级部署。

站点基于 [AstroPaper](https://github.com/satnaing/astro-paper) 主题二次开发，用 [Astro](https://astro.build/) + [Tailwind CSS](https://tailwindcss.com/) 构建。

## 特色：交互式文章

不只是纯文字。关键篇章会嵌入 **可真实运行的 Agent Demo**，读者在文章里直接点按钮就能看到 Agent 的执行轨迹（tool calls、中间思考、最终输出）。

## 本地开发

环境要求：**Node.js ≥ 22.12.0**

```bash
# 安装依赖
npm install

# 启动开发服务器
npm run dev
# 访问 http://localhost:4321

# 构建生产版本
npm run build

# 预览构建产物
npm run preview
```

## 项目结构

```
agent-craft/
├── src/
│   ├── content/
│   │   ├── posts/         # 文章正文（.md / .mdx）
│   │   └── pages/         # 静态页（about 等）
│   ├── components/
│   │   └── _interactive/  # 交互式 React 组件（用于 .mdx 文章）
│   ├── layouts/           # 页面布局
│   ├── pages/             # 路由
│   ├── styles/            # 全局样式与主题色
│   └── i18n/lang/zh.ts    # 中文 UI 文案
├── astro-paper.config.ts  # 站点元数据
└── astro.config.ts        # Astro 主配置
```

## 写作

- 普通文章：在 `src/content/posts/` 下新建 `.md`
- 交互式文章：用 `.mdx`，import `AgentDemoButton` 组件

## 协议

- 文字内容：[CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/deed.zh)
- 站点源代码：[MIT](./LICENSE)

## 致谢

基于 [AstroPaper](https://github.com/satnaing/astro-paper) 主题（作者 [Sat Naing](https://github.com/satnaing)），按 MIT 协议使用与改造。
