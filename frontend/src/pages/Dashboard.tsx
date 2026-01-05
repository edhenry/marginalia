import { useQuery, useMutation } from '@tanstack/react-query';
import { BookOpen, Lightbulb, Clock, ArrowRight, Sparkles } from 'lucide-react';
import { Link } from 'react-router-dom';
import { papersApi, contextApi } from '../services/api';
import type { Paper } from '../types';

function StatusBadge({ status }: { status: string }) {
  const colors: Record<string, string> = {
    new: 'bg-blue-100 text-blue-700',
    processing: 'bg-yellow-100 text-yellow-700',
    claude_reviewed: 'bg-green-100 text-green-700',
    reading: 'bg-purple-100 text-purple-700',
  };

  return (
    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${colors[status] || 'bg-gray-100 text-gray-700'}`}>
      {status.replace('_', ' ')}
    </span>
  );
}

function PaperCard({ paper }: { paper: Paper }) {
  return (
    <Link
      to={`/paper/${paper.id}`}
      className="block p-4 bg-white rounded-lg border border-gray-200 hover:border-primary-300 hover:shadow-sm transition-all"
    >
      <div className="flex items-start justify-between gap-2 mb-2">
        <StatusBadge status={paper.status} />
        {paper.relevance_score !== null && (
          <span className="text-xs text-gray-500">
            {Math.round(paper.relevance_score * 100)}% relevant
          </span>
        )}
      </div>

      <h3 className="font-medium text-gray-900 line-clamp-2 mb-1">
        {paper.title}
      </h3>

      <p className="text-sm text-gray-500 mb-2">
        {paper.authors.slice(0, 3).join(', ')}
        {paper.authors.length > 3 && ' et al.'}
        {paper.year && ` · ${paper.year}`}
      </p>

      {paper.relevance_reason && (
        <p className="text-sm text-gray-600 line-clamp-2">
          {paper.relevance_reason}
        </p>
      )}
    </Link>
  );
}

export default function Dashboard() {
  const { data: queue, isLoading: queueLoading } = useQuery({
    queryKey: ['queue'],
    queryFn: papersApi.getQueue,
  });

  const { data: patterns } = useQuery({
    queryKey: ['patterns'],
    queryFn: contextApi.getPatterns,
  });

  const { data: questions } = useQuery({
    queryKey: ['questions'],
    queryFn: contextApi.getQuestions,
  });

  const briefingMutation = useMutation({
    mutationFn: contextApi.generateBriefing,
  });

  const priorityPapers = queue?.papers.slice(0, 5) || [];
  const unacknowledgedPatterns = patterns?.filter((p) => !p.acknowledged) || [];
  const activeQuestions = questions?.filter((q) => q.status === 'active') || [];

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-500">Welcome back to your research workspace</p>
        </div>

        <button
          onClick={() => briefingMutation.mutate()}
          disabled={briefingMutation.isPending}
          className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 transition-colors"
        >
          <Sparkles size={18} />
          {briefingMutation.isPending ? 'Generating...' : 'Generate Briefing'}
        </button>
      </div>

      {/* Briefing display */}
      {briefingMutation.data && (
        <div className="mb-6 p-4 bg-primary-50 border border-primary-200 rounded-lg">
          <h2 className="font-semibold text-primary-900 mb-2">Today's Briefing</h2>
          <div className="prose prose-sm text-primary-800 whitespace-pre-wrap">
            {briefingMutation.data.briefing}
          </div>
        </div>
      )}

      {/* Stats row */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        <div className="bg-white p-4 rounded-lg border border-gray-200">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-100 rounded-lg">
              <BookOpen className="text-blue-600" size={20} />
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-900">{queue?.total_count || 0}</p>
              <p className="text-sm text-gray-500">Papers in queue</p>
            </div>
          </div>
        </div>

        <div className="bg-white p-4 rounded-lg border border-gray-200">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-green-100 rounded-lg">
              <Clock className="text-green-600" size={20} />
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-900">{queue?.claude_reviewed_count || 0}</p>
              <p className="text-sm text-gray-500">Ready to read</p>
            </div>
          </div>
        </div>

        <div className="bg-white p-4 rounded-lg border border-gray-200">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-purple-100 rounded-lg">
              <Lightbulb className="text-purple-600" size={20} />
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-900">{unacknowledgedPatterns.length}</p>
              <p className="text-sm text-gray-500">New patterns</p>
            </div>
          </div>
        </div>

        <div className="bg-white p-4 rounded-lg border border-gray-200">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-amber-100 rounded-lg">
              <BookOpen className="text-amber-600" size={20} />
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-900">{activeQuestions.length}</p>
              <p className="text-sm text-gray-500">Active questions</p>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Priority papers */}
        <div className="lg:col-span-2">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">Priority Papers</h2>
            <Link
              to="/queue"
              className="text-sm text-primary-600 hover:text-primary-700 flex items-center gap-1"
            >
              View all <ArrowRight size={16} />
            </Link>
          </div>

          {queueLoading ? (
            <div className="space-y-3">
              {[1, 2, 3].map((i) => (
                <div key={i} className="h-32 bg-gray-100 rounded-lg animate-pulse" />
              ))}
            </div>
          ) : priorityPapers.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <BookOpen className="mx-auto mb-2" size={32} />
              <p>No papers in queue yet</p>
              <p className="text-sm">Add papers to get started</p>
            </div>
          ) : (
            <div className="space-y-3">
              {priorityPapers.map((paper) => (
                <PaperCard key={paper.id} paper={paper} />
              ))}
            </div>
          )}
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Active Research Questions */}
          <div className="bg-white p-4 rounded-lg border border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900 mb-3">Active Research Questions</h2>
            {activeQuestions.length === 0 ? (
              <p className="text-sm text-gray-500">No active questions</p>
            ) : (
              <ul className="space-y-2">
                {activeQuestions.slice(0, 5).map((q) => (
                  <li key={q.id} className="text-sm text-gray-700">
                    <span className="text-primary-600 mr-1">Q:</span>
                    {q.question}
                  </li>
                ))}
              </ul>
            )}
            <Link
              to="/agenda"
              className="block mt-3 text-sm text-primary-600 hover:text-primary-700"
            >
              Manage questions
            </Link>
          </div>

          {/* Recent Patterns */}
          {unacknowledgedPatterns.length > 0 && (
            <div className="bg-amber-50 p-4 rounded-lg border border-amber-200">
              <h2 className="text-lg font-semibold text-amber-900 mb-3">New Patterns Identified</h2>
              <ul className="space-y-2">
                {unacknowledgedPatterns.slice(0, 3).map((p) => (
                  <li key={p.id} className="text-sm text-amber-800">
                    <Lightbulb className="inline mr-1" size={14} />
                    {p.description}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
