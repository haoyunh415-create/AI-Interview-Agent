"use client";

import { useEffect, useState, useMemo } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import toast from "react-hot-toast";
import { getBookmarks, deleteBookmark } from "@/lib/api";
import { useBookmarkStore } from "@/stores/bookmarkStore";
import { CardSkeleton } from "@/components/ui/skeleton";
import { useTranslation } from "@/i18n";

export function BookmarksView() {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const bookmarks = useBookmarkStore((s) => s.bookmarks);
  const loading = useBookmarkStore((s) => s.loading);
  const setBookmarks = useBookmarkStore((s) => s.setBookmarks);
  const setLoading = useBookmarkStore((s) => s.setLoading);

  const [searchQuery, setSearchQuery] = useState("");
  const [selectedTopic, setSelectedTopic] = useState<string>("");
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());
  const [expandedIds, setExpandedIds] = useState<Set<number>>(new Set());
  const [sortBy, setSortBy] = useState<string>("newest");

  // React Query fetch
  const { data, isLoading } = useQuery({
    queryKey: ["bookmarks"],
    queryFn: () => getBookmarks("guest"),
    select: (res) => res.bookmarks,
  });

  useEffect(() => {
    if (data) setBookmarks(data);
  }, [data, setBookmarks]);

  // Delete single
  const deleteMutation = useMutation({
    mutationFn: (id: number) => deleteBookmark(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["bookmarks"] });
      toast.success(t("bookmarks.deleted"));
    },
    onError: () => {
      queryClient.invalidateQueries({ queryKey: ["bookmarks"] });
      toast.error(t("common.delete"));
    },
  });

  // Delete batch
  const batchDeleteMutation = useMutation({
    mutationFn: (ids: number[]) =>
      Promise.all(ids.map((id) => deleteBookmark(id))),
    onSuccess: (_, ids) => {
      queryClient.invalidateQueries({ queryKey: ["bookmarks"] });
      setSelectedIds(new Set());
      toast.success(t("bookmarks.batch_deleted", { count: ids.length }));
    },
    onError: () => toast.error("批量删除失败"),
  });

  const handleDelete = (id: number) => {
    setBookmarks(bookmarks.filter((b) => b.id !== id));
    deleteMutation.mutate(id);
  };

  const handleToggleExpand = (id: number) => {
    setExpandedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const handleToggleSelect = (id: number) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const handleSelectAll = () => {
    if (selectedIds.size === filtered.length) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(filtered.map((b) => b.id)));
    }
  };

  const handleBatchDelete = () => {
    if (selectedIds.size === 0) return;
    batchDeleteMutation.mutate(Array.from(selectedIds));
  };

  // Derive unique topics and tags from bookmarks
  const { topics, allTags } = useMemo(() => {
    const topicSet = new Set<string>();
    const tagSet = new Set<string>();
    bookmarks.forEach((b) => {
      if (b.topic) topicSet.add(b.topic);
      b.tags?.forEach((t) => tagSet.add(t));
    });
    return {
      topics: Array.from(topicSet).sort(),
      allTags: Array.from(tagSet).sort(),
    };
  }, [bookmarks]);

  // Filter bookmarks + sort
  const filtered = useMemo(() => {
    let result = bookmarks;
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      result = result.filter(
        (b) =>
          b.question.toLowerCase().includes(q) ||
          b.answer.toLowerCase().includes(q) ||
          b.topic?.toLowerCase().includes(q),
      );
    }
    if (selectedTopic) {
      result = result.filter((b) => b.topic === selectedTopic);
    }
    // Sort
    result = [...result].sort((a, b) => {
      switch (sortBy) {
        case "oldest":
          return (a.created_at || "").localeCompare(b.created_at || "");
        case "topic":
          return (a.topic || "zzz").localeCompare(b.topic || "zzz");
        case "stage":
          return (a.stage || "zzz").localeCompare(b.stage || "zzz");
        case "newest":
        default:
          return (b.created_at || "").localeCompare(a.created_at || "");
      }
    });
    return result;
  }, [bookmarks, searchQuery, selectedTopic, sortBy]);

  const hasSelection = selectedIds.size > 0;

  return (
    <div
      className="smooth-scroll"
      style={{
        maxWidth: "var(--content-max-width)",
        margin: "0 auto",
        width: "100%",
        padding: "24px 16px",
      }}
    >
      {/* Header */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: 16,
          flexWrap: "wrap",
          gap: 8,
        }}
      >
        <h2
          style={{
            fontSize: "1rem",
            fontWeight: 600,
            color: "var(--fg)",
            margin: 0,
          }}
        >
          ⭐ {t("bookmarks.title")}
          {bookmarks.length > 0 && (
            <span style={{ color: "var(--text-muted)", fontWeight: 400, marginLeft: 6 }}>
              ({bookmarks.length})
            </span>
          )}
        </h2>
        {bookmarks.length > 0 && (
          <button
            onClick={() => {
              const lines: string[] = [];
              lines.push("# 面试收藏题目\n");
              lines.push(`导出时间: ${new Date().toLocaleString()}\n`);
              lines.push(`共 ${filtered.length} 题\n`);
              lines.push("---\n");
              filtered.forEach((bm, i) => {
                lines.push(`## ${i + 1}. ${bm.question}\n`);
                if (bm.answer) lines.push(`**答案:** ${bm.answer}\n`);
                if (bm.topic) lines.push(`- 主题: ${bm.topic}`);
                if (bm.stage) lines.push(` / 阶段: ${bm.stage}`);
                if (bm.tags?.length) lines.push(` / 标签: ${bm.tags.filter(Boolean).join(", ")}`);
                lines.push(`\n_收藏时间: ${bm.created_at || ""}_\n`);
                lines.push("---\n");
              });
              const blob = new Blob([lines.join("\n")], { type: "text/markdown;charset=utf-8" });
              const url = URL.createObjectURL(blob);
              const a = document.createElement("a");
              a.href = url;
              a.download = `面试收藏_${new Date().toISOString().slice(0, 10)}.md`;
              a.click();
              URL.revokeObjectURL(url);
              toast.success("导出成功");
            }}
            className="btn-ghost"
            style={{ padding: "6px 12px", fontSize: "0.78rem" }}
          >
            📤 导出
          </button>
        )}
      </div>

      {/* Search + Filter bar */}
      <div
        style={{
          display: "flex",
          gap: 8,
          marginBottom: 12,
          flexWrap: "wrap",
          alignItems: "center",
        }}
      >
        {/* Search */}
        <div style={{ flex: 1, minWidth: 180, position: "relative" }}>
          <span
            style={{
              position: "absolute",
              left: 10,
              top: "50%",
              transform: "translateY(-50%)",
              fontSize: "0.85rem",
              color: "var(--text-muted)",
              pointerEvents: "none",
            }}
          >
            🔍
          </span>
          <input
            placeholder={t("bookmarks.search")}
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="input-base"
            style={{
              width: "100%",
              padding: "8px 10px 8px 32px",
              fontSize: "0.85rem",
            }}
          />
        </div>

        {/* Topic filter */}
        {topics.length > 0 && (
          <select
            value={selectedTopic}
            onChange={(e) => setSelectedTopic(e.target.value)}
            className="input-base"
            style={{
              padding: "8px 10px",
              fontSize: "0.82rem",
              cursor: "pointer",
              minWidth: 100,
            }}
          >
            <option value="">{t("bookmarks.all_topics")}</option>
            {topics.map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
        )}

        {/* Sort */}
        <select
          value={sortBy}
          onChange={(e) => setSortBy(e.target.value)}
          className="input-base"
          style={{
            padding: "8px 10px",
            fontSize: "0.82rem",
            cursor: "pointer",
            minWidth: 90,
          }}
        >
          <option value="newest">最新优先</option>
          <option value="oldest">最早优先</option>
          <option value="topic">按主题</option>
          <option value="stage">按阶段</option>
        </select>
      </div>

      {/* Batch actions */}
      {bookmarks.length > 0 && (
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 8,
            marginBottom: 8,
            fontSize: "0.82rem",
          }}
        >
          <label
            style={{
              display: "flex",
              alignItems: "center",
              gap: 4,
              cursor: "pointer",
              color: "var(--text-secondary)",
            }}
          >
            <input
              type="checkbox"
              checked={hasSelection && selectedIds.size === filtered.length}
              onChange={handleSelectAll}
              style={{ accentColor: "var(--primary)", cursor: "pointer" }}
            />
            {t("bookmarks.select_all")}
          </label>
          {hasSelection && (
            <>
              <span style={{ color: "var(--text-muted)" }}>
                {t("bookmarks.selected", { count: selectedIds.size })}
              </span>
              <button
                onClick={handleBatchDelete}
                disabled={batchDeleteMutation.isPending}
                className="btn-ghost"
                style={{
                  padding: "4px 10px",
                  color: "var(--danger)",
                  borderColor: "var(--danger-soft)",
                  fontSize: "0.78rem",
                }}
              >
                {t("bookmarks.delete_selected")}
              </button>
            </>
          )}
        </div>
      )}

      {/* Loading */}
      {(isLoading || loading) && bookmarks.length === 0 && (
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          {Array.from({ length: 3 }).map((_, i) => (
            <CardSkeleton key={i} lines={2} />
          ))}
        </div>
      )}

      {/* Empty state */}
      {!isLoading && bookmarks.length === 0 && (
        <div className="empty-state animate-fade-in" style={{ padding: "60px 20px" }}>
          <div style={{ fontSize: "2.5rem", opacity: 0.5 }}>⭐</div>
          <div style={{ color: "var(--text-muted)", fontSize: "0.9rem" }}>
            {t("bookmarks.empty")}
          </div>
        </div>
      )}

      {/* No results for search */}
      {bookmarks.length > 0 && filtered.length === 0 && !isLoading && (
        <div className="empty-state animate-fade-in" style={{ padding: "40px 20px" }}>
          <div style={{ color: "var(--text-muted)", fontSize: "0.9rem" }}>
            {t("bookmarks.no_results")}
          </div>
        </div>
      )}

      {/* List */}
      <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
        {filtered.map((bm, i) => (
          <div
            key={bm.id}
            className="card-base animate-slide-in-up"
            style={{
              padding: "14px 16px",
              animationDelay: `${i * 30}ms`,
              animationFillMode: "backwards",
              display: "flex",
              gap: 10,
              alignItems: "flex-start",
            }}
          >
            {/* Checkbox */}
            <label
              style={{
                marginTop: 2,
                cursor: "pointer",
                flexShrink: 0,
              }}
              onClick={(e) => e.stopPropagation()}
            >
              <input
                type="checkbox"
                checked={selectedIds.has(bm.id)}
                onChange={() => handleToggleSelect(bm.id)}
                style={{ accentColor: "var(--primary)", cursor: "pointer", width: 16, height: 16 }}
              />
            </label>

            <div style={{ flex: 1, minWidth: 0 }}>
              {/* Question — clickable to toggle answer */}
              <div
                onClick={() => handleToggleExpand(bm.id)}
                style={{
                  fontSize: "0.9rem",
                  lineHeight: 1.7,
                  color: "var(--fg)",
                  marginBottom: expandedIds.has(bm.id) && bm.answer ? 6 : 10,
                  wordBreak: "break-word",
                  cursor: bm.answer ? "pointer" : "default",
                }}
              >
                {bm.question}
              </div>

              {/* Answer — expandable */}
              {bm.answer && expandedIds.has(bm.id) && (
                <div
                  className="animate-fade-in"
                  style={{
                    fontSize: "0.85rem",
                    lineHeight: 1.7,
                    color: "var(--text-secondary)",
                    padding: "8px 12px",
                    marginBottom: 10,
                    background: "var(--card-hover)",
                    borderRadius: "var(--radius-sm)",
                    borderLeft: "3px solid var(--primary-soft)",
                    wordBreak: "break-word",
                    whiteSpace: "pre-wrap",
                  }}
                >
                  <div style={{ fontSize: "0.7rem", fontWeight: 600, color: "var(--primary-text)", marginBottom: 4 }}>
                    📝 {t("bookmarks.show_answer")}
                  </div>
                  {bm.answer}
                </div>
              )}

              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  flexWrap: "wrap",
                  gap: 4,
                }}
              >
                <div style={{ display: "flex", gap: 6, alignItems: "center", flexWrap: "wrap" }}>
                  <span className="tag tag-muted" style={{ fontSize: "0.72rem" }}>
                    {bm.topic || t("common.general")}
                  </span>
                  {bm.tags?.length > 0 &&
                    bm.tags.slice(0, 3).map((t, j) => (
                      <span key={j} className="tag tag-primary" style={{ fontSize: "0.72rem" }}>
                        {t}
                      </span>
                    ))}
                  <span style={{ fontSize: "0.7rem", color: "var(--text-dim)" }}>
                    {bm.created_at?.slice(0, 10)}
                  </span>
                  {bm.answer && (
                    <button
                      onClick={() => handleToggleExpand(bm.id)}
                      className="btn-ghost"
                      style={{
                        padding: "2px 6px",
                        fontSize: "0.68rem",
                        borderColor: "transparent",
                        color: "var(--primary-text)",
                      }}
                    >
                      {expandedIds.has(bm.id) ? "🔼 " + t("bookmarks.hide_answer") : "🔽 " + t("bookmarks.show_answer")}
                    </button>
                  )}
                </div>
                <button
                  onClick={() => handleDelete(bm.id)}
                  className="btn-ghost"
                  style={{
                    padding: "4px 10px",
                    color: "var(--danger)",
                    borderColor: "var(--danger-soft)",
                    fontSize: "0.78rem",
                    flexShrink: 0,
                  }}
                >
                  {t("common.delete")}
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>

      {filtered.length > 0 && bookmarks.length > 0 && (
        <div
          style={{
            textAlign: "center",
            padding: "12px 0",
            fontSize: "0.78rem",
            color: "var(--text-dim)",
          }}
        >
          {t("bookmarks.showing", { shown: filtered.length, total: bookmarks.length })}
        </div>
      )}
    </div>
  );
}
