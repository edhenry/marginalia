import { useState, useCallback } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  ArrowLeft,
  MessageSquare,
  FileText,
  Bookmark,
  Send,
  Lightbulb,
  ExternalLink,
  Upload,
} from 'lucide-react';
import { papersApi, chatApi, syncApi } from '../services/api';
import type { ChatMessage, Annotation as AnnotationType } from '../types';
import PDFViewer from '../components/pdf/PDFViewer';
import TextSelectionPopover from '../components/pdf/TextSelectionPopover';
import clsx from 'clsx';

type TabType = 'review' | 'annotations' | 'chat';

interface SelectionState {
  text: string;
  pageNumber: number;
  position: { x: number; y: number };
  rects: Array<{ x: number; y: number; width: number; height: number }>;
}

export default function PaperView() {
  const { paperId } = useParams<{ paperId: string }>();
  const [activeTab, setActiveTab] = useState<TabType>('review');
  const [chatMessage, setChatMessage] = useState('');
  const [selection, setSelection] = useState<SelectionState | null>(null);
  const queryClient = useQueryClient();

  const { data: paper, isLoading: paperLoading } = useQuery({
    queryKey: ['paper', paperId],
    queryFn: () => papersApi.get(paperId!),
    enabled: !!paperId,
    refetchInterval: (data) => {
      // Poll while paper is processing
      if (data?.status === 'processing') {
        return 5000;
      }
      return false;
    },
  });

  const { data: annotations, refetch: refetchAnnotations } = useQuery({
    queryKey: ['annotations', paperId],
    queryFn: () => papersApi.getAnnotations(paperId!),
    enabled: !!paperId,
  });

  const { data: threads } = useQuery({
    queryKey: ['threads', paperId],
    queryFn: () => chatApi.listThreads({ paper_id: paperId }),
    enabled: !!paperId,
  });

  // Get or create a chat thread for this paper
  const thread = threads?.[0];

  const { data: messages, refetch: refetchMessages } = useQuery({
    queryKey: ['messages', thread?.id],
    queryFn: () => chatApi.getMessages(thread!.id),
    enabled: !!thread,
  });

  const createThreadMutation = useMutation({
    mutationFn: () =>
      chatApi.createThread({
        context_type: 'paper',
        paper_id: paperId,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['threads', paperId] });
    },
  });

  const sendMessageMutation = useMutation({
    mutationFn: async (content: string) => {
      let threadId = thread?.id;
      if (!threadId) {
        const newThread = await chatApi.createThread({
          context_type: 'paper',
          paper_id: paperId,
        });
        threadId = newThread.id;
        queryClient.invalidateQueries({ queryKey: ['threads', paperId] });
      }
      return chatApi.sendMessage(threadId, content);
    },
    onSuccess: () => {
      refetchMessages();
      setChatMessage('');
    },
  });

  const createAnnotationMutation = useMutation({
    mutationFn: (data: { type: string; content: string; pageNumber: number; selectedText?: string; position?: any }) =>
      papersApi.createAnnotation(paperId!, {
        author: 'user',
        type: data.type as 'highlight' | 'note' | 'question',
        page_number: data.pageNumber,
        selected_text: data.selectedText,
        content: data.content,
        position: data.position,
        thread_id: null,
      }),
    onSuccess: () => {
      refetchAnnotations();
      setSelection(null);
    },
  });

  const saveLiteNoteMutation = useMutation({
    mutationFn: () => syncApi.saveLiteratureNote(paperId!),
  });

  const handleTextSelect = useCallback(
    (text: string, pageNumber: number, position: { rects: any[]; pageIndex: number }) => {
      if (!text.trim()) return;

      // Get position for popover (use center of first rect)
      const firstRect = position.rects[0];
      if (!firstRect) return;

      setSelection({
        text,
        pageNumber,
        position: { x: firstRect.x + firstRect.width / 2, y: firstRect.y + firstRect.height },
        rects: position.rects,
      });
    },
    []
  );

  const handleHighlight = () => {
    if (!selection) return;
    createAnnotationMutation.mutate({
      type: 'highlight',
      content: selection.text,
      pageNumber: selection.pageNumber,
      selectedText: selection.text,
      position: { page_index: selection.pageNumber - 1, rects: selection.rects },
    });
  };

  const handleAddNote = (note: string) => {
    if (!selection) return;
    createAnnotationMutation.mutate({
      type: 'note',
      content: note,
      pageNumber: selection.pageNumber,
      selectedText: selection.text,
      position: { page_index: selection.pageNumber - 1, rects: selection.rects },
    });
  };

  const handleAskClaude = () => {
    if (!selection) return;
    setActiveTab('chat');
    setChatMessage(`Regarding this passage: "${selection.text.slice(0, 200)}${selection.text.length > 200 ? '...' : ''}"\n\n`);
    setSelection(null);
  };

  const handleSendMessage = () => {
    if (!chatMessage.trim()) return;
    sendMessageMutation.mutate(chatMessage);
  };

  const handleAnnotationClick = (annotation: AnnotationType) => {
    setActiveTab('annotations');
    // Could scroll to annotation in list
  };

  if (paperLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" />
      </div>
    );
  }

  if (!paper) {
    return (
      <div className="flex flex-col items-center justify-center h-full">
        <p className="text-gray-500">Paper not found</p>
        <Link to="/queue" className="text-primary-600 hover:underline mt-2">
          Back to queue
        </Link>
      </div>
    );
  }

  const review = paper.claude_review;
  const pdfUrl = papersApi.getPdfUrl(paperId!);
  const hasPdf = paper.pdf_url && paper.pdf_url.length > 0;

  return (
    <div className="flex h-full">
      {/* PDF Viewer */}
      <div className="flex-1 flex flex-col">
        <div className="p-4 bg-white border-b border-gray-200 flex items-center gap-4">
          <Link
            to="/queue"
            className="p-2 hover:bg-gray-100 rounded-lg text-gray-600"
          >
            <ArrowLeft size={20} />
          </Link>

          <div className="flex-1 min-w-0">
            <h1 className="font-medium text-gray-900 truncate">{paper.title}</h1>
            <p className="text-sm text-gray-500 truncate">
              {paper.authors.join(', ')}
              {paper.year && ` (${paper.year})`}
            </p>
          </div>

          <div className="flex items-center gap-2">
            {paper.status === 'processing' && (
              <span className="flex items-center gap-1 px-3 py-1.5 text-sm bg-yellow-50 text-yellow-700 rounded-lg">
                <span className="w-2 h-2 bg-yellow-500 rounded-full animate-pulse" />
                Processing...
              </span>
            )}

            <button
              onClick={() => saveLiteNoteMutation.mutate()}
              disabled={saveLiteNoteMutation.isPending}
              className="flex items-center gap-1 px-3 py-1.5 text-sm bg-primary-50 text-primary-700 rounded-lg hover:bg-primary-100"
            >
              <FileText size={16} />
              {saveLiteNoteMutation.isPending ? 'Saving...' : 'Save Note'}
            </button>

            {paper.source_url && (
              <a
                href={paper.source_url}
                target="_blank"
                rel="noopener noreferrer"
                className="p-2 hover:bg-gray-100 rounded-lg text-gray-600"
              >
                <ExternalLink size={20} />
              </a>
            )}
          </div>
        </div>

        {hasPdf ? (
          <PDFViewer
            url={pdfUrl}
            annotations={annotations || []}
            onTextSelect={handleTextSelect}
            onAnnotationClick={handleAnnotationClick}
          />
        ) : (
          <div className="flex-1 flex items-center justify-center bg-gray-100">
            <div className="text-center">
              <FileText size={64} className="mx-auto mb-4 text-gray-300" />
              <p className="text-gray-500 mb-4">No PDF available</p>
              <label className="inline-flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 cursor-pointer">
                <Upload size={18} />
                Upload PDF
                <input
                  type="file"
                  accept=".pdf"
                  className="hidden"
                  onChange={async (e) => {
                    const file = e.target.files?.[0];
                    if (file) {
                      await papersApi.uploadPdf(paperId!, file);
                      queryClient.invalidateQueries({ queryKey: ['paper', paperId] });
                    }
                  }}
                />
              </label>
            </div>
          </div>
        )}
      </div>

      {/* Text selection popover */}
      {selection && (
        <TextSelectionPopover
          selectedText={selection.text}
          position={selection.position}
          onHighlight={handleHighlight}
          onAddNote={handleAddNote}
          onAskClaude={handleAskClaude}
          onClose={() => setSelection(null)}
        />
      )}

      {/* Side panel */}
      <div className="w-96 border-l border-gray-200 bg-white flex flex-col">
        {/* Tabs */}
        <div className="flex border-b border-gray-200">
          {[
            { id: 'review' as const, icon: Lightbulb, label: 'Review' },
            { id: 'annotations' as const, icon: Bookmark, label: `Annotations (${annotations?.length || 0})` },
            { id: 'chat' as const, icon: MessageSquare, label: 'Chat' },
          ].map(({ id, icon: Icon, label }) => (
            <button
              key={id}
              onClick={() => setActiveTab(id)}
              className={clsx(
                'flex-1 flex items-center justify-center gap-2 py-3 text-sm font-medium border-b-2 transition-colors',
                activeTab === id
                  ? 'border-primary-600 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              )}
            >
              <Icon size={16} />
              {label}
            </button>
          ))}
        </div>

        {/* Tab content */}
        <div className="flex-1 overflow-auto">
          {activeTab === 'review' && (
            <div className="p-4 space-y-4">
              {paper.status === 'processing' ? (
                <div className="text-center py-8">
                  <div className="w-8 h-8 border-2 border-primary-600 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
                  <p className="text-gray-600">Claude is reviewing this paper...</p>
                  <p className="text-sm text-gray-500 mt-1">This may take a few minutes</p>
                </div>
              ) : review ? (
                <>
                  <div>
                    <h3 className="font-medium text-gray-900 mb-2">Summary</h3>
                    <p className="text-sm text-gray-700 whitespace-pre-wrap">
                      {review.summary}
                    </p>
                  </div>

                  {review.key_contributions?.length > 0 && (
                    <div>
                      <h3 className="font-medium text-gray-900 mb-2">
                        Key Contributions
                      </h3>
                      <ul className="space-y-1">
                        {review.key_contributions.map((contrib: string, i: number) => (
                          <li key={i} className="text-sm text-gray-700 flex gap-2">
                            <span className="text-primary-600">•</span>
                            {contrib}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {review.relevance_analysis && (
                    <div>
                      <h3 className="font-medium text-gray-900 mb-2">
                        Relevance to Your Research
                      </h3>
                      <p className="text-sm text-gray-700">
                        {review.relevance_analysis}
                      </p>
                    </div>
                  )}

                  {review.discussion_questions?.length > 0 && (
                    <div>
                      <h3 className="font-medium text-gray-900 mb-2">
                        Discussion Questions
                      </h3>
                      <ul className="space-y-2">
                        {review.discussion_questions.map((q: string, i: number) => (
                          <li
                            key={i}
                            className="text-sm text-gray-700 p-2 bg-primary-50 rounded-lg cursor-pointer hover:bg-primary-100"
                            onClick={() => {
                              setActiveTab('chat');
                              setChatMessage(q + '\n\n');
                            }}
                          >
                            {q}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  <Lightbulb size={32} className="mx-auto mb-2 opacity-50" />
                  <p>No review yet</p>
                  <p className="text-sm">Upload a PDF to generate a review</p>
                </div>
              )}
            </div>
          )}

          {activeTab === 'annotations' && (
            <div className="p-4">
              {!annotations?.length ? (
                <div className="text-center py-8 text-gray-500">
                  <Bookmark size={32} className="mx-auto mb-2 opacity-50" />
                  <p>No annotations yet</p>
                  <p className="text-sm">Select text in the PDF to add annotations</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {annotations.map((ann) => (
                    <div
                      key={ann.id}
                      className={clsx(
                        'p-3 rounded-lg border',
                        ann.type === 'highlight' && 'bg-yellow-50 border-yellow-200',
                        ann.type === 'note' && 'bg-blue-50 border-blue-200',
                        ann.type === 'question' && 'bg-purple-50 border-purple-200'
                      )}
                    >
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-xs text-gray-500">
                          Page {ann.page_number}
                        </span>
                        <span className="text-xs px-1.5 py-0.5 bg-white rounded text-gray-600">
                          {ann.type}
                        </span>
                      </div>
                      {ann.selected_text && (
                        <p className="text-sm text-gray-600 italic mb-2 line-clamp-2">
                          "{ann.selected_text}"
                        </p>
                      )}
                      <p className="text-sm text-gray-700">{ann.content}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {activeTab === 'chat' && (
            <div className="flex flex-col h-full">
              <div className="flex-1 p-4 space-y-4 overflow-auto">
                {!messages?.length && (
                  <div className="text-center py-8 text-gray-500">
                    <MessageSquare size={32} className="mx-auto mb-2 opacity-50" />
                    <p>Start a conversation</p>
                    <p className="text-sm">Ask Claude about this paper</p>
                  </div>
                )}

                {messages?.map((msg: ChatMessage) => (
                  <div
                    key={msg.id}
                    className={clsx(
                      'p-3 rounded-lg max-w-[85%]',
                      msg.role === 'user'
                        ? 'ml-auto bg-primary-600 text-white'
                        : 'bg-gray-100 text-gray-800'
                    )}
                  >
                    <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                  </div>
                ))}

                {sendMessageMutation.isPending && (
                  <div className="p-3 rounded-lg bg-gray-100 max-w-[85%]">
                    <div className="flex gap-1">
                      <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
                      <span
                        className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                        style={{ animationDelay: '0.1s' }}
                      />
                      <span
                        className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                        style={{ animationDelay: '0.2s' }}
                      />
                    </div>
                  </div>
                )}
              </div>

              <div className="p-4 border-t border-gray-200">
                <div className="flex gap-2">
                  <textarea
                    value={chatMessage}
                    onChange={(e) => setChatMessage(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault();
                        handleSendMessage();
                      }
                    }}
                    placeholder="Ask about this paper..."
                    rows={2}
                    className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 resize-none"
                  />
                  <button
                    onClick={handleSendMessage}
                    disabled={!chatMessage.trim() || sendMessageMutation.isPending}
                    className="p-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 self-end"
                  >
                    <Send size={20} />
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
