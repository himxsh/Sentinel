"use client";

import { ReactLenis, useLenis } from "lenis/react";
import { usePathname } from "next/navigation";
import { useEffect } from "react";

function ResetScroll() {
  const pathname = usePathname();
  const lenis = useLenis();

  useEffect(() => {
    lenis?.scrollTo(0, { immediate: true });
  }, [pathname, lenis]);

  return null;
}

export function SmoothScroll() {
  return (
    <>
      <ReactLenis root options={{ stopInertiaOnNavigate: true }} />
      <ResetScroll />
    </>
  );
}
