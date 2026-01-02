'use client';

import { Thread, getThreads } from '@/lib/api';
import { useEffect, useState } from 'react';

interface ThreadListProps {
  limit?: number;
}

export default function ThreadList({ limit = 10 }: ThreadListProps) {
  const [threads, setThreads] = useState<Thread[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchThreads() {
      try {
        setLoading(true);
        const data = await getThreads(limit);
        setThreads(data);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error');
      } finally {
        setLoading(false);
      }
    }

    fetchThreads();
  }, [limit]);

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="text-zinc-600 dark:text-zinc-400">Loading threads...</div>
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

  const getSentimentColor = (sentiment: string) => {
    switch (sentiment) {
      case 'pos':
        return 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300';
      case 'neg':
        return 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300';
      case 'neutral':
        return 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300';
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300';
    }
  };

  const getStatusColor = (status: string) => {
    return status === 'open'
      ? 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300'
      : 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300';
  };

  return (
    <div className="w-full">
      <h2 className="mb-4 text-xl font-semibold text-black dark:text-zinc-50">
        Recent Threads
      </h2>
      <div className="space-y-3">
        {threads.map((thread) => (
          <div
            key={thread.thread_id}
            className="rounded-lg border border-zinc-200 bg-white p-4 shadow-sm dark:border-zinc-800 dark:bg-zinc-900"
          >
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="mb-2 flex items-center gap-2">
                  <span className="font-mono text-sm font-medium text-zinc-900 dark:text-zinc-100">
                    {thread.thread_id}
                  </span>
                  <span
                    className={`rounded px-2 py-1 text-xs font-medium ${getStatusColor(
                      thread.thread_status
                    )}`}
                  >
                    {thread.thread_status}
                  </span>
                  <span
                    className={`rounded px-2 py-1 text-xs font-medium ${getSentimentColor(
                      thread.sentiment
                    )}`}
                  >
                    {thread.sentiment}
                  </span>
                </div>
                <div className="grid grid-cols-2 gap-4 text-sm text-zinc-600 dark:text-zinc-400">
                  <div>
                    <span className="font-medium">Messages:</span> {thread.message_count}
                  </div>
                  <div>
                    <span className="font-medium">Confidence:</span>{' '}
                    {(thread.confidence * 100).toFixed(1)}%
                  </div>
                  <div>
                    <span className="font-medium">Model:</span> {thread.model_name}
                  </div>
                  <div>
                    <span className="font-medium">Prompt:</span> {thread.prompt_version}
                  </div>
                </div>
                <div className="mt-2 text-xs text-zinc-500 dark:text-zinc-500">
                  Last message: {new Date(thread.last_message_ts).toLocaleString()}
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

