"use client";

import { useEffect, useState } from "react";

export function toast(message: string) {
  window.dispatchEvent(new CustomEvent("sentinel-toast", { detail: message }));
}

export function ToastHost() {
  const [message, setMessage] = useState("");
  const [shown, setShown] = useState(false);

  useEffect(() => {
    let hide: number;
    function onToast(event: Event) {
      const detail = (event as CustomEvent<string>).detail;
      setMessage(detail);
      setShown(true);
      window.clearTimeout(hide);
      hide = window.setTimeout(() => setShown(false), 2800);
    }
    window.addEventListener("sentinel-toast", onToast);
    return () => {
      window.removeEventListener("sentinel-toast", onToast);
      window.clearTimeout(hide);
    };
  }, []);

  return (
    <div className={shown ? "toast show" : "toast"} role="status" aria-live="polite">
      {message}
    </div>
  );
}
