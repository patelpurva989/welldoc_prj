'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import StreamingGenerator from '@/components/StreamingGenerator';

const API_BASE = 'http://72.61.11.62:8660';

function getToken() {
  if (typeof window !== 'undefined') return localStorage.getItem('token') || '';
  return '';
}

async function apiFetch(path: string, options?: RequestInit) {
  const token = getToken();
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
      ...((options?.headers as Record<string, string>) || {}),
    },
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(err);
  }
  if (res.status === 204) return null;
  return res.json();
}

function progressColor(pct: number) {
  if (pct === 0) return '#ef4444';
  if (pct < 26) return '#f97316';
  if (pct < 51) return '#eab308';
  if (pct < 76) return '#84cc16';
  if (pct < 100) return '#22c55e';
  return '#16a34a';
}

export default function SubmissionDetailPage() {
  const params = useParams();
  const id = params?.id as string;
  const [submission, setSubmission] = useState<any>(null);
  const [documents, setDocuments] = useState<any[]>([]);
  const [reviews, setReviews] = useState<any[]>([]);
  const [activeReview, setActiveReview] = useState<any>(null);
  const [statusHistory, setStatusHistory] = useState<any[]>([]);
  const [tab, setTab] = useState<'overview' | 'documents' | 'checklist' | 'history'>('overview');
  const [uploading, setUploading] = useState(false);
  const [reviewingDoc, setReviewingDoc] = useState<number | null>(null);
  const [docType, setDocType] = useState('test_report');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  const [showStreaming, setShowStreaming] = useState(false);

  useEffect(() => {
    if (!id) return;
    loadAll();
  }, [id]);

  async function loadAll() {
    setLoading(true);
    try {
      const [sub, docs, revList, hist] = await Promise.allSettled([
        apiFetch(`/api/v1/regulatory/submissions/${id}`),
        apiFetch(`/api/v1/submissions/${id}/documents`),
        apiFetch(`/api/v1/submissions/${id}/reviews`),
        apiFetch(`/api/v1/submissions/${id}/status-history`),
      ]);
      if (sub.status === 'fulfilled') setSubmission(sub.value);
      if (docs.status === 'fulfilled') setDocuments(docs.value || []);
      if (revList.status === 'fulfilled') {
        const rvs = revList.value || [];
        setReviews(rvs);
        if (rvs.length > 0) {
          const full = await apiFetch(`/api/v1/submissions/${id}/reviews/${rvs[0].id}`);
          setActiveReview(full);
        }
      }
      if (hist.status === 'fulfilled') setStatusHistory(hist.value || []);
    } catch (e: any) {
      setError(e.message);
    }
    setLoading(false);
  }

  async function handleUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    try {
      const fd = new FormData();
      fd.append('file', file);
      fd.append('document_type', docType);
      const token = getToken();
      const res = await fetch(`${API_BASE}/api/v1/submissions/${id}/documents`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: fd,
      });
      if (!res.ok) throw new Error('Upload failed');
      const doc = await res.json();
      setDocuments(prev => [...prev, doc]);
    } catch (e: any) {
      setError(e.message);
    }
    setUploading(false);
    e.target.value = '';
  }

  async function handleAiReview(docId: number) {
    setReviewingDoc(docId);
    try {
      const result = await apiFetch(`/api/v1/submissions/${id}/documents/${docId}/ai-review`, { method: 'POST' });
      setDocuments(prev => prev.map(d => d.id === docId ? { ...d, ai_reviewed: true, ai_review_summary: result.summary } : d));
    } catch (e: any) {
      setError(e.message);
    }
    setReviewingDoc(null);
  }

  async function handleCreateReview() {
    try {
      const rev = await apiFetch(`/api/v1/submissions/${id}/reviews`, {
        method: 'POST',
        body: JSON.stringify({ reviewer_name: 'Kevin Admin', review_round: (reviews.length + 1) }),
      });
      const full = await apiFetch(`/api/v1/submissions/${id}/reviews/${rev.id}`);
      setActiveReview(full);
      setReviews(prev => [...prev, rev]);
      setTab('checklist');
    } catch (e: any) {
      setError(e.message);
    }
  }

  async function handleChecklistUpdate(itemId: number, field: string, value: any) {
    if (!activeReview) return;
    try {
      const updated = await apiFetch(`/api/v1/submissions/${id}/reviews/${activeReview.id}/checklist/${itemId}`, {
        method: 'PATCH',
        body: JSON.stringify({ [field]: value }),
      });
      const newChecklist = (activeReview.checklist || []).map((c: any) => c.id === itemId ? { ...c, ...updated } : c);
      const applicable = newChecklist.filter((c: any) => c.is_applicable);
      const prog = applicable.length ? Math.round(applicable.reduce((s: number, c: any) => s + (c.completeness_percent || 0), 0) / applicable.length) : 0;
      setActiveReview((prev: any) => ({ ...prev, checklist: newChecklist, overall_progress: prog }));
    } catch (e: any) {
      setError(e.message);
    }
  }

  if (loading) return <div className="p-8 text-center text-gray-500">Loading submission...</div>;
  if (!submission) return <div className="p-8 text-center text-red-500">Submission not found. <Link href="/" className="text-blue-600 underline">Back to dashboard</Link></div>;

  const progress = activeReview?.overall_progress ?? submission.progress_percent ?? 0;

  return (
    <div className="max-w-6xl mx-auto p-6">
      <div className="mb-6">
        <Link href="/" className="text-blue-600 hover:underline text-sm">← Back to Dashboard</Link>
        <h1 className="text-2xl font-bold mt-2">{submission.device_name}</h1>
        <div className="flex items-center gap-4 mt-2 flex-wrap">
          <span className={`px-3 py-1 rounded-full text-sm font-medium ${
            submission.status === 'approved' ? 'bg-green-100 text-green-800' :
            submission.status === 'rejected' ? 'bg-red-100 text-red-800' :
            submission.status === 'review_pending' ? 'bg-yellow-100 text-yellow-800' :
            'bg-blue-100 text-blue-800'
          }`}>{submission.status?.replace(/_/g, ' ').toUpperCase()}</span>
          <span className="text-sm text-gray-500">{submission.manufacturer}</span>
          <span className="text-sm text-gray-500">{submission.submission_type?.toUpperCase()}</span>
        </div>
        <div className="mt-3">
          <div className="flex justify-between text-sm mb-1">
            <span className="text-gray-600">Review Progress</span>
            <span className="font-medium" style={{ color: progressColor(progress) }}>{progress}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-3">
            <div className="h-3 rounded-full transition-all" style={{ width: `${progress}%`, backgroundColor: progressColor(progress) }} />
          </div>
        </div>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 rounded flex justify-between">
          <span>{error}</span>
          <button onClick={() => setError('')} className="text-red-400 hover:text-red-600 ml-2">×</button>
        </div>
      )}

      <div className="flex gap-1 border-b border-gray-200 mb-6">
        {(['overview', 'documents', 'checklist', 'history'] as const).map(t => (
          <button key={t} onClick={() => setTab(t)}
            className={`px-4 py-2 text-sm font-medium rounded-t transition-colors ${tab === t ? 'border-b-2 border-blue-600 text-blue-600 bg-white' : 'text-gray-600 hover:text-gray-800 hover:bg-gray-50'}`}>
            {t === 'checklist' ? '20-Section Checklist' : t.charAt(0).toUpperCase() + t.slice(1)}
            {t === 'documents' && documents.length > 0 && (
              <span className="ml-1 bg-blue-100 text-blue-700 rounded-full px-2 text-xs">{documents.length}</span>
            )}
          </button>
        ))}
      </div>

      {tab === 'overview' && (
        <div className="space-y-4">
          <div className="bg-white border rounded-lg p-5">
            <h2 className="font-semibold text-gray-800 mb-3">Device Information</h2>
            <dl className="grid grid-cols-2 gap-3 text-sm">
              <div><dt className="text-gray-500">Device Name</dt><dd className="font-medium">{submission.device_name}</dd></div>
              <div><dt className="text-gray-500">Manufacturer</dt><dd className="font-medium">{submission.manufacturer}</dd></div>
              <div><dt className="text-gray-500">Submission Type</dt><dd className="font-medium">{submission.submission_type?.toUpperCase()}</dd></div>
              <div><dt className="text-gray-500">Predicate K-Number</dt><dd className="font-medium">{submission.predicate_k_number || 'N/A'}</dd></div>
            </dl>
            {submission.indications_for_use && (
              <div className="mt-3 text-sm"><dt className="text-gray-500">Indications for Use</dt><dd className="mt-1">{submission.indications_for_use}</dd></div>
            )}
          </div>

          {submission.compliance_report && (
            <div className="bg-white border rounded-lg p-5">
              <h2 className="font-semibold text-gray-800 mb-3">Compliance Score (21 CFR Part 11)</h2>
              <div className="flex items-center gap-4">
                <div className="text-4xl font-bold" style={{ color: progressColor(submission.compliance_report.score || 0) }}>
                  {submission.compliance_report.score || 0}
                </div>
                <div className="text-sm text-gray-600">
                  <div>Status: <span className="font-medium">{submission.compliance_status}</span></div>
                  <div className="text-xs text-gray-400 mt-1">90-100: Fully compliant · 75-89: Minor issues · Below 75: Needs remediation</div>
                </div>
              </div>
            </div>
          )}

          {submission.generated_submission && (
            <div className="bg-white border rounded-lg p-5">
              <h2 className="font-semibold text-gray-800 mb-3">Generated 510(k) Document</h2>
              <div className="bg-gray-50 rounded p-4 max-h-96 overflow-y-auto">
                <pre className="text-xs text-gray-700 whitespace-pre-wrap font-mono">{submission.generated_submission}</pre>
              </div>
            </div>
          )}

          {showStreaming && (
            <div className="mb-4">
              <StreamingGenerator
                submissionId={Number(id)}
                onComplete={() => { setShowStreaming(false); loadAll(); }}
                onCancel={() => setShowStreaming(false)}
              />
            </div>
          )}

          <div className="flex gap-3 pt-2 flex-wrap">
            {!showStreaming && (
              <button onClick={() => setShowStreaming(true)}
                className="px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700 text-sm font-medium flex items-center gap-1">
                Stream Generate
              </button>
            )}
            {!activeReview ? (
              <button onClick={handleCreateReview}
                className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 text-sm font-medium">
                Start Review Workflow
              </button>
            ) : (
              <button onClick={() => setTab('checklist')}
                className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 text-sm font-medium">
                Continue Review ({progress}% complete)
              </button>
            )}
          </div>
        </div>
      )}

      {tab === 'documents' && (
        <div className="space-y-4">
          <div className="bg-white border rounded-lg p-5">
            <h2 className="font-semibold text-gray-800 mb-3">Upload Supporting Document</h2>
            <div className="flex gap-3 items-end flex-wrap">
              <div>
                <label className="block text-sm text-gray-600 mb-1">Document Type</label>
                <select value={docType} onChange={e => setDocType(e.target.value)}
                  className="border rounded px-3 py-2 text-sm text-gray-700">
                  <option value="test_report">Test Report</option>
                  <option value="biocompatibility">Biocompatibility</option>
                  <option value="clinical_data">Clinical Data</option>
                  <option value="sterilization">Sterilization Data</option>
                  <option value="risk_management">Risk Management</option>
                  <option value="labeling">Labeling</option>
                  <option value="supporting_doc">Supporting Document</option>
                </select>
              </div>
              <label className={`px-4 py-2 rounded text-sm font-medium cursor-pointer ${uploading ? 'bg-gray-300 text-gray-500 cursor-not-allowed' : 'bg-blue-600 text-white hover:bg-blue-700'}`}>
                {uploading ? 'Uploading...' : 'Choose File & Upload'}
                <input type="file" className="hidden" onChange={handleUpload} disabled={uploading}
                  accept=".pdf,.doc,.docx,.txt,.png,.jpg,.jpeg" />
              </label>
            </div>
            <p className="text-xs text-gray-400 mt-2">Accepted: PDF, DOCX, TXT, PNG, JPG (max 50MB)</p>
          </div>

          {documents.length === 0 ? (
            <div className="text-center py-12 text-gray-400 border-2 border-dashed border-gray-200 rounded-lg">
              No documents uploaded yet. Upload supporting materials to enhance AI generation.
            </div>
          ) : (
            <div className="space-y-3">
              {documents.map(doc => (
                <div key={doc.id} className="bg-white border rounded-lg p-4">
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1 min-w-0">
                      <div className="font-medium text-gray-800 truncate">{doc.filename}</div>
                      <div className="flex items-center gap-2 mt-1 flex-wrap">
                        <span className="text-xs text-gray-500">{doc.document_type}</span>
                        <span className="text-xs text-gray-400">{((doc.file_size || 0) / 1024).toFixed(1)} KB</span>
                        <span className={`text-xs px-2 py-0.5 rounded-full ${doc.ai_reviewed ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'}`}>
                          {doc.ai_reviewed ? 'AI Reviewed' : 'Pending AI Review'}
                        </span>
                      </div>
                    </div>
                    {!doc.ai_reviewed && (
                      <button onClick={() => handleAiReview(doc.id)} disabled={reviewingDoc === doc.id}
                        className="flex-shrink-0 px-3 py-1 text-xs bg-purple-600 text-white rounded hover:bg-purple-700 disabled:bg-gray-300">
                        {reviewingDoc === doc.id ? 'Analyzing...' : 'AI Review'}
                      </button>
                    )}
                  </div>
                  {doc.ai_review_summary && (
                    <div className="mt-3 bg-purple-50 border border-purple-100 rounded p-3">
                      <div className="text-xs font-medium text-purple-700 mb-1">AI Summary:</div>
                      <pre className="text-xs text-gray-700 whitespace-pre-wrap">{doc.ai_review_summary}</pre>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {tab === 'checklist' && (
        <div className="space-y-4">
          {!activeReview ? (
            <div className="text-center py-12">
              <p className="text-gray-500 mb-4">No review started yet for this submission.</p>
              <button onClick={handleCreateReview}
                className="px-5 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">
                Start 20-Section Review
              </button>
            </div>
          ) : (
            <>
              <div className="bg-white border rounded-lg p-4">
                <div className="flex justify-between items-center">
                  <div>
                    <div className="font-semibold">Review Round {activeReview.review_round}</div>
                    <div className="text-sm text-gray-500">Reviewer: {activeReview.reviewer_name} · Status: {activeReview.status}</div>
                  </div>
                  <div className="text-right">
                    <div className="text-3xl font-bold" style={{ color: progressColor(activeReview.overall_progress || 0) }}>
                      {activeReview.overall_progress || 0}%
                    </div>
                    <div className="text-xs text-gray-400">Overall Progress</div>
                  </div>
                </div>
              </div>

              <div className="space-y-2">
                {(activeReview.checklist || []).map((item: any) => (
                  <div key={item.id} className="bg-white border rounded-lg p-4 transition-all"
                    style={{ borderLeftWidth: 4, borderLeftColor: progressColor(item.completeness_percent || 0) }}>
                    <div className="flex items-start gap-3">
                      <div className="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold text-white"
                        style={{ backgroundColor: progressColor(item.completeness_percent || 0) }}>
                        {item.section_number}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="font-medium text-gray-800 text-sm">{item.section_name}</div>
                        <div className="flex gap-4 mt-2 flex-wrap items-center">
                          <label className="flex items-center gap-2 text-sm cursor-pointer">
                            <input type="checkbox" checked={item.is_complete || false}
                              onChange={e => handleChecklistUpdate(item.id, 'is_complete', e.target.checked)}
                              className="w-4 h-4 rounded" />
                            <span>Complete</span>
                          </label>
                          <div className="flex items-center gap-2 text-sm">
                            <span className="text-gray-500 text-xs">Progress:</span>
                            <input type="range" min="0" max="100" step="10"
                              value={item.completeness_percent || 0}
                              onChange={e => handleChecklistUpdate(item.id, 'completeness_percent', parseInt(e.target.value))}
                              className="w-20" />
                            <span className="text-sm font-medium w-9 text-right" style={{ color: progressColor(item.completeness_percent || 0) }}>
                              {item.completeness_percent || 0}%
                            </span>
                          </div>
                          <select value={item.deficiency_level || ''}
                            onChange={e => handleChecklistUpdate(item.id, 'deficiency_level', e.target.value || null)}
                            className="border rounded text-xs px-2 py-1 text-gray-700">
                            <option value="">No deficiency</option>
                            <option value="minor">Minor</option>
                            <option value="major">Major</option>
                          </select>
                        </div>
                        <div className="mt-2 flex gap-2">
                          <input type="text" placeholder="Assignee" value={item.assignee || ''}
                            onBlur={e => handleChecklistUpdate(item.id, 'assignee', e.target.value)}
                            onChange={e => {
                              const newChecklist = (activeReview.checklist || []).map((c: any) => c.id === item.id ? { ...c, assignee: e.target.value } : c);
                              setActiveReview((prev: any) => ({ ...prev, checklist: newChecklist }));
                            }}
                            className="border rounded text-xs px-2 py-1 w-32 text-gray-700" />
                          <input type="text" placeholder="Notes for reviewer..."
                            value={item.reviewer_notes || ''}
                            onBlur={e => handleChecklistUpdate(item.id, 'reviewer_notes', e.target.value)}
                            onChange={e => {
                              const newChecklist = (activeReview.checklist || []).map((c: any) => c.id === item.id ? { ...c, reviewer_notes: e.target.value } : c);
                              setActiveReview((prev: any) => ({ ...prev, checklist: newChecklist }));
                            }}
                            className="border rounded text-xs px-2 py-1 flex-1 text-gray-700" />
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              <div className="flex gap-3 pt-4 pb-8">
                <button
                  onClick={() => apiFetch(`/api/v1/submissions/${id}/reviews/${activeReview.id}`, { method: 'PATCH', body: JSON.stringify({ status: 'approved', overall_notes: 'Submission approved after review' }) }).then(() => loadAll())}
                  className="px-5 py-2 bg-green-600 text-white rounded hover:bg-green-700 text-sm font-medium">
                  Approve Submission
                </button>
                <button
                  onClick={() => apiFetch(`/api/v1/submissions/${id}/reviews/${activeReview.id}`, { method: 'PATCH', body: JSON.stringify({ status: 'rejected', overall_notes: 'Revision required - see checklist notes' }) }).then(() => loadAll())}
                  className="px-5 py-2 bg-red-600 text-white rounded hover:bg-red-700 text-sm font-medium">
                  Request Revision
                </button>
                <button onClick={loadAll} className="px-5 py-2 bg-gray-200 text-gray-700 rounded hover:bg-gray-300 text-sm font-medium">
                  Refresh
                </button>
              </div>
            </>
          )}
        </div>
      )}

      {tab === 'history' && (
        <div className="space-y-2">
          {statusHistory.length === 0 ? (
            <div className="text-center py-12 text-gray-400">No status changes recorded yet</div>
          ) : (
            statusHistory.map((log: any) => (
              <div key={log.id} className="bg-white border rounded-lg p-4">
                <div className="flex items-center gap-3 flex-wrap">
                  <div className="flex-1">
                    <span className="text-sm font-medium text-gray-600">{log.previous_status || 'created'}</span>
                    <span className="text-gray-400 mx-2">→</span>
                    <span className="text-sm font-medium text-blue-700">{log.new_status}</span>
                  </div>
                  <span className="text-xs text-gray-500">by {log.changed_by}</span>
                  <span className="text-xs text-gray-400">{log.changed_at ? new Date(log.changed_at).toLocaleString() : ''}</span>
                </div>
                {log.notes && <div className="mt-1 text-sm text-gray-600 border-t pt-1">{log.notes}</div>}
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
}
