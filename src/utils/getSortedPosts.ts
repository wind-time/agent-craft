import type { CollectionEntry } from "astro:content";
import { postFilter } from "./postFilter";

/**
 * Returns posts that are eligible to be shown to users.
 *
 * 排序规则（支持多专题）：
 * 1. 先按 series（专题）分组，同专题内按 chapter 升序，保证系列文「上一篇/下一篇」
 *    严格按章节顺序导航，不依赖 pubDatetime（多篇文章同日发布时日期排序会乱序）。
 * 2. 专题之间按「该专题第一章的 pubDatetime」升序排（先开的专题排前）。
 * 3. 没标 chapter 的单篇回退日期降序，排在所属专题的系列文之后。
 *
 * Note: filtering respects drafts and scheduled posts via `postFilter()`.
 */
export function getSortedPosts(posts: CollectionEntry<"posts">[]) {
  const filtered = posts.filter(postFilter);

  // 专题 -> 该专题第一章的 pubDatetime（用于专题间排序）
  const seriesFirstPub: Record<string, number> = {};
  for (const p of filtered) {
    const s = p.data.series;
    const t = new Date(p.data.pubDatetime).getTime();
    if (!(s in seriesFirstPub) || t < seriesFirstPub[s]) {
      seriesFirstPub[s] = t;
    }
  }

  return filtered.sort((a, b) => {
    const sa = a.data.series;
    const sb = b.data.series;
    // 不同专题：按各自第一章发布时间升序
    if (sa !== sb) {
      return (seriesFirstPub[sa] ?? 0) - (seriesFirstPub[sb] ?? 0);
    }
    // 同专题内：
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
