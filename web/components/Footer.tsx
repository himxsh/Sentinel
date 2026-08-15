import Link from "next/link";

export function Footer() {
  return (
    <footer className="site-footer">
      <p className="m-0 max-w-[62ch]">
        Sentinel is a live demo for the CockroachDB x AWS hackathon. The agent keeps cases, the trail, and the lessons
        in one CockroachDB cluster.
      </p>
      <p className="mt-3 m-0">
        <Link href="/how">How it works</Link>
        {" · "}
        <Link href="/incidents">Cases</Link>
      </p>
    </footer>
  );
}
