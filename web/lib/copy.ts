export const STEPS = [
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

export const DEMO_FACTS = [
  { label: "What is wrong", value: "A heavy query is holding connections open." },
  { label: "How bad", value: "P1. Connection pool at 95 percent." },
  { label: "Which cluster", value: "kooky-efreet" },
  { label: "The query", value: "SELECT COUNT(*) FROM large_table CROSS JOIN another_table" },
];

export const MEMORY = [
  {
    title: "The case",
    body: "What is open, how severe it is, and whether Sentinel is looking, fixing, or done.",
  },
  {
    title: "The trail",
    body: "Every look-up, guess, and action, in order. This is the audit, not a chat log.",
  },
  {
    title: "The lesson",
    body: "A write-up stored next to the case so the following night does not start from zero.",
  },
];

export const GUARDS = [
  {
    title: "It can look. It cannot smash.",
    body: "Reads of cluster state are allowed. A change that can hurt waits for a person.",
  },
  {
    title: "Dry run first",
    body: "When a step can be simulated, Sentinel tries that before it touches the real thing.",
  },
  {
    title: "The trail is the record",
    body: "Nothing important lives only in a model reply. If the agent restarts, the case is still there.",
  },
];

export const HOW_NIGHT = [
  {
    title: "Open the case",
    body: "The alert becomes a durable record: title, severity, cluster, and the raw signal. That is the working memory.",
  },
  {
    title: "Remember",
    body: "Sentinel searches past cases and runbooks for something close. You will see what it recalled on the trail.",
  },
  {
    title: "Look",
    body: "It checks live state with a read-only path, then notes what the control plane and ops checks said.",
  },
  {
    title: "Decide",
    body: "It writes a guess and a plan. Safe steps can run. Destructive steps sit on the case until you approve.",
  },
  {
    title: "File",
    body: "When the loop finishes, a write-up is stored as knowledge. The next P1 does not meet a blank agent.",
  },
];

export const CASE_PAGE_SHOWS = [
  {
    title: "Status",
    body: "Opened, looking, fixing, resolved, or failed. If it is still moving, the page keeps polling.",
  },
  {
    title: "What it concluded",
    body: "The hypothesis lands first. The write-up appears when the case closes.",
  },
  {
    title: "Audit timeline",
    body: "Plain labels on each event, with the raw note tucked under a disclosure if you want the detail.",
  },
];
