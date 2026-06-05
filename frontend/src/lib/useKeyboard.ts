"use client";

import { useEffect } from "react";

export interface Shortcut {
  key: string;
  ctrl?: boolean;
  shift?: boolean;
  handler: () => void;
  label: string;
}

export function useKeyboardShortcuts(shortcuts: Shortcut[]) {
  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      const pressedKey = (e.key || "").toLowerCase();
      if (!pressedKey) return;

      for (const s of shortcuts) {
        const needsCtrl = s.ctrl || false;
        const needsShift = s.shift || false;
        const hasCtrl = e.ctrlKey || e.metaKey;
        if (
          pressedKey === s.key.toLowerCase() &&
          hasCtrl === needsCtrl &&
          e.shiftKey === needsShift
        ) {
          e.preventDefault();
          s.handler();
          return;
        }
      }
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [shortcuts]);
}
