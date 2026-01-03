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

  const getSentimentBadge = (sentiment: string | null | undefined) => {
    if (!sentiment) {
      return <span className="text-zinc-400 dark:text-zinc-500">—</span>;
    }
    
    const sentimentConfig: Record<string, { color: string; label: string }> = {
      'Happy': { color: 'bg-green-500 text-white', label: 'Happy' },
      'Bit Irritated': { color: 'bg-yellow-500 text-white', label: 'Bit Irritated' },
      'Moderately Concerned': { color: 'bg-orange-500 text-white', label: 'Moderately Concerned' },
      'Anger': { color: 'bg-red-500 text-white', label: 'Anger' },
      'Frustrated': { color: 'bg-red-700 text-white', label: 'Frustrated' },
      // Backward compatibility
      'pos': { color: 'bg-green-500 text-white', label: 'Pos' },
      'neg': { color: 'bg-red-500 text-white', label: 'Neg' },
      'neutral': { color: 'bg-gray-500 text-white', label: 'Neutral' },
    };
    
    const config = sentimentConfig[sentiment] || { color: 'bg-gray-500 text-white', label: sentiment };
    
    return (
      <span className={`inline-flex items-center rounded px-2 py-1 text-xs font-medium ${config.color}`}>
        {config.label}
      </span>
    );
  };

  const getStatusBadge = (status: string, source?: string) => {
    const statusBadge = status === 'open' ? (
      <span className="inline-flex items-center rounded border border-blue-500 bg-transparent px-2 py-1 text-xs font-medium text-blue-700 dark:text-blue-400">
        Open
      </span>
    ) : (
      <span className="inline-flex items-center rounded bg-gray-700 px-2 py-1 text-xs font-medium text-white">
        Closed
      </span>
    );

    if (source) {
      const sourceBadge = source === 'llm' ? (
        <span className="ml-1 inline-flex items-center rounded bg-purple-100 px-1.5 py-0.5 text-xs font-medium text-purple-800 dark:bg-purple-900 dark:text-purple-200">
          LLM
        </span>
      ) : (
        <span className="ml-1 inline-flex items-center rounded bg-gray-100 px-1.5 py-0.5 text-xs font-medium text-gray-800 dark:bg-gray-700 dark:text-gray-200">
          Heuristic
        </span>
      );
      return (
        <span className="inline-flex items-center">
          {statusBadge}
          {sourceBadge}
        </span>
      );
    }

    return statusBadge;
  };

  const getNextActionBadge = (owner?: string) => {
    if (!owner) return <span className="text-zinc-400 dark:text-zinc-500">—</span>;
    
    const config: Record<string, { color: string; label: string }> = {
      'org': { color: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200', label: 'Org' },
      'customer': { color: 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200', label: 'Customer' },
      'none': { color: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200', label: 'None' },
    };
    
    const actionConfig = config[owner] || { color: 'bg-gray-100 text-gray-800', label: owner };
    
    return (
      <span className={`inline-flex items-center rounded px-2 py-1 text-xs font-medium ${actionConfig.color}`}>
        {actionConfig.label}
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
                Next Action
              </th>
              <th className="px-4 py-3 text-left text-sm font-semibold text-zinc-900 dark:text-zinc-100">
                Why?
              </th>
              <th className="px-4 py-3 text-left text-sm font-semibold text-zinc-900 dark:text-zinc-100">
                Sentiment
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
                  {getStatusBadge(thread.thread_status, thread.status_source)}
                </td>
                <td className="px-4 py-3 text-sm">
                  {getNextActionBadge(thread.next_action_owner)}
                </td>
                <td className="px-4 py-3 text-sm text-zinc-600 dark:text-zinc-400">
                  {thread.status_reason ? (
                    <span
                      title={thread.status_reason}
                      className="cursor-help text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 underline decoration-dotted"
                    >
                      {thread.status_reason}
                    </span>
                  ) : (
                    <span className="text-zinc-400 dark:text-zinc-500">—</span>
                  )}
                </td>
                <td className="px-4 py-3 text-sm">
                  {getSentimentBadge(thread.sentiment)}
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

