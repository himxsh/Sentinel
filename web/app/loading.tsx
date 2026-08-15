export default function Loading() {
  return (
    <div className="shell">
      <div className="topbar">
        <div className="skeleton h-5 w-24" />
        <div className="skeleton h-5 w-16" />
      </div>
      <div className="grid gap-10 lg:grid-cols-2">
        <div className="space-y-4 pt-8">
          <div className="skeleton h-16 w-4/5" />
          <div className="skeleton h-16 w-3/5" />
          <div className="skeleton h-6 w-full max-w-md" />
          <div className="flex gap-3 pt-4">
            <div className="skeleton h-11 w-44" />
            <div className="skeleton h-11 w-36" />
          </div>
        </div>
        <div className="skeleton aspect-video w-full" />
      </div>
    </div>
  );
}
