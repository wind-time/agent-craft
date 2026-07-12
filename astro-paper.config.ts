import { defineAstroPaperConfig } from "./src/types/config";

export default defineAstroPaperConfig({
  site: {
    // TODO 部署前替换为你的 GitHub Pages 地址，例如 https://<你的用户名>.github.io/agent-craft/
    url: "https://wind-time.github.io/agent-craft/",
    title: "Agent Craft",
    description: "一个记录 Agent 开发实战与思考的技术博客。",
    author: "北北",
    profile: "https://github.com/wind-time",
    ogImage: "default-og.jpg",
    lang: "zh",
    timezone: "Asia/Shanghai",
    dir: "ltr",
  },
  posts: {
    perPage: 8,
    perIndex: 6,
    scheduledPostMargin: 15 * 60 * 1000,
  },
  features: {
    lightAndDarkMode: true,
    dynamicOgImage: true,
    showArchives: true,
    showBackButton: true,
    editPost: {
      enabled: true,
      // TODO 替换为你的仓库地址
      url: "https://github.com/wind-time/agent-craft/edit/main/",
    },
    search: "pagefind",
  },
  socials: [
    // TODO 替换为你的社交链接；不需要的整行删除即可
    { name: "github", url: "https://github.com/wind-time" },
  ],
  shareLinks: [
    { name: "x", url: "https://x.com/intent/post?url=" },
    { name: "telegram", url: "https://t.me/share/url?url=" },
    { name: "mail", url: "mailto:?subject=来自 Agent Craft 的文章&body=" },
  ],
});
