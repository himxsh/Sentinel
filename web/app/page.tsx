import Image from "next/image";
import Link from "next/link";
import { FireAlertButton } from "@/components/FireAlertButton";
import { Header } from "@/components/Header";
import { api } from "@/lib/api";
import { DEMO_FACTS, GUARDS, MEMORY, STEPS } from "@/lib/copy";
import { fmtTs, shortId, statusLabel } from "@/lib/format";
import type { IncidentSummary } from "@/lib/types";

export const dynamic = "force-dynamic";

export default async function Home() {
  let recent: IncidentSummary[] = [];
  let recentError: string | null = null;
  try {
    const all = await api<IncidentSummary[]>("/api/incidents");
    recent = all.slice(0, 5);
  } catch (caught) {
    recentError = caught instanceof Error ? caught.message : "Could not load cases.";
  }

  return (
    <div className="shell">
      <Header />
      <main className="grid min-h-[min(68dvh,38rem)] items-center gap-10 lg:grid-cols-[minmax(0,1.05fr)_minmax(0,0.95fr)] lg:gap-16">
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
              Cases
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

      <section className="mt-20">
        <h2 className="m-0 max-w-[16ch] text-[2rem] leading-[1.15]">Live cases</h2>
        <p className="mt-3 max-w-[58ch] text-ink-muted">
          This list is the real feed from the agent. Fire the demo alert if it is empty.
        </p>
        {recentError ? (
          <p className="mt-6 text-ink-muted" role="alert">
            {recentError}
          </p>
        ) : recent.length === 0 ? (
          <p className="mt-6 text-ink-muted">No cases yet. The button above opens the first one.</p>
        ) : (
          <ul className="feed mt-6">
            {recent.map((incident) => (
              <li key={incident.id}>
                <Link href={`/incidents/${incident.id}`}>
                  <span className="feed-title">{incident.title}</span>
                  <span className="meta">
                    <span className={`badge sev-${incident.severity}`}>{incident.severity}</span>
                    <span className={`status-${incident.status}`}>{statusLabel(incident.status)}</span>
                    <span>{shortId(incident.id)}</span>
                    <span>{fmtTs(incident.created_at)}</span>
                  </span>
                </Link>
              </li>
            ))}
          </ul>
        )}
        {recent.length > 0 ? (
          <p className="mt-5">
            <Link href="/incidents">All cases</Link>
          </p>
        ) : null}
      </section>

      <section className="mt-24 grid gap-10 lg:grid-cols-[minmax(0,0.85fr)_minmax(0,1.15fr)] lg:items-start lg:gap-16">
        <div>
          <h2 className="m-0 max-w-[12ch] text-[2rem] leading-[1.15]">Tonight&apos;s demo alert</h2>
          <p className="mt-4 max-w-[42ch] text-ink-muted">
            One click sends this P1 into the agent. You land on the case it opens, with the trail already writing.
          </p>
        </div>
        <dl className="facts">
          {DEMO_FACTS.map((fact) => (
            <div className="fact" key={fact.label}>
              <dt>{fact.label}</dt>
              <dd className={fact.label === "The query" ? "font-mono text-[0.9rem]" : undefined}>{fact.value}</dd>
            </div>
          ))}
        </dl>
      </section>

      <section className="mt-24">
        <p className="pull m-0">
          Kill a node mid-incident and the agent still has its memory.
        </p>
        <div className="mt-10 border-t border-line">
          {MEMORY.map((item) => (
            <div className="memory-row" key={item.title}>
              <h3 className="m-0 text-[1.45rem] leading-[1.2]">{item.title}</h3>
              <p className="m-0 max-w-[52ch] text-ink-muted">{item.body}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="mt-24 max-w-[62ch]">
        <h2 className="m-0 text-[2rem] leading-[1.15]">It does not get a blank check</h2>
        <div className="mt-8">
          {GUARDS.map((item) => (
            <div key={item.title} className="border-b border-line py-6 first:border-t">
              <h3 className="m-0 text-[1.45rem] leading-[1.2]">{item.title}</h3>
              <p className="mt-2 m-0 text-ink-muted">{item.body}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="band">
        <h2 className="m-0 max-w-[16ch] text-[2rem] leading-[1.15]">Watch a case all the way through</h2>
        <p className="mt-3 max-w-[48ch] text-ink-muted">
          The how-it-works page walks the same loop you will see after you fire the alert.
        </p>
        <p className="mt-6">
          <Link className="btn btn-ghost" href="/how">
            How it works
          </Link>
        </p>
      </section>
    </div>
  );
}
