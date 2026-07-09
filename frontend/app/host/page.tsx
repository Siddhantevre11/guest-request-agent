import { HostDashboard } from "@/components/HostDashboard";

export default function HostPage() {
  return (
    <main className="flex min-h-screen flex-col items-center gap-6 bg-zinc-50 px-16 py-16 dark:bg-black">
      <h1 className="text-2xl font-semibold text-black dark:text-zinc-50">Host Dashboard</h1>
      <HostDashboard />
    </main>
  );
}
