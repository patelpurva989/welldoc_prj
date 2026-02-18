import Link from 'next/link';
import { format } from 'date-fns';
import type { Submission } from '@/lib/api';

interface SubmissionCardProps {
  submission: Submission;
}

export default function SubmissionCard({ submission }: SubmissionCardProps) {
  const statusColors: Record<string, string> = {
    draft: 'bg-gray-100 text-gray-800',
    generating: 'bg-yellow-100 text-yellow-800',
    review_pending: 'bg-purple-100 text-purple-800',
    approved: 'bg-green-100 text-green-800',
    rejected: 'bg-red-100 text-red-800',
    submitted: 'bg-blue-100 text-blue-800',
  };

  const complianceColors: Record<string, string> = {
    compliant: 'text-green-600',
    non_compliant: 'text-red-600',
    needs_review: 'text-yellow-600',
  };

  const progress = (submission as any).progress_percent || 0;
  const progressColor = progress === 0 ? "#ef4444" : progress < 26 ? "#f97316" : progress < 51 ? "#eab308" : progress < 76 ? "#84cc16" : progress < 100 ? "#22c55e" : "#16a34a";

  return (
    <div className="bg-white rounded-lg shadow hover:shadow-lg transition-shadow p-6">
      <div className="flex justify-between items-start mb-4">
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-gray-900">{submission.device_name}</h3>
          <p className="text-sm text-gray-500 mt-1">
            {submission.manufacturer || 'No manufacturer'}
          </p>
        </div>
        <span
          className={`px-2 py-1 text-xs font-semibold rounded-full ${
            statusColors[submission.status] || 'bg-gray-100 text-gray-800'
          }`}
        >
          {submission.status.replace('_', ' ').toUpperCase()}
        </span>
      </div>

      <div className="space-y-2 mb-4">
        <div className="flex justify-between text-sm">
          <span className="text-gray-500">Type:</span>
          <span className="font-medium text-gray-900">
            {submission.submission_type.toUpperCase()}
          </span>
        </div>

        <div className="flex justify-between text-sm">
          <span className="text-gray-500">Compliance:</span>
          <span
            className={`font-medium ${
              complianceColors[submission.compliance_status] || 'text-gray-600'
            }`}
          >
            {submission.compliance_status.replace('_', ' ').toUpperCase()}
          </span>
        </div>

        {submission.compliance_report?.score && (
          <div className="flex justify-between text-sm">
            <span className="text-gray-500">Compliance Score:</span>
            <span className="font-medium text-gray-900">
              {submission.compliance_report.score}/100
            </span>
          </div>
        )}

        {submission.predicate_k_number && (
          <div className="flex justify-between text-sm">
            <span className="text-gray-500">Predicate:</span>
            <span className="font-medium text-gray-900">{submission.predicate_k_number}</span>
          </div>
        )}

        <div className="flex justify-between text-sm">
          <span className="text-gray-500">Created:</span>
          <span className="text-gray-900">
            {format(new Date(submission.created_at), 'MMM d, yyyy')}
          </span>
        </div>
      </div>

      {submission.device_description && (
        <p className="text-sm text-gray-600 mb-4 line-clamp-2">
          {submission.device_description}
        </p>
      )}

      {progress > 0 && (
        <div className="mb-3">
          <div className="flex justify-between text-xs mb-1">
            <span className="text-gray-500">Review Progress</span>
            <span style={{ color: progressColor }} className="font-medium">{progress}%</span>
          </div>
          <div className="w-full bg-gray-100 rounded-full h-2">
            <div className="h-2 rounded-full" style={{ width: `${progress}%`, backgroundColor: progressColor }} />
          </div>
        </div>
      )}

      <div className="flex space-x-3">
        <Link
          href={`/submissions/${submission.id}`}
          className="flex-1 text-center px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50"
        >
          View Details
        </Link>
        {submission.status === 'review_pending' && (
          <Link
            href={`/review/${submission.id}`}
            className="flex-1 text-center px-4 py-2 bg-primary-600 rounded-md text-sm font-medium text-white hover:bg-primary-700"
          >
            Review
          </Link>
        )}
      </div>
    </div>
  );
}
