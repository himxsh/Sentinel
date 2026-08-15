import type { Metadata } from "next";
import Link from "next/link";
import { FireAlertButton } from "@/components/FireAlertButton";
import { Header } from "@/components/Header";
import { CASE_PAGE_SHOWS, HOW_NIGHT } from "@/lib/copy";

export const metadata: Metadata = {
  title: "How it works",
};

export default function HowPage() {
  return (
    <div className="shell shell-narrow">
      <Header current="how" />
      <h1 className="m-0 max-w-[16ch] text-[clamp(2.4rem,6vw,3.6rem)] leading-[1.12]">
        A night on call, without starting from zero.
      </h1>
      <p className="mt-5 max-w-[58ch] text-[1.125rem] text-ink-muted">
        Sentinel watches databases. When something is wrong, it does not wait for someone to paste logs into Slack. It
        opens a case, looks up what worked last time, and writes down what it did.
      </p>

      <p className="pull mt-16 mb-0">
        The memory is the product. The model is just the person reading it.
      </p>

      <ol className="mt-12 m-0 list-none p-0">
        {HOW_NIGHT.map((step) => (
          <li key={step.title} className="border-b border-line py-7 first:border-t">
            <h2 className="m-0 text-[1.7rem] leading-[1.15]">{step.title}</h2>
            <p className="mt-2 max-w-[58ch] text-ink-muted">{step.body}</p>
          </li>
        ))}
      </ol>

      <section className="mt-20">
        <h2 className="m-0 text-[2rem] leading-[1.15]">What you will see on a case</h2>
        <p className="mt-3 max-w-[58ch] text-ink-muted">
          After you fire the demo alert, Sentinel sends you to that case. Stay on the page. If work is still running, it
          refreshes on its own.
        </p>
        <div className="mt-8">
          {CASE_PAGE_SHOWS.map((item) => (
            <div key={item.title} className="grid gap-2 border-b border-line py-6 first:border-t md:grid-cols-[9rem_1fr] md:gap-8">
              <h3 className="m-0 text-[1.35rem] leading-[1.2]">{item.title}</h3>
              <p className="m-0 text-ink-muted">{item.body}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="mt-20 max-w-[58ch]">
        <h2 className="m-0 text-[2rem] leading-[1.15]">Why the memory lives in CockroachDB</h2>
        <p className="mt-4 text-ink-muted">
          The open case, the audit trail, and the lessons are not three systems taped together. They sit in one cluster,
          so a node dying mid-incident does not wipe the night. AWS is where the model and the files live. CockroachDB
          is where Sentinel remembers.
        </p>
      </section>

      <section className="band">
        <h2 className="m-0 text-[2rem] leading-[1.15]">Try the loop</h2>
        <p className="mt-3 max-w-[48ch] text-ink-muted">
          The demo alert is a runaway query. You will get a real case, not a slide.
        </p>
        <div className="mt-6 flex flex-wrap gap-3">
          <FireAlertButton />
          <Link className="btn btn-ghost" href="/incidents">
            Cases
          </Link>
        </div>
      </section>
    </div>
  );
}
