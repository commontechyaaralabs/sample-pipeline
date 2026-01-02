'use client';

import { MonthlyAggregate, getMonthlyAggregates } from '@/lib/api';
import { useEffect, useState } from 'react';

interface MonthlyAggregatesProps {
  months?: number;
}

export default function MonthlyAggregates({ months = 12 }: MonthlyAggregatesProps) {
  const [aggregates, setAggregates] = useState<MonthlyAggregate[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchAggregates() {
      try {
        setLoading(true);
        const data = await getMonthlyAggregates(months);
        setAggregates(data);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error');
      } finally {
        setLoading(false);
      }
    }

    fetchAggregates();
  }, [months]);

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="text-zinc-600 dark:text-zinc-400">Loading aggregates...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-lg bg-red-50 dark:bg-red-900/20 p-4 text-red-800 dark:text-red-200">
        Error: {error}
      </div>
    );
  }

  return (
    <div className="w-full">
      <h2 className="mb-4 text-xl font-semibold text-zinc-900 dark:text-zinc-50">
        Monthly Thread Aggregates
      </h2>
      <div className="max-h-96 overflow-y-auto overflow-x-auto rounded-lg border border-zinc-200 bg-white shadow-sm dark:border-zinc-800 dark:bg-zinc-800">
        <table className="w-full border-collapse">
          <thead className="sticky top-0 z-10">
            <tr className="border-b border-zinc-200 bg-zinc-50 dark:border-zinc-700 dark:bg-zinc-900">
              <th className="px-4 py-3 text-left text-sm font-semibold text-zinc-900 dark:text-zinc-100">
                Month
              </th>
              <th className="px-4 py-3 text-right text-sm font-semibold text-zinc-900 dark:text-zinc-100">
                Total Threads
              </th>
              <th className="px-4 py-3 text-right text-sm font-semibold text-green-700 dark:text-green-400">
                Positive
              </th>
              <th className="px-4 py-3 text-right text-sm font-semibold text-zinc-600 dark:text-zinc-400">
                Neutral
              </th>
              <th className="px-4 py-3 text-right text-sm font-semibold text-red-700 dark:text-red-400">
                Negative
              </th>
            </tr>
          </thead>
          <tbody>
            {aggregates.map((agg) => {
              const posPercent = (agg.pos_threads / agg.thread_count) * 100;
              const neutralPercent = (agg.neutral_threads / agg.thread_count) * 100;
              const negPercent = (agg.neg_threads / agg.thread_count) * 100;

              return (
                <tr
                  key={agg.month}
                  className="border-b border-zinc-100 dark:border-zinc-700 hover:bg-zinc-50 dark:hover:bg-zinc-700/50"
                >
                  <td className="px-4 py-3 text-sm font-medium text-zinc-900 dark:text-zinc-100">
                    {agg.month}
                  </td>
                  <td className="px-4 py-3 text-right text-sm font-semibold text-zinc-900 dark:text-zinc-100">
                    {agg.thread_count.toLocaleString()}
                  </td>
                  <td className="px-4 py-3 text-right text-sm text-green-700 dark:text-green-400">
                    {agg.pos_threads.toLocaleString()} ({posPercent.toFixed(1)}%)
                  </td>
                  <td className="px-4 py-3 text-right text-sm text-zinc-600 dark:text-zinc-400">
                    {agg.neutral_threads.toLocaleString()} ({neutralPercent.toFixed(1)}%)
                  </td>
                  <td className="px-4 py-3 text-right text-sm text-red-700 dark:text-red-400">
                    {agg.neg_threads.toLocaleString()} ({negPercent.toFixed(1)}%)
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

