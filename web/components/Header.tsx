import Link from "next/link";

export function Header({ current }: { current?: "incidents" }) {
  return (
    <header className="topbar">
      <Link className="brand" href="/">
        Sentinel
      </Link>
      <nav className="nav">
        <Link href="/incidents" aria-current={current === "incidents" ? "page" : undefined}>
          Cases
        </Link>
      </nav>
    </header>
  );
}
