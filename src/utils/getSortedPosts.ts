import type { CollectionEntry } from "astro:content";
import { postFilter } from "./postFilter";

/**
 * Returns posts that are eligible to be shown to users, sorted by chapter order
 * (ascending) when present; otherwise falls back to “last updated” descending
 * (uses `modDatetime` when present, otherwise `pubDatetime`).
 *
 * 章节顺序优先：有 chapter 字段的文章按章号升序排在前，保证系列文「上一篇/下一篇」
 * 严格按章节顺序导航，不依赖 pubDatetime（多篇文章同日发布时日期排序会乱序）。
 * 没标 chapter 的文章（如非系列的单篇）回退到日期降序，排在系列文章之后。
 *
 * Note: filtering respects drafts and scheduled posts via `postFilter()`.
 */
export function getSortedPosts(posts: CollectionEntry<"posts">[]) {
  return posts
    .filter(postFilter)
    .sort((a, b) => {
      const ca = a.data.chapter;
      const cb = b.data.chapter;
      // 两侧都有 chapter：按章号升序
      if (ca != null && cb != null) return ca - cb;
      // 仅一侧有 chapter：有 chapter 的排前
      if (ca != null) return -1;
      if (cb != null) return 1;
      // 都没 chapter：回退日期降序（原行为）
      return (
        Math.floor(
          new Date(b.data.modDatetime ?? b.data.pubDatetime).getTime() / 1000
        ) -
        Math.floor(
          new Date(a.data.modDatetime ?? a.data.pubDatetime).getTime() / 1000
        )
      );
    });
}
