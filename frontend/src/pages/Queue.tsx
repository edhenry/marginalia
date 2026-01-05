import { useState, useRef } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Plus, Search, Filter, Archive, ExternalLink, Upload, FileText, Link as LinkIcon } from 'lucide-react';
import { Link } from 'react-router-dom';
import { papersApi, syncApi } from '../services/api';
import type { Paper, PaperStatus } from '../types';
import clsx from 'clsx';

const statusFilters: { value: PaperStatus | 'all'; label: string }[] = [
  { value: 'all', label: 'All' },
  { value: 'new', label: 'New' },
  { value: 'processing', label: 'Processing' },
  { value: 'claude_reviewed', label: 'Ready to Read' },
  { value: 'reading', label: 'Reading' },
  { value: 'read', label: 'Read' },
];

function StatusBadge({ status }: { status: PaperStatus }) {
  const colors: Record<string, string> = {
    new: 'bg-blue-100 text-blue-700',
    processing: 'bg-yellow-100 text-yellow-700',
    claude_reviewed: 'bg-green-100 text-green-700',
    reading: 'bg-purple-100 text-purple-700',
    read: 'bg-gray-100 text-gray-700',
    synthesized: 'bg-emerald-100 text-emerald-700',
    archived: 'bg-gray-100 text-gray-500',
  };

  return (
    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${colors[status]}`}>
      {status.replace('_', ' ')}
    </span>
  );
}

function PaperRow({ paper, onArchive }: { paper: Paper; onArchive: () => void }) {
  return (
    <div className="p-4 bg-white border border-gray-200 rounded-lg hover:border-primary-300 transition-colors">
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <StatusBadge status={paper.status} />
            <span className="text-xs text-gray-500">Priority: {paper.priority}</span>
            {paper.relevance_score !== null && (
              <span className="text-xs text-gray-500">
                {Math.round(paper.relevance_score * 100)}% relevant
              </span>
            )}
          </div>

          <Link
            to={`/paper/${paper.id}`}
            className="block font-medium text-gray-900 hover:text-primary-600 line-clamp-1"
          >
            {paper.title}
          </Link>

          <p className="text-sm text-gray-500 mt-1">
            {paper.authors.slice(0, 3).join(', ')}
            {paper.authors.length > 3 && ' et al.'}
            {paper.venue && ` · ${paper.venue}`}
            {paper.year && ` (${paper.year})`}
          </p>

          {paper.relevance_reason && (
            <p className="text-sm text-gray-600 mt-2 line-clamp-2">
              {paper.relevance_reason}
            </p>
          )}

          {paper.tags.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-2">
              {paper.tags.map((tag) => (
                <span
                  key={tag}
                  className="px-2 py-0.5 bg-gray-100 text-gray-600 rounded text-xs"
                >
                  {tag}
                </span>
              ))}
            </div>
          )}
        </div>

        <div className="flex items-center gap-2">
          {paper.source_url && (
            <a
              href={paper.source_url}
              target="_blank"
              rel="noopener noreferrer"
              className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg"
              title="Open source"
            >
              <ExternalLink size={18} />
            </a>
          )}

          <button
            onClick={onArchive}
            className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg"
            title="Archive"
          >
            <Archive size={18} />
          </button>
        </div>
      </div>
    </div>
  );
}

type AddMode = 'arxiv' | 'upload';

function AddPaperDialog({
  open,
  onClose,
}: {
  open: boolean;
  onClose: () => void;
}) {
  const [mode, setMode] = useState<AddMode>('arxiv');
  const [arxivId, setArxivId] = useState('');
  const [pdfFile, setPdfFile] = useState<File | null>(null);
  const [title, setTitle] = useState('');
  const [authors, setAuthors] = useState('');
  const [year, setYear] = useState('');
  const [venue, setVenue] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);
  const queryClient = useQueryClient();

  const importMutation = useMutation({
    mutationFn: (id: string) => syncApi.importFromArxiv(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['queue'] });
      queryClient.invalidateQueries({ queryKey: ['papers'] });
      resetForm();
      onClose();
    },
  });

  const uploadMutation = useMutation({
    mutationFn: async () => {
      if (!pdfFile || !title) throw new Error('PDF and title required');
      return papersApi.uploadPaper(pdfFile, {
        title,
        authors: authors.split(',').map((a) => a.trim()).filter(Boolean),
        year: year ? parseInt(year, 10) : undefined,
        venue: venue || undefined,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['queue'] });
      queryClient.invalidateQueries({ queryKey: ['papers'] });
      resetForm();
      onClose();
    },
  });

  const resetForm = () => {
    setArxivId('');
    setPdfFile(null);
    setTitle('');
    setAuthors('');
    setYear('');
    setVenue('');
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setPdfFile(file);
      // Try to extract title from filename
      if (!title) {
        const nameWithoutExt = file.name.replace(/\.pdf$/i, '');
        setTitle(nameWithoutExt);
      }
    }
  };

  if (!open) return null;

  const isLoading = importMutation.isPending || uploadMutation.isPending;
  const error = importMutation.error || uploadMutation.error;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-md">
        <h2 className="text-lg font-semibold mb-4">Add Paper</h2>

        {/* Mode tabs */}
        <div className="flex mb-4 border-b border-gray-200">
          <button
            onClick={() => setMode('arxiv')}
            className={clsx(
              'flex items-center gap-2 px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors',
              mode === 'arxiv'
                ? 'border-primary-600 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            )}
          >
            <LinkIcon size={16} />
            From arXiv
          </button>
          <button
            onClick={() => setMode('upload')}
            className={clsx(
              'flex items-center gap-2 px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors',
              mode === 'upload'
                ? 'border-primary-600 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            )}
          >
            <Upload size={16} />
            Upload PDF
          </button>
        </div>

        <div className="space-y-4">
          {mode === 'arxiv' ? (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                arXiv ID
              </label>
              <input
                type="text"
                value={arxivId}
                onChange={(e) => setArxivId(e.target.value)}
                placeholder="e.g., 2301.12345"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
              <p className="text-xs text-gray-500 mt-1">
                Enter the arXiv ID to import paper and PDF
              </p>
            </div>
          ) : (
            <>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  PDF File
                </label>
                <input
                  type="file"
                  ref={fileInputRef}
                  accept=".pdf"
                  onChange={handleFileChange}
                  className="hidden"
                />
                <button
                  onClick={() => fileInputRef.current?.click()}
                  className={clsx(
                    'w-full p-4 border-2 border-dashed rounded-lg transition-colors text-center',
                    pdfFile
                      ? 'border-primary-300 bg-primary-50'
                      : 'border-gray-300 hover:border-gray-400'
                  )}
                >
                  {pdfFile ? (
                    <div className="flex items-center justify-center gap-2">
                      <FileText size={20} className="text-primary-600" />
                      <span className="text-sm text-primary-700">{pdfFile.name}</span>
                    </div>
                  ) : (
                    <div>
                      <Upload className="mx-auto mb-2 text-gray-400" size={24} />
                      <p className="text-sm text-gray-500">Click to select PDF</p>
                    </div>
                  )}
                </button>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Title *
                </label>
                <input
                  type="text"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="Paper title"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Authors
                </label>
                <input
                  type="text"
                  value={authors}
                  onChange={(e) => setAuthors(e.target.value)}
                  placeholder="Author 1, Author 2, ..."
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Year
                  </label>
                  <input
                    type="number"
                    value={year}
                    onChange={(e) => setYear(e.target.value)}
                    placeholder="2024"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Venue
                  </label>
                  <input
                    type="text"
                    value={venue}
                    onChange={(e) => setVenue(e.target.value)}
                    placeholder="Conference/Journal"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                  />
                </div>
              </div>
            </>
          )}

          {error && (
            <p className="text-sm text-red-600">
              {(error as Error).message}
            </p>
          )}
        </div>

        <div className="flex justify-end gap-3 mt-6">
          <button
            onClick={() => {
              resetForm();
              onClose();
            }}
            className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg"
          >
            Cancel
          </button>
          {mode === 'arxiv' ? (
            <button
              onClick={() => importMutation.mutate(arxivId)}
              disabled={!arxivId || isLoading}
              className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50"
            >
              {importMutation.isPending ? 'Importing...' : 'Import from arXiv'}
            </button>
          ) : (
            <button
              onClick={() => uploadMutation.mutate()}
              disabled={!pdfFile || !title || isLoading}
              className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50"
            >
              {uploadMutation.isPending ? 'Uploading...' : 'Upload Paper'}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

export default function Queue() {
  const [statusFilter, setStatusFilter] = useState<PaperStatus | 'all'>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [showAddDialog, setShowAddDialog] = useState(false);

  const queryClient = useQueryClient();

  const { data: queue, isLoading } = useQuery({
    queryKey: ['queue'],
    queryFn: papersApi.getQueue,
  });

  const archiveMutation = useMutation({
    mutationFn: (id: string) => papersApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['queue'] });
    },
  });

  const filteredPapers = (queue?.papers || []).filter((paper) => {
    if (statusFilter !== 'all' && paper.status !== statusFilter) {
      return false;
    }
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      return (
        paper.title.toLowerCase().includes(query) ||
        paper.authors.some((a) => a.toLowerCase().includes(query))
      );
    }
    return true;
  });

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Reading Queue</h1>
          <p className="text-gray-500">
            {queue?.total_count || 0} papers · {queue?.claude_reviewed_count || 0} ready to read
          </p>
        </div>

        <button
          onClick={() => setShowAddDialog(true)}
          className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
        >
          <Plus size={18} />
          Add Paper
        </button>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-4 mb-6">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search papers..."
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
          />
        </div>

        <div className="flex items-center gap-2">
          <Filter size={18} className="text-gray-400" />
          <div className="flex gap-1">
            {statusFilters.map(({ value, label }) => (
              <button
                key={value}
                onClick={() => setStatusFilter(value)}
                className={clsx(
                  'px-3 py-1 text-sm rounded-lg transition-colors',
                  statusFilter === value
                    ? 'bg-primary-100 text-primary-700'
                    : 'text-gray-600 hover:bg-gray-100'
                )}
              >
                {label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Paper list */}
      {isLoading ? (
        <div className="space-y-3">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="h-32 bg-gray-100 rounded-lg animate-pulse" />
          ))}
        </div>
      ) : filteredPapers.length === 0 ? (
        <div className="text-center py-12 text-gray-500">
          <p className="text-lg">No papers found</p>
          <p className="text-sm mt-1">
            {statusFilter !== 'all' || searchQuery
              ? 'Try adjusting your filters'
              : 'Add papers to get started'}
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {filteredPapers.map((paper) => (
            <PaperRow
              key={paper.id}
              paper={paper}
              onArchive={() => archiveMutation.mutate(paper.id)}
            />
          ))}
        </div>
      )}

      <AddPaperDialog
        open={showAddDialog}
        onClose={() => setShowAddDialog(false)}
      />
    </div>
  );
}
