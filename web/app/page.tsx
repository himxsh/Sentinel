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
      <main className="grid min-h-[min(72dvh,40rem)] items-center gap-10 lg:grid-cols-[minmax(0,1.05fr)_minmax(0,0.95fr)] lg:gap-16">
        <div className="rise min-h-0 pt-2 lg:pt-4">
          <h1 className="m-0 max-w-[13ch] text-[clamp(2.75rem,8vw,4.75rem)] leading-[1.12] tracking-[-0.02em]">
            The on-call that <em className="italic">remembers</em>.
          </h1>
          <p className="mt-5 max-w-[38ch] text-[1.125rem] text-ink-muted">
            When a database gets sick, Sentinel opens a case, checks what worked last time, and files what it did.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <FireAlertButton />
            <Link className="btn btn-ghost" href="/incidents">
              See past cases
            </Link>
          </div>
        </div>

        <figure className="hero-frame rise m-0">
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

      <ol className="mt-20 max-w-[62ch] border-t border-line pt-4">
        {STEPS.map((step, index) => (
          <li key={step.title} className="grid gap-2 border-b border-line py-7 md:grid-cols-[4.5rem_1fr] md:gap-8">
            <p className="m-0 font-mono text-[0.78rem] font-semibold text-signal-ink">
              {String(index + 1).padStart(2, "0")}
            </p>
            <div>
              <h2 className="m-0 text-[1.65rem] leading-[1.15]">{step.title}</h2>
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
