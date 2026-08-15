import Link from "next/link";
import { Header } from "@/components/Header";

export default function NotFound() {
  return (
    <div className="shell shell-narrow">
      <Header />
      <h1 className="m-0 text-[2.15rem] leading-[1.15]">Page not found</h1>
      <p className="mt-3 max-w-[42ch] text-ink-muted">
        That route is not part of the demo. Head back to the start or open the case list.
      </p>
      <p className="mt-6 flex flex-wrap gap-3">
        <Link className="btn btn-signal" href="/">
          Home
        </Link>
        <Link className="btn btn-ghost" href="/incidents">
          See past cases
        </Link>
      </p>
    </div>
  );
}
