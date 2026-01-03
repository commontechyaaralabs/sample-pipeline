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
                Happy
              </th>
              <th className="px-4 py-3 text-right text-sm font-semibold text-yellow-700 dark:text-yellow-400">
                Bit Irritated
              </th>
              <th className="px-4 py-3 text-right text-sm font-semibold text-orange-700 dark:text-orange-400">
                Moderately Concerned
              </th>
              <th className="px-4 py-3 text-right text-sm font-semibold text-red-700 dark:text-red-400">
                Anger
              </th>
              <th className="px-4 py-3 text-right text-sm font-semibold text-red-900 dark:text-red-500">
                Frustrated
              </th>
            </tr>
          </thead>
          <tbody>
            {aggregates.map((agg) => {
              const happyPercent = (agg.happy_threads / agg.thread_count) * 100;
              const bitIrritatedPercent = (agg.bit_irritated_threads / agg.thread_count) * 100;
              const moderatelyConcernedPercent = (agg.moderately_concerned_threads / agg.thread_count) * 100;
              const angerPercent = (agg.anger_threads / agg.thread_count) * 100;
              const frustratedPercent = (agg.frustrated_threads / agg.thread_count) * 100;

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
                    {agg.happy_threads.toLocaleString()} ({happyPercent.toFixed(1)}%)
                  </td>
                  <td className="px-4 py-3 text-right text-sm text-yellow-700 dark:text-yellow-400">
                    {agg.bit_irritated_threads.toLocaleString()} ({bitIrritatedPercent.toFixed(1)}%)
                  </td>
                  <td className="px-4 py-3 text-right text-sm text-orange-700 dark:text-orange-400">
                    {agg.moderately_concerned_threads.toLocaleString()} ({moderatelyConcernedPercent.toFixed(1)}%)
                  </td>
                  <td className="px-4 py-3 text-right text-sm text-red-700 dark:text-red-400">
                    {agg.anger_threads.toLocaleString()} ({angerPercent.toFixed(1)}%)
                  </td>
                  <td className="px-4 py-3 text-right text-sm text-red-900 dark:text-red-500">
                    {agg.frustrated_threads.toLocaleString()} ({frustratedPercent.toFixed(1)}%)
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

