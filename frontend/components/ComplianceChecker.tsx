'use client';

import { useState } from 'react';
import { checkCompliance } from '@/lib/api';

interface ComplianceCheckerProps {
  submissionId: number;
}

export default function ComplianceChecker({ submissionId }: ComplianceCheckerProps) {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const runComplianceCheck = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await checkCompliance(submissionId, true, true, true);
      setResult(data);
    } catch (err: any) {
      setError(err.message || 'Failed to run compliance check');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">
        21 CFR Part 11 Compliance Check
      </h3>

      {!result && (
        <button
          onClick={runComplianceCheck}
          disabled={loading}
          className="w-full px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? (
            <span className="flex items-center justify-center">
              <svg
                className="animate-spin -ml-1 mr-3 h-5 w-5 text-white"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                ></circle>
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                ></path>
              </svg>
              Running Compliance Check...
            </span>
          ) : (
            'Run Compliance Check'
          )}
        </button>
      )}

      {error && (
        <div className="mt-4 bg-red-50 border-l-4 border-red-400 p-4">
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}

      {result && (
        <div className="mt-4 space-y-4">
          {/* Compliance Score */}
          <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
            <div>
              <h4 className="text-sm font-medium text-gray-700">Compliance Score</h4>
              <p className="text-xs text-gray-500 mt-1">Overall compliance rating</p>
            </div>
            <div className="text-right">
              <div
                className={`text-3xl font-bold ${
                  result.score >= 90
                    ? 'text-green-600'
                    : result.score >= 75
                    ? 'text-yellow-600'
                    : 'text-red-600'
                }`}
              >
                {result.score}
              </div>
              <div className="text-xs text-gray-500">out of 100</div>
            </div>
          </div>

          {/* Status */}
          <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
            <span className="text-sm font-medium text-gray-700">Status:</span>
            <span
              className={`px-3 py-1 rounded-full text-sm font-semibold ${
                result.compliance_status === 'compliant'
                  ? 'bg-green-100 text-green-800'
                  : result.compliance_status === 'non_compliant'
                  ? 'bg-red-100 text-red-800'
                  : 'bg-yellow-100 text-yellow-800'
              }`}
            >
              {result.compliance_status.replace('_', ' ').toUpperCase()}
            </span>
          </div>

          {/* Issues */}
          {result.issues && result.issues.length > 0 && (
            <div>
              <h4 className="text-sm font-medium text-gray-900 mb-2">Issues Found</h4>
              <div className="space-y-2">
                {result.issues.map((issue: any, index: number) => (
                  <div
                    key={index}
                    className="p-3 bg-red-50 border-l-4 border-red-400 rounded"
                  >
                    <p className="text-sm text-red-800">{issue.description || issue}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Recommendations */}
          {result.recommendations && result.recommendations.length > 0 && (
            <div>
              <h4 className="text-sm font-medium text-gray-900 mb-2">Recommendations</h4>
              <ul className="space-y-2">
                {result.recommendations.map((rec: string, index: number) => (
                  <li key={index} className="flex items-start">
                    <svg
                      className="h-5 w-5 text-green-500 mt-0.5 mr-2"
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
                    <span className="text-sm text-gray-700">{rec}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Rerun Button */}
          <button
            onClick={runComplianceCheck}
            disabled={loading}
            className="w-full px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50"
          >
            Rerun Check
          </button>
        </div>
      )}
    </div>
  );
}
