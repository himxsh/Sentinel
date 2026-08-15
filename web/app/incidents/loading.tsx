export default function Loading() {
  return (
    <div className="shell shell-narrow">
      <div className="topbar">
        <div className="skeleton h-5 w-24" />
        <div className="skeleton h-5 w-16" />
      </div>
      <div className="skeleton mb-8 h-10 w-40" />
      <div className="space-y-0">
        <div className="skeleton mb-px h-20 w-full rounded-none" />
        <div className="skeleton mb-px h-20 w-full rounded-none" />
        <div className="skeleton h-20 w-full rounded-none" />
      </div>
    </div>
  );
}
