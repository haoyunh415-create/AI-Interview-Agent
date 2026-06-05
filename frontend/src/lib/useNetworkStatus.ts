"use client";

import { useEffect, useRef } from "react";
import toast from "react-hot-toast";

/**
 * Monitors online/offline status and shows toast notifications
 * when connectivity changes. Call once at the app root.
 */
export function useNetworkStatus() {
  const wasOffline = useRef(false);

  useEffect(() => {
    const handleOnline = () => {
      if (wasOffline.current) {
        toast.success("🌐 网络已恢复", { duration: 3000 });
        wasOffline.current = false;
      }
    };

    const handleOffline = () => {
      wasOffline.current = true;
      toast.error("🌐 网络连接已断开", { duration: Infinity });
    };

    window.addEventListener("online", handleOnline);
    window.addEventListener("offline", handleOffline);

    return () => {
      window.removeEventListener("online", handleOnline);
      window.removeEventListener("offline", handleOffline);
    };
  }, []);
}
