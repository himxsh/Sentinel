import Image from "next/image";
import Link from "next/link";
import { FireAlertButton } from "@/components/FireAlertButton";
import { Header } from "@/components/Header";

const STEPS = [
  {
    title: "An alert comes in",
    body: "Sentinel opens a case and writes it down so the work is not stuck in a chat window.",
  },
  {
    title: "It checks past cases",
    body: "Similar problems and the fixes that worked are pulled from memory before anyone guesses.",
  },
  {
    title: "It files what it did",
    body: "The next alert starts with that lesson already in hand, even if a database node went down in between.",
  },
];

export default function Home() {
  return (
    <div className="shell">
      <Header />
      <main className="grid items-center gap-10 lg:grid-cols-[minmax(0,1fr)_minmax(0,0.92fr)] lg:gap-16">
        <div className="rise min-h-0 pt-4 lg:pt-8">
          <h1 className="m-0 max-w-[14ch] text-[clamp(2.5rem,8vw,4.25rem)] font-semibold leading-[1.05] tracking-[-0.03em]">
            The on-call that remembers.
          </h1>
          <p className="mt-5 max-w-[38ch] text-[1.125rem] text-ink-muted">
            When a database gets sick, Sentinel opens a case, checks what worked last time, and files what it did.
          </p>
          <div className="mt-7 flex flex-wrap gap-3">
            <FireAlertButton />
            <Link className="btn btn-ghost" href="/incidents">
              See past cases
            </Link>
          </div>
        </div>

        <figure className="rise m-0 overflow-hidden rounded-lg border border-line bg-surface">
          <Image
            src="/watch-floor.png"
            alt="A quiet data-center aisle with teal status lights on the racks"
            width={1600}
            height={900}
            priority
            className="h-auto w-full object-cover"
          />
        </figure>
      </main>

      <ol className="mt-20 max-w-[62ch] border-t border-line pt-10">
        {STEPS.map((step, index) => (
          <li key={step.title} className="grid gap-2 border-b border-line py-6 md:grid-cols-[4.5rem_1fr] md:gap-8">
            <p className="m-0 font-mono text-[0.78rem] font-semibold uppercase tracking-wide text-signal-ink">
              {String(index + 1).padStart(2, "0")}
            </p>
            <div>
              <h2 className="m-0 text-xl font-semibold tracking-[-0.02em]">{step.title}</h2>
              <p className="mt-2 text-ink-muted">{step.body}</p>
            </div>
          </li>
        ))}
      </ol>

      <p className="mt-16 max-w-[62ch] text-ink-muted">
        Every case, decision, and lesson lives in one CockroachDB cluster. Kill a node mid-incident and the agent still
        has its memory.
      </p>
    </div>
  );
}
