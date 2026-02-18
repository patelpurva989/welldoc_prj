'use client';

/**
 * StreamingGenerator
 *
 * Connects to the backend SSE endpoint
 *   POST /api/v1/regulatory/submissions/{id}/generate-stream
 * and surfaces real-time generation progress plus live token streaming
 * to the user.
 *
 * Events received from the backend:
 *   { type: 'started',   message: string }
 *   { type: 'progress',  percent: number, message: string }
 *   { type: 'chunk',     text: string }
 *   { type: 'completed', percent: 100, submission_id: number, compliance_score: number, compliant: boolean, message: string }
 *   { type: 'error',     message: string }
 */

import { useEffect, useRef, useState, useCallback } from 'react';
import {
  FiZap,
  FiX,
  FiCheckCircle,
  FiAlertCircle,
  FiChevronDown,
  FiChevronUp,
  FiFileText,
} from 'react-icons/fi';

// ─── Types ───────────────────────────────────────────────────────────────────

interface SSEEvent {
  type: 'started' | 'progress' | 'chunk' | 'completed' | 'error';
  message?: string;
  percent?: number;
  text?: string;
  submission_id?: number;
  compliance_score?: number;
  compliant?: boolean;
}

type GenerationPhase =
  | 'idle'
  | 'connecting'
  | 'running'
  | 'completed'
  | 'error'
  | 'cancelled';

export interface StreamingGeneratorProps {
  submissionId: number;
  onComplete: () => void;
  onCancel?: () => void;
}

// ─── Phase Labels ─────────────────────────────────────────────────────────────

const PHASE_LABELS: Record<GenerationPhase, string> = {
  idle: 'Ready',
  connecting: 'Connecting…',
  running: 'Generating…',
  completed: 'Complete',
  error: 'Failed',
  cancelled: 'Cancelled',
};

const PHASE_COLORS: Record<GenerationPhase, string> = {
  idle: 'bg-gray-100 text-gray-700',
  connecting: 'bg-blue-100 text-blue-700',
  running: 'bg-indigo-100 text-indigo-700',
  completed: 'bg-green-100 text-green-800',
  error: 'bg-red-100 text-red-800',
  cancelled: 'bg-yellow-100 text-yellow-800',
};

// ─── Sub-components ───────────────────────────────────────────────────────────

function PhaseBadge({ phase }: { phase: GenerationPhase }) {
  return (
    <span
      className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold ${PHASE_COLORS[phase]}`}
    >
      {phase === 'running' && (
        <span className="relative flex h-2 w-2">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-indigo-400 opacity-75" />
          <span className="relative inline-flex rounded-full h-2 w-2 bg-indigo-500" />
        </span>
      )}
      {PHASE_LABELS[phase]}
    </span>
  );
}

function ProgressBar({ percent }: { percent: number }) {
  const clampedPercent = Math.min(100, Math.max(0, percent));
  const colorClass =
    clampedPercent === 100
      ? 'bg-green-500'
      : clampedPercent >= 70
      ? 'bg-blue-500'
      : 'bg-indigo-500';

  return (
    <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
      <div
        className={`h-3 rounded-full transition-all duration-500 ease-out ${colorClass}`}
        style={{ width: `${clampedPercent}%` }}
        role="progressbar"
        aria-valuenow={clampedPercent}
        aria-valuemin={0}
        aria-valuemax={100}
      />
    </div>
  );
}

// ─── Main Component ───────────────────────────────────────────────────────────

export default function StreamingGenerator({
  submissionId,
  onComplete,
  onCancel,
}: StreamingGeneratorProps) {
  const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8400';

  const [phase, setPhase] = useState<GenerationPhase>('idle');
  const [percent, setPercent] = useState(0);
  const [statusMessage, setStatusMessage] = useState('');
  const [streamedText, setStreamedText] = useState('');
  const [complianceScore, setComplianceScore] = useState<number | null>(null);
  const [isCompliant, setIsCompliant] = useState<boolean | null>(null);
  const [errorMessage, setErrorMessage] = useState('');
  const [previewExpanded, setPreviewExpanded] = useState(false);

  const abortRef = useRef<AbortController | null>(null);
  const previewRef = useRef<HTMLPreElement | null>(null);

  // Auto-scroll preview to bottom as text streams in
  useEffect(() => {
    if (previewExpanded && previewRef.current) {
      previewRef.current.scrollTop = previewRef.current.scrollHeight;
    }
  }, [streamedText, previewExpanded]);

  // ── Core: start SSE stream ──────────────────────────────────────────────────
  const startGeneration = useCallback(async () => {
    // Reset state
    setPhase('connecting');
    setPercent(0);
    setStatusMessage('Connecting to generation service…');
    setStreamedText('');
    setErrorMessage('');
    setComplianceScore(null);
    setIsCompliant(null);

    const controller = new AbortController();
    abortRef.current = controller;

    try {
      const response = await fetch(
        `${API_BASE}/api/v1/regulatory/submissions/${submissionId}/generate-stream`,
        {
          method: 'POST',
          signal: controller.signal,
          headers: { 'Content-Type': 'application/json' },
        }
      );

      if (!response.ok) {
        throw new Error(`Server returned ${response.status}: ${response.statusText}`);
      }

      if (!response.body) {
        throw new Error('Response has no readable body');
      }

      setPhase('running');

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });

        // SSE messages are delimited by double newlines
        const parts = buffer.split('\n\n');
        // The last part may be an incomplete message — keep it in the buffer
        buffer = parts.pop() ?? '';

        for (const part of parts) {
          const lines = part.split('\n');
          for (const line of lines) {
            if (!line.startsWith('data: ')) continue;
            const raw = line.slice('data: '.length).trim();
            if (!raw) continue;

            let event: SSEEvent;
            try {
              event = JSON.parse(raw);
            } catch {
              continue; // ignore malformed frames
            }

            handleEvent(event);
          }
        }
      }
    } catch (err: unknown) {
      if ((err as Error).name === 'AbortError') {
        setPhase('cancelled');
        setStatusMessage('Generation cancelled.');
      } else {
        setPhase('error');
        setErrorMessage((err as Error).message || 'Unknown error');
      }
    }
  }, [submissionId, API_BASE]);

  // ── Event dispatch ─────────────────────────────────────────────────────────
  const handleEvent = useCallback(
    (event: SSEEvent) => {
      switch (event.type) {
        case 'started':
          setStatusMessage(event.message ?? 'Starting…');
          setPercent(2);
          break;

        case 'progress':
          if (event.percent !== undefined) setPercent(event.percent);
          if (event.message) setStatusMessage(event.message);
          break;

        case 'chunk':
          if (event.text) {
            setStreamedText((prev) => prev + event.text);
          }
          break;

        case 'completed':
          setPercent(100);
          setPhase('completed');
          setStatusMessage(event.message ?? 'Generation complete!');
          if (event.compliance_score !== undefined) setComplianceScore(event.compliance_score);
          if (event.compliant !== undefined) setIsCompliant(event.compliant);
          onComplete();
          break;

        case 'error':
          setPhase('error');
          setErrorMessage(event.message ?? 'An unknown error occurred.');
          break;
      }
    },
    [onComplete]
  );

  // ── Cancel ─────────────────────────────────────────────────────────────────
  const handleCancel = () => {
    abortRef.current?.abort();
    setPhase('cancelled');
    setStatusMessage('Cancelled by user.');
    onCancel?.();
  };

  // ── Render ─────────────────────────────────────────────────────────────────

  const isActive = phase === 'running' || phase === 'connecting';
  const wordCount = streamedText.trim().split(/\s+/).filter(Boolean).length;

  return (
    <div className="rounded-2xl border border-gray-200 shadow-lg overflow-hidden bg-white">
      {/* ── Header ─────────────────────────────────────────────────────────── */}
      <div className="flex items-center justify-between px-6 py-4 bg-gradient-to-r from-indigo-700 to-blue-600 text-white">
        <div className="flex items-center gap-3">
          <FiZap className="h-5 w-5 text-yellow-300" />
          <div>
            <h3 className="text-base font-semibold tracking-tight">
              AI Document Generation
            </h3>
            <p className="text-xs text-indigo-200 mt-0.5">
              510(k) Premarket Notification — Real-time stream
            </p>
          </div>
        </div>
        <PhaseBadge phase={phase} />
      </div>

      {/* ── Body ───────────────────────────────────────────────────────────── */}
      <div className="px-6 py-5 space-y-5">

        {/* Status message */}
        {statusMessage && (
          <p className="text-sm text-gray-600 flex items-start gap-2">
            <FiFileText className="mt-0.5 shrink-0 text-indigo-400" />
            <span>{statusMessage}</span>
          </p>
        )}

        {/* Progress bar */}
        {phase !== 'idle' && (
          <div className="space-y-1.5">
            <div className="flex justify-between text-xs text-gray-500">
              <span>Generation progress</span>
              <span className="font-medium text-gray-700">{percent}%</span>
            </div>
            <ProgressBar percent={percent} />
          </div>
        )}

        {/* Error banner */}
        {phase === 'error' && errorMessage && (
          <div className="flex items-start gap-3 bg-red-50 border border-red-200 rounded-xl px-4 py-3 text-sm text-red-700">
            <FiAlertCircle className="mt-0.5 shrink-0 h-4 w-4 text-red-500" />
            <div>
              <p className="font-medium">Generation failed</p>
              <p className="mt-0.5 text-red-600">{errorMessage}</p>
            </div>
          </div>
        )}

        {/* Compliance result (shown after completion) */}
        {phase === 'completed' && complianceScore !== null && (
          <div
            className={`flex items-center gap-3 rounded-xl px-4 py-3 text-sm border ${
              isCompliant
                ? 'bg-green-50 border-green-200 text-green-700'
                : 'bg-orange-50 border-orange-200 text-orange-700'
            }`}
          >
            {isCompliant ? (
              <FiCheckCircle className="h-5 w-5 text-green-500 shrink-0" />
            ) : (
              <FiAlertCircle className="h-5 w-5 text-orange-500 shrink-0" />
            )}
            <div>
              <p className="font-semibold">
                {isCompliant ? '21 CFR Part 11 — Compliant' : '21 CFR Part 11 — Needs Attention'}
              </p>
              <p className="mt-0.5 text-xs opacity-80">
                Compliance score: {complianceScore}/100
              </p>
            </div>
          </div>
        )}

        {/* Live document preview */}
        {streamedText && (
          <div className="rounded-xl border border-gray-200 overflow-hidden">
            {/* Preview toggle header */}
            <button
              onClick={() => setPreviewExpanded((v) => !v)}
              className="w-full flex items-center justify-between px-4 py-2.5 bg-gray-50 hover:bg-gray-100 transition-colors text-sm font-medium text-gray-700"
            >
              <span className="flex items-center gap-2">
                <FiFileText className="text-indigo-500" />
                Live Document Preview
                {isActive && (
                  <span className="inline-flex items-center gap-1 text-xs text-indigo-600 font-normal">
                    <span className="animate-pulse">●</span> streaming
                  </span>
                )}
              </span>
              <span className="flex items-center gap-3 text-xs text-gray-500">
                {wordCount > 0 && <span>{wordCount.toLocaleString()} words</span>}
                {previewExpanded ? <FiChevronUp /> : <FiChevronDown />}
              </span>
            </button>

            {/* Preview content */}
            {previewExpanded && (
              <pre
                ref={previewRef}
                className="text-xs text-gray-700 whitespace-pre-wrap leading-relaxed p-4 bg-white max-h-96 overflow-y-auto font-mono"
              >
                {streamedText}
                {isActive && (
                  <span className="animate-pulse text-indigo-500">▋</span>
                )}
              </pre>
            )}

            {/* Collapsed summary */}
            {!previewExpanded && (
              <div className="px-4 py-2 bg-white text-xs text-gray-400 italic truncate">
                {streamedText.slice(0, 160)}…
              </div>
            )}
          </div>
        )}

        {/* Action buttons */}
        <div className="flex items-center gap-3 pt-1">
          {phase === 'idle' && (
            <button
              onClick={startGeneration}
              className="flex items-center gap-2 px-5 py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-semibold shadow-sm transition-colors"
            >
              <FiZap className="h-4 w-4" />
              Generate 510(k) Document
            </button>
          )}

          {isActive && (
            <button
              onClick={handleCancel}
              className="flex items-center gap-2 px-5 py-2.5 rounded-lg bg-red-100 hover:bg-red-200 text-red-700 text-sm font-semibold transition-colors"
            >
              <FiX className="h-4 w-4" />
              Cancel
            </button>
          )}

          {(phase === 'completed' || phase === 'error' || phase === 'cancelled') && (
            <button
              onClick={() => {
                setPhase('idle');
                setPercent(0);
                setStatusMessage('');
                setStreamedText('');
                setErrorMessage('');
                setComplianceScore(null);
                setIsCompliant(null);
              }}
              className="flex items-center gap-2 px-5 py-2.5 rounded-lg bg-gray-100 hover:bg-gray-200 text-gray-700 text-sm font-semibold transition-colors"
            >
              {phase === 'completed' ? 'Regenerate' : 'Retry'}
            </button>
          )}

          {phase === 'completed' && (
            <span className="flex items-center gap-1.5 text-sm text-green-600 font-medium">
              <FiCheckCircle className="h-4 w-4" />
              Document saved — refresh the page to view full output
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
