'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { getSubmissions, getAdverseEvents, type Submission, type AdverseEvent } from '@/lib/api';
import SubmissionCard from '@/components/SubmissionCard';

export default function Home() {
  const [submissions, setSubmissions] = useState<Submission[]>([]);
  const [adverseEvents, setAdverseEvents] = useState<AdverseEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [submissionsData, eventsData] = await Promise.all([
        getSubmissions(),
        getAdverseEvents(undefined, 50), // High risk events only
      ]);
      setSubmissions(submissionsData);
      setAdverseEvents(eventsData);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const stats = {
    total: submissions.length,
    draft: submissions.filter((s) => s.status === 'draft').length,
    generating: submissions.filter((s) => s.status === 'generating').length,
    reviewPending: submissions.filter((s) => s.status === 'review_pending').length,
    approved: submissions.filter((s) => s.status === 'approved').length,
    highRiskEvents: adverseEvents.length,
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">FDA Regulatory Dashboard</h1>
        <p className="mt-2 text-gray-600">
          AI-powered submission automation with real-time monitoring
        </p>
      </div>

      {/* Error Alert */}
      {error && (
        <div className="mb-6 bg-red-50 border-l-4 border-red-400 p-4">
          <div className="flex">
            <div className="ml-3">
              <p className="text-sm text-red-700">{error}</p>
            </div>
          </div>
        </div>
      )}

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-8">
        <StatCard label="Total Submissions" value={stats.total} color="blue" />
        <StatCard label="Draft" value={stats.draft} color="gray" />
        <StatCard label="Generating" value={stats.generating} color="yellow" />
        <StatCard label="Review Pending" value={stats.reviewPending} color="purple" />
        <StatCard label="Approved" value={stats.approved} color="green" />
        <StatCard label="High Risk Events" value={stats.highRiskEvents} color="red" />
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <Link
          href="/submit"
          className="block p-6 bg-white rounded-lg border-2 border-dashed border-gray-300 hover:border-primary-500 transition-colors"
        >
          <div className="text-center">
            <svg
              className="mx-auto h-12 w-12 text-gray-400"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 4v16m8-8H4"
              />
            </svg>
            <h3 className="mt-2 text-lg font-medium text-gray-900">New Submission</h3>
            <p className="mt-1 text-sm text-gray-500">Start a new 510(k) submission</p>
          </div>
        </Link>

        <Link
          href="/review"
          className="block p-6 bg-white rounded-lg border-2 border-dashed border-gray-300 hover:border-primary-500 transition-colors"
        >
          <div className="text-center">
            <svg
              className="mx-auto h-12 w-12 text-gray-400"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <h3 className="mt-2 text-lg font-medium text-gray-900">Review Submissions</h3>
            <p className="mt-1 text-sm text-gray-500">Human-in-the-loop review</p>
          </div>
        </Link>

        <button
          onClick={loadData}
          className="block p-6 bg-white rounded-lg border-2 border-dashed border-gray-300 hover:border-primary-500 transition-colors w-full"
        >
          <div className="text-center">
            <svg
              className="mx-auto h-12 w-12 text-gray-400"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
              />
            </svg>
            <h3 className="mt-2 text-lg font-medium text-gray-900">Refresh Data</h3>
            <p className="mt-1 text-sm text-gray-500">Update dashboard</p>
          </div>
        </button>
      </div>

      {/* Recent Submissions */}
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">Recent Submissions</h2>
        {submissions.length === 0 ? (
          <div className="bg-white rounded-lg p-8 text-center">
            <p className="text-gray-500">No submissions yet. Create your first one!</p>
            <Link
              href="/submit"
              className="mt-4 inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary-600 hover:bg-primary-700"
            >
              Create Submission
            </Link>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {submissions.slice(0, 6).map((submission) => (
              <SubmissionCard key={submission.id} submission={submission} />
            ))}
          </div>
        )}
      </div>

      {/* High Risk Adverse Events */}
      {adverseEvents.length > 0 && (
        <div>
          <h2 className="text-2xl font-bold text-gray-900 mb-4">High Risk Adverse Events</h2>
          <div className="bg-white rounded-lg shadow overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Device
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Event Type
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Severity
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Risk Score
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {adverseEvents.slice(0, 5).map((event) => (
                  <tr key={event.id}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {event.device_name}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {event.event_type}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {event.severity}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span
                        className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                          event.risk_score >= 75
                            ? 'bg-red-100 text-red-800'
                            : event.risk_score >= 50
                            ? 'bg-yellow-100 text-yellow-800'
                            : 'bg-green-100 text-green-800'
                        }`}
                      >
                        {event.risk_score}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

function StatCard({
  label,
  value,
  color,
}: {
  label: string;
  value: number;
  color: string;
}) {
  const colorClasses: Record<string, string> = {
    blue: 'bg-blue-100 text-blue-800',
    gray: 'bg-gray-100 text-gray-800',
    yellow: 'bg-yellow-100 text-yellow-800',
    purple: 'bg-purple-100 text-purple-800',
    green: 'bg-green-100 text-green-800',
    red: 'bg-red-100 text-red-800',
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="text-sm font-medium text-gray-500">{label}</div>
      <div className={`mt-2 text-3xl font-bold ${colorClasses[color] || 'text-gray-900'}`}>
        {value}
      </div>
    </div>
  );
}
