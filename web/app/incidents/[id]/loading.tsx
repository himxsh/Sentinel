export default function Loading() {
  return (
    <div className="shell shell-narrow">
      <div className="topbar">
        <div className="skeleton h-5 w-24" />
        <div className="skeleton h-5 w-16" />
      </div>
      <div className="skeleton mb-6 h-10 w-3/4" />
      <div className="grid gap-4 md:grid-cols-2">
        <div className="skeleton h-40" />
        <div className="skeleton h-40" />
        <div className="skeleton h-64 md:col-span-2" />
      </div>
    </div>
  );
}
