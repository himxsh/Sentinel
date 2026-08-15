import { Header } from "@/components/Header";
import { IncidentDetail } from "@/components/IncidentDetail";

export default async function IncidentPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  return (
    <div className="shell shell-narrow">
      <Header current="incidents" />
      <IncidentDetail id={id} />
    </div>
  );
}
