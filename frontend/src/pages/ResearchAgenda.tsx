import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Plus, Target, Lightbulb, Check, Trash2, Edit2 } from 'lucide-react';
import { contextApi } from '../services/api';
import type { ResearchQuestion, Pattern } from '../types';
import clsx from 'clsx';

function AddQuestionDialog({
  open,
  onClose,
}: {
  open: boolean;
  onClose: () => void;
}) {
  const [question, setQuestion] = useState('');
  const [description, setDescription] = useState('');
  const queryClient = useQueryClient();

  const createMutation = useMutation({
    mutationFn: (data: { question: string; description?: string }) =>
      contextApi.createQuestion(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['questions'] });
      setQuestion('');
      setDescription('');
      onClose();
    },
  });

  if (!open) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-md">
        <h2 className="text-lg font-semibold mb-4">Add Research Question</h2>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Question
            </label>
            <input
              type="text"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="What are you trying to understand?"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Description (optional)
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Add more context..."
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>
        </div>

        <div className="flex justify-end gap-3 mt-6">
          <button
            onClick={onClose}
            className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg"
          >
            Cancel
          </button>
          <button
            onClick={() =>
              createMutation.mutate({
                question,
                description: description || undefined,
              })
            }
            disabled={!question || createMutation.isPending}
            className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50"
          >
            {createMutation.isPending ? 'Adding...' : 'Add Question'}
          </button>
        </div>
      </div>
    </div>
  );
}

function QuestionCard({ question }: { question: ResearchQuestion }) {
  const queryClient = useQueryClient();

  const updateMutation = useMutation({
    mutationFn: (data: Partial<ResearchQuestion>) =>
      contextApi.updateQuestion(question.id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['questions'] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: () => contextApi.deleteQuestion(question.id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['questions'] });
    },
  });

  const statusColors: Record<string, string> = {
    active: 'bg-green-100 text-green-700',
    paused: 'bg-yellow-100 text-yellow-700',
    resolved: 'bg-gray-100 text-gray-700',
  };

  return (
    <div className="p-4 bg-white border border-gray-200 rounded-lg">
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            <span
              className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                statusColors[question.status]
              }`}
            >
              {question.status}
            </span>
          </div>

          <h3 className="font-medium text-gray-900">{question.question}</h3>

          {question.description && (
            <p className="text-sm text-gray-600 mt-1">{question.description}</p>
          )}

          {question.related_paper_ids.length > 0 && (
            <p className="text-xs text-gray-500 mt-2">
              {question.related_paper_ids.length} related papers
            </p>
          )}
        </div>

        <div className="flex items-center gap-1">
          {question.status === 'active' && (
            <button
              onClick={() => updateMutation.mutate({ status: 'resolved' })}
              className="p-1.5 text-gray-400 hover:text-green-600 hover:bg-green-50 rounded"
              title="Mark resolved"
            >
              <Check size={16} />
            </button>
          )}

          {question.status === 'resolved' && (
            <button
              onClick={() => updateMutation.mutate({ status: 'active' })}
              className="p-1.5 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded"
              title="Reactivate"
            >
              <Target size={16} />
            </button>
          )}

          <button
            onClick={() => deleteMutation.mutate()}
            className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded"
            title="Delete"
          >
            <Trash2 size={16} />
          </button>
        </div>
      </div>
    </div>
  );
}

function PatternCard({ pattern }: { pattern: Pattern }) {
  const queryClient = useQueryClient();

  const acknowledgeMutation = useMutation({
    mutationFn: () => contextApi.acknowledgePattern(pattern.id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['patterns'] });
    },
  });

  return (
    <div
      className={clsx(
        'p-4 rounded-lg border',
        pattern.acknowledged
          ? 'bg-white border-gray-200'
          : 'bg-amber-50 border-amber-200'
      )}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            <Lightbulb
              size={16}
              className={pattern.acknowledged ? 'text-gray-400' : 'text-amber-600'}
            />
            {!pattern.acknowledged && (
              <span className="text-xs font-medium text-amber-700">New</span>
            )}
          </div>

          <p className="text-gray-700">{pattern.description}</p>

          <p className="text-xs text-gray-500 mt-2">
            {pattern.paper_ids.length} papers · Identified{' '}
            {new Date(pattern.identified_at).toLocaleDateString()}
          </p>
        </div>

        {!pattern.acknowledged && (
          <button
            onClick={() => acknowledgeMutation.mutate()}
            className="p-1.5 text-amber-600 hover:bg-amber-100 rounded"
            title="Acknowledge"
          >
            <Check size={16} />
          </button>
        )}
      </div>
    </div>
  );
}

export default function ResearchAgenda() {
  const [showAddDialog, setShowAddDialog] = useState(false);
  const [showResolved, setShowResolved] = useState(false);

  const { data: questions, isLoading: questionsLoading } = useQuery({
    queryKey: ['questions'],
    queryFn: contextApi.getQuestions,
  });

  const { data: patterns, isLoading: patternsLoading } = useQuery({
    queryKey: ['patterns'],
    queryFn: contextApi.getPatterns,
  });

  const analyzeMutation = useMutation({
    mutationFn: contextApi.analyzePatterns,
  });

  const activeQuestions = questions?.filter((q) => q.status === 'active') || [];
  const resolvedQuestions = questions?.filter((q) => q.status === 'resolved') || [];
  const unacknowledgedPatterns = patterns?.filter((p) => !p.acknowledged) || [];
  const acknowledgedPatterns = patterns?.filter((p) => p.acknowledged) || [];

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Research Agenda</h1>
          <p className="text-gray-500">
            Track your research questions and emerging patterns
          </p>
        </div>

        <button
          onClick={() => setShowAddDialog(true)}
          className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
        >
          <Plus size={18} />
          Add Question
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Research Questions */}
        <div>
          <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <Target size={20} />
            Research Questions
          </h2>

          {questionsLoading ? (
            <div className="space-y-3">
              {[1, 2, 3].map((i) => (
                <div key={i} className="h-24 bg-gray-100 rounded-lg animate-pulse" />
              ))}
            </div>
          ) : activeQuestions.length === 0 ? (
            <div className="text-center py-8 text-gray-500 bg-gray-50 rounded-lg">
              <Target size={32} className="mx-auto mb-2 opacity-50" />
              <p>No active questions</p>
              <p className="text-sm">Add questions to guide your research</p>
            </div>
          ) : (
            <div className="space-y-3">
              {activeQuestions.map((q) => (
                <QuestionCard key={q.id} question={q} />
              ))}
            </div>
          )}

          {resolvedQuestions.length > 0 && (
            <div className="mt-6">
              <button
                onClick={() => setShowResolved(!showResolved)}
                className="text-sm text-gray-500 hover:text-gray-700"
              >
                {showResolved ? 'Hide' : 'Show'} {resolvedQuestions.length} resolved
                questions
              </button>

              {showResolved && (
                <div className="mt-3 space-y-3">
                  {resolvedQuestions.map((q) => (
                    <QuestionCard key={q.id} question={q} />
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Patterns */}
        <div>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
              <Lightbulb size={20} />
              Identified Patterns
            </h2>

            <button
              onClick={() => analyzeMutation.mutate()}
              disabled={analyzeMutation.isPending}
              className="text-sm text-primary-600 hover:text-primary-700"
            >
              {analyzeMutation.isPending ? 'Analyzing...' : 'Analyze now'}
            </button>
          </div>

          {patternsLoading ? (
            <div className="space-y-3">
              {[1, 2].map((i) => (
                <div key={i} className="h-24 bg-gray-100 rounded-lg animate-pulse" />
              ))}
            </div>
          ) : patterns?.length === 0 ? (
            <div className="text-center py-8 text-gray-500 bg-gray-50 rounded-lg">
              <Lightbulb size={32} className="mx-auto mb-2 opacity-50" />
              <p>No patterns identified yet</p>
              <p className="text-sm">Claude will identify patterns as you read</p>
            </div>
          ) : (
            <div className="space-y-3">
              {unacknowledgedPatterns.map((p) => (
                <PatternCard key={p.id} pattern={p} />
              ))}
              {acknowledgedPatterns.map((p) => (
                <PatternCard key={p.id} pattern={p} />
              ))}
            </div>
          )}
        </div>
      </div>

      <AddQuestionDialog
        open={showAddDialog}
        onClose={() => setShowAddDialog(false)}
      />
    </div>
  );
}
