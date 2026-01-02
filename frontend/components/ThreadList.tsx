'use client';

import { Thread, getThreads } from '@/lib/api';
import { useEffect, useState } from 'react';

interface ThreadListProps {
  limit?: number;
}

export default function ThreadList({ limit = 200 }: ThreadListProps) {
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

  const getSentimentBadge = (sentiment: string) => {
    const colors = {
      pos: 'bg-green-500 text-white',
      neg: 'bg-red-500 text-white',
      neutral: 'bg-gray-500 text-white',
    };
    const labels = {
      pos: 'Pos',
      neg: 'Neg',
      neutral: 'Neutral',
    };
    return (
      <span className={`inline-flex items-center rounded px-2 py-1 text-xs font-medium ${colors[sentiment as keyof typeof colors] || colors.neutral}`}>
        {labels[sentiment as keyof typeof labels] || sentiment}
      </span>
    );
  };

  const getStatusBadge = (status: string) => {
    if (status === 'open') {
      return (
        <span className="inline-flex items-center rounded border border-blue-500 bg-transparent px-2 py-1 text-xs font-medium text-blue-700 dark:text-blue-400">
          Open
        </span>
      );
    }
    return (
      <span className="inline-flex items-center rounded bg-gray-700 px-2 py-1 text-xs font-medium text-white">
        Closed
      </span>
    );
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
      hour12: true,
    });
  };

  return (
    <div className="w-full">
      <h2 className="mb-4 text-xl font-semibold text-zinc-900 dark:text-zinc-50">
        Threads (Latest Activity)
      </h2>
      <div className="max-h-96 overflow-y-auto overflow-x-auto rounded-lg border border-zinc-200 bg-white shadow-sm dark:border-zinc-800 dark:bg-zinc-800">
        <table className="w-full border-collapse">
          <thead className="sticky top-0 z-10">
            <tr className="border-b border-zinc-200 bg-zinc-50 dark:border-zinc-700 dark:bg-zinc-900">
              <th className="px-4 py-3 text-left text-sm font-semibold text-zinc-900 dark:text-zinc-100">
                Thread ID
              </th>
              <th className="px-4 py-3 text-left text-sm font-semibold text-zinc-900 dark:text-zinc-100">
                Status
              </th>
              <th className="px-4 py-3 text-left text-sm font-semibold text-zinc-900 dark:text-zinc-100">
                Sentiment
              </th>
              <th className="px-4 py-3 text-left text-sm font-semibold text-zinc-900 dark:text-zinc-100">
                Confidence
              </th>
              <th className="px-4 py-3 text-left text-sm font-semibold text-zinc-900 dark:text-zinc-100">
                Last Updated
              </th>
              <th className="px-4 py-3 text-left text-sm font-semibold text-zinc-900 dark:text-zinc-100">
                Messages
              </th>
            </tr>
          </thead>
          <tbody>
            {threads.map((thread) => (
              <tr
                key={thread.thread_id}
                className="border-b border-zinc-100 dark:border-zinc-700 hover:bg-zinc-50 dark:hover:bg-zinc-700/50 cursor-pointer"
                onClick={() => console.log('Thread clicked:', thread.thread_id)}
              >
                <td className="px-4 py-3 text-sm font-mono text-zinc-900 dark:text-zinc-100">
                  {thread.thread_id}
                </td>
                <td className="px-4 py-3 text-sm">
                  {getStatusBadge(thread.thread_status)}
                </td>
                <td className="px-4 py-3 text-sm">
                  {getSentimentBadge(thread.sentiment)}
                </td>
                <td className="px-4 py-3 text-sm text-zinc-600 dark:text-zinc-400">
                  <span
                    title={`Confidence: ${(thread.confidence * 100).toFixed(1)}% | Model: ${thread.model_name} | Prompt: ${thread.prompt_version}`}
                    className="cursor-help underline decoration-dotted"
                  >
                    {(thread.confidence * 100).toFixed(0)}%
                  </span>
                </td>
                <td className="px-4 py-3 text-sm text-zinc-600 dark:text-zinc-400">
                  {formatDate(thread.last_message_ts)}
                </td>
                <td className="px-4 py-3 text-sm text-zinc-600 dark:text-zinc-400">
                  {thread.message_count}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

