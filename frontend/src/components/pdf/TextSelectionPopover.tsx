import { useState, useEffect, useRef } from 'react';
import { Highlighter, StickyNote, MessageSquare, X } from 'lucide-react';

interface TextSelectionPopoverProps {
  selectedText: string;
  position: { x: number; y: number };
  onHighlight: () => void;
  onAddNote: (note: string) => void;
  onAskClaude: () => void;
  onClose: () => void;
}

export default function TextSelectionPopover({
  selectedText,
  position,
  onHighlight,
  onAddNote,
  onAskClaude,
  onClose,
}: TextSelectionPopoverProps) {
  const [showNoteInput, setShowNoteInput] = useState(false);
  const [noteText, setNoteText] = useState('');
  const popoverRef = useRef<HTMLDivElement>(null);

  // Close on outside click
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (popoverRef.current && !popoverRef.current.contains(event.target as Node)) {
        onClose();
      }
    }

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [onClose]);

  // Close on escape key
  useEffect(() => {
    function handleEscape(event: KeyboardEvent) {
      if (event.key === 'Escape') {
        onClose();
      }
    }

    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [onClose]);

  const handleAddNote = () => {
    if (noteText.trim()) {
      onAddNote(noteText.trim());
      setNoteText('');
      setShowNoteInput(false);
    }
  };

  return (
    <div
      ref={popoverRef}
      className="fixed z-50 bg-white rounded-lg shadow-xl border border-gray-200 overflow-hidden"
      style={{
        left: Math.max(10, Math.min(position.x - 100, window.innerWidth - 220)),
        top: Math.max(10, position.y + 10),
      }}
    >
      {!showNoteInput ? (
        <div className="flex items-center">
          <button
            onClick={onHighlight}
            className="flex items-center gap-2 px-3 py-2 hover:bg-yellow-50 text-gray-700 transition-colors"
            title="Highlight"
          >
            <Highlighter size={18} className="text-yellow-500" />
            <span className="text-sm">Highlight</span>
          </button>

          <div className="w-px h-8 bg-gray-200" />

          <button
            onClick={() => setShowNoteInput(true)}
            className="flex items-center gap-2 px-3 py-2 hover:bg-blue-50 text-gray-700 transition-colors"
            title="Add note"
          >
            <StickyNote size={18} className="text-blue-500" />
            <span className="text-sm">Note</span>
          </button>

          <div className="w-px h-8 bg-gray-200" />

          <button
            onClick={onAskClaude}
            className="flex items-center gap-2 px-3 py-2 hover:bg-purple-50 text-gray-700 transition-colors"
            title="Ask Claude"
          >
            <MessageSquare size={18} className="text-purple-500" />
            <span className="text-sm">Ask Claude</span>
          </button>

          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 text-gray-400 transition-colors"
          >
            <X size={16} />
          </button>
        </div>
      ) : (
        <div className="p-3 w-72">
          <div className="mb-2">
            <p className="text-xs text-gray-500 mb-1">Selected text:</p>
            <p className="text-sm text-gray-700 line-clamp-2 italic">
              "{selectedText.slice(0, 100)}{selectedText.length > 100 ? '...' : ''}"
            </p>
          </div>

          <textarea
            value={noteText}
            onChange={(e) => setNoteText(e.target.value)}
            placeholder="Add your note..."
            className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 resize-none"
            rows={3}
            autoFocus
          />

          <div className="flex justify-end gap-2 mt-2">
            <button
              onClick={() => {
                setShowNoteInput(false);
                setNoteText('');
              }}
              className="px-3 py-1.5 text-sm text-gray-600 hover:bg-gray-100 rounded"
            >
              Cancel
            </button>
            <button
              onClick={handleAddNote}
              disabled={!noteText.trim()}
              className="px-3 py-1.5 text-sm bg-primary-600 text-white rounded hover:bg-primary-700 disabled:opacity-50"
            >
              Save Note
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
