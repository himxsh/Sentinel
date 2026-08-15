import Image from "next/image";
import Link from "next/link";

export function Header({ current }: { current?: "incidents" | "how" }) {
  return (
    <header className="topbar">
      <Link className="brand" href="/">
        <Image className="brand-mark" src="/sentinel.svg" alt="" width={28} height={28} unoptimized />
        Sentinel
      </Link>
      <nav className="nav">
        <Link href="/how" aria-current={current === "how" ? "page" : undefined}>
          How it works
        </Link>
        <Link href="/incidents" aria-current={current === "incidents" ? "page" : undefined}>
          Cases
        </Link>
      </nav>
    </header>
  );
}
