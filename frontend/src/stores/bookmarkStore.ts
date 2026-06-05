"use client";

import { create } from "zustand";
import type { Bookmark } from "@/lib/api";

interface BookmarkState {
  bookmarks: Bookmark[];
  loading: boolean;
  setBookmarks: (bookmarks: Bookmark[]) => void;
  setLoading: (loading: boolean) => void;
  reset: () => void;
}

export const useBookmarkStore = create<BookmarkState>((set) => ({
  bookmarks: [],
  loading: false,
  setBookmarks: (bookmarks) => set({ bookmarks }),
  setLoading: (loading) => set({ loading }),
  reset: () => set({ bookmarks: [], loading: false }),
}));
