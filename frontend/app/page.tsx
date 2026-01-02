'use client';

import ThreadList from '@/components/ThreadList';
import MonthlyAggregates from '@/components/MonthlyAggregates';
import { getThreads } from '@/lib/api';
import { useEffect, useState } from 'react';

export default function Home() {
  const [lastUpdated, setLastUpdated] = useState<string | null>(null);

  useEffect(() => {
    // Fetch threads to get the latest timestamp for "Last updated" indicator
    async function fetchLastUpdated() {
      try {
        const threads = await getThreads(1); // Just need the first (most recent) thread
        if (threads.length > 0 && threads[0].last_message_ts) {
          const date = new Date(threads[0].last_message_ts);
          setLastUpdated(date.toLocaleString('en-US', {
            hour: 'numeric',
            minute: '2-digit',
            hour12: true
          }));
        }
      } catch (err) {
        // Silently fail - last updated is not critical
        console.error('Failed to fetch last updated:', err);
      }
    }
    fetchLastUpdated();
  }, []);

  return (
    <div className="min-h-screen bg-zinc-50 font-sans dark:bg-zinc-900">
      <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        {/* Header Section */}
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold text-zinc-900 dark:text-zinc-50">
              Threads Overview
            </h1>
          </div>
          {lastUpdated && (
            <div className="text-sm text-zinc-500 dark:text-zinc-400">
              Last updated: {lastUpdated}
            </div>
          )}
        </div>

        {/* Monthly Sentiment Trend Chart */}
        <div className="mb-8">
          <MonthlyAggregates months={12} />
        </div>

        {/* Threads Table */}
        <div>
          <ThreadList limit={200} />
        </div>
      </main>
    </div>
  );
}
