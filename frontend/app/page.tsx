import ThreadList from '@/components/ThreadList';
import MonthlyAggregates from '@/components/MonthlyAggregates';

export default function Home() {
  return (
    <div className="min-h-screen bg-zinc-50 font-sans dark:bg-black">
      <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-black dark:text-zinc-50">
            Thread Analytics Dashboard
          </h1>
          <p className="mt-2 text-zinc-600 dark:text-zinc-400">
            Enterprise-compliant thread analytics powered by FastAPI and Next.js
          </p>
        </div>

        <div className="grid gap-8 lg:grid-cols-2">
          <div className="lg:col-span-2">
            <MonthlyAggregates months={6} />
          </div>
          <div className="lg:col-span-2">
            <ThreadList limit={10} />
          </div>
        </div>
      </main>
    </div>
  );
}
