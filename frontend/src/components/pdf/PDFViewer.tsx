import { useEffect, useRef, useState, useCallback } from 'react';
import * as pdfjsLib from 'pdfjs-dist';
import type { PDFDocumentProxy, PDFPageProxy } from 'pdfjs-dist';
import { ChevronLeft, ChevronRight, ZoomIn, ZoomOut, Loader2 } from 'lucide-react';
import type { Annotation } from '../../types';

// Set up PDF.js worker
pdfjsLib.GlobalWorkerOptions.workerSrc = `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjsLib.version}/pdf.worker.min.js`;

interface PDFViewerProps {
  url: string;
  annotations?: Annotation[];
  onTextSelect?: (text: string, pageNumber: number, position: SelectionPosition) => void;
  onAnnotationClick?: (annotation: Annotation) => void;
}

interface SelectionPosition {
  rects: Array<{ x: number; y: number; width: number; height: number }>;
  pageIndex: number;
}

export default function PDFViewer({
  url,
  annotations = [],
  onTextSelect,
  onAnnotationClick,
}: PDFViewerProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [pdfDoc, setPdfDoc] = useState<PDFDocumentProxy | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [numPages, setNumPages] = useState(0);
  const [scale, setScale] = useState(1.2);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [renderedPages, setRenderedPages] = useState<Set<number>>(new Set());

  // Load PDF document
  useEffect(() => {
    let cancelled = false;

    async function loadPDF() {
      try {
        setLoading(true);
        setError(null);

        const loadingTask = pdfjsLib.getDocument(url);
        const pdf = await loadingTask.promise;

        if (!cancelled) {
          setPdfDoc(pdf);
          setNumPages(pdf.numPages);
          setCurrentPage(1);
          setRenderedPages(new Set());
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : 'Failed to load PDF');
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    loadPDF();

    return () => {
      cancelled = true;
    };
  }, [url]);

  // Render a single page
  const renderPage = useCallback(
    async (pageNum: number, canvas: HTMLCanvasElement, textLayer: HTMLDivElement) => {
      if (!pdfDoc || renderedPages.has(pageNum)) return;

      try {
        const page = await pdfDoc.getPage(pageNum);
        const viewport = page.getViewport({ scale });

        // Set canvas dimensions
        canvas.height = viewport.height;
        canvas.width = viewport.width;

        const context = canvas.getContext('2d');
        if (!context) return;

        // Render PDF page
        await page.render({
          canvasContext: context,
          viewport,
        }).promise;

        // Render text layer for selection
        const textContent = await page.getTextContent();
        textLayer.innerHTML = '';
        textLayer.style.width = `${viewport.width}px`;
        textLayer.style.height = `${viewport.height}px`;

        // Create text layer items
        textContent.items.forEach((item: any) => {
          const div = document.createElement('span');
          const tx = pdfjsLib.Util.transform(viewport.transform, item.transform);

          div.textContent = item.str;
          div.style.position = 'absolute';
          div.style.left = `${tx[4]}px`;
          div.style.top = `${tx[5] - item.height}px`;
          div.style.fontSize = `${item.height}px`;
          div.style.fontFamily = item.fontName || 'sans-serif';
          div.style.color = 'transparent';
          div.style.whiteSpace = 'pre';
          div.style.transformOrigin = '0 0';
          div.style.transform = `scaleX(${item.width / (item.str.length * item.height * 0.5) || 1})`;

          textLayer.appendChild(div);
        });

        setRenderedPages((prev) => new Set([...prev, pageNum]));
      } catch (err) {
        console.error(`Error rendering page ${pageNum}:`, err);
      }
    },
    [pdfDoc, scale, renderedPages]
  );

  // Handle text selection
  const handleMouseUp = useCallback(() => {
    if (!onTextSelect) return;

    const selection = window.getSelection();
    if (!selection || selection.isCollapsed) return;

    const text = selection.toString().trim();
    if (!text) return;

    // Get selection range and position
    const range = selection.getRangeAt(0);
    const rects = Array.from(range.getClientRects()).map((rect) => ({
      x: rect.x,
      y: rect.y,
      width: rect.width,
      height: rect.height,
    }));

    // Find which page the selection is on
    const container = containerRef.current;
    if (!container) return;

    const pageElements = container.querySelectorAll('[data-page-number]');
    let pageNumber = currentPage;

    pageElements.forEach((el) => {
      const pageRect = el.getBoundingClientRect();
      const selectionRect = rects[0];
      if (
        selectionRect &&
        selectionRect.y >= pageRect.top &&
        selectionRect.y <= pageRect.bottom
      ) {
        pageNumber = parseInt(el.getAttribute('data-page-number') || '1', 10);
      }
    });

    onTextSelect(text, pageNumber, { rects, pageIndex: pageNumber - 1 });
  }, [onTextSelect, currentPage]);

  // Navigation handlers
  const goToPage = (page: number) => {
    if (page >= 1 && page <= numPages) {
      setCurrentPage(page);
    }
  };

  const zoomIn = () => setScale((s) => Math.min(s + 0.2, 3));
  const zoomOut = () => setScale((s) => Math.max(s - 0.2, 0.5));

  // Reset rendered pages when scale changes
  useEffect(() => {
    setRenderedPages(new Set());
  }, [scale]);

  // Get annotations for current page
  const pageAnnotations = annotations.filter((a) => a.page_number === currentPage);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full bg-gray-100">
        <div className="text-center">
          <Loader2 className="w-8 h-8 animate-spin text-primary-600 mx-auto mb-2" />
          <p className="text-gray-500">Loading PDF...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-full bg-gray-100">
        <div className="text-center text-red-600">
          <p className="font-medium">Failed to load PDF</p>
          <p className="text-sm">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full bg-gray-100">
      {/* Toolbar */}
      <div className="flex items-center justify-between px-4 py-2 bg-white border-b border-gray-200">
        <div className="flex items-center gap-2">
          <button
            onClick={() => goToPage(currentPage - 1)}
            disabled={currentPage <= 1}
            className="p-1.5 rounded hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <ChevronLeft size={20} />
          </button>

          <span className="text-sm text-gray-600">
            Page{' '}
            <input
              type="number"
              value={currentPage}
              onChange={(e) => goToPage(parseInt(e.target.value, 10))}
              className="w-12 px-1 py-0.5 text-center border border-gray-300 rounded"
              min={1}
              max={numPages}
            />{' '}
            of {numPages}
          </span>

          <button
            onClick={() => goToPage(currentPage + 1)}
            disabled={currentPage >= numPages}
            className="p-1.5 rounded hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <ChevronRight size={20} />
          </button>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={zoomOut}
            className="p-1.5 rounded hover:bg-gray-100"
            title="Zoom out"
          >
            <ZoomOut size={20} />
          </button>
          <span className="text-sm text-gray-600 w-16 text-center">
            {Math.round(scale * 100)}%
          </span>
          <button
            onClick={zoomIn}
            className="p-1.5 rounded hover:bg-gray-100"
            title="Zoom in"
          >
            <ZoomIn size={20} />
          </button>
        </div>
      </div>

      {/* PDF Content */}
      <div
        ref={containerRef}
        className="flex-1 overflow-auto p-4"
        onMouseUp={handleMouseUp}
      >
        <div className="flex flex-col items-center gap-4">
          {Array.from({ length: numPages }, (_, i) => i + 1).map((pageNum) => (
            <PDFPage
              key={pageNum}
              pageNum={pageNum}
              pdfDoc={pdfDoc}
              scale={scale}
              isVisible={Math.abs(pageNum - currentPage) <= 2}
              annotations={annotations.filter((a) => a.page_number === pageNum)}
              onAnnotationClick={onAnnotationClick}
              renderPage={renderPage}
            />
          ))}
        </div>
      </div>
    </div>
  );
}

interface PDFPageProps {
  pageNum: number;
  pdfDoc: PDFDocumentProxy | null;
  scale: number;
  isVisible: boolean;
  annotations: Annotation[];
  onAnnotationClick?: (annotation: Annotation) => void;
  renderPage: (
    pageNum: number,
    canvas: HTMLCanvasElement,
    textLayer: HTMLDivElement
  ) => Promise<void>;
}

function PDFPage({
  pageNum,
  pdfDoc,
  scale,
  isVisible,
  annotations,
  onAnnotationClick,
  renderPage,
}: PDFPageProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const textLayerRef = useRef<HTMLDivElement>(null);
  const [dimensions, setDimensions] = useState({ width: 0, height: 0 });

  useEffect(() => {
    async function setup() {
      if (!pdfDoc) return;

      const page = await pdfDoc.getPage(pageNum);
      const viewport = page.getViewport({ scale });
      setDimensions({ width: viewport.width, height: viewport.height });
    }

    setup();
  }, [pdfDoc, pageNum, scale]);

  useEffect(() => {
    if (isVisible && canvasRef.current && textLayerRef.current && pdfDoc) {
      renderPage(pageNum, canvasRef.current, textLayerRef.current);
    }
  }, [isVisible, pdfDoc, pageNum, renderPage]);

  return (
    <div
      className="relative bg-white shadow-lg"
      data-page-number={pageNum}
      style={{
        width: dimensions.width || 'auto',
        height: dimensions.height || 'auto',
        minHeight: 200,
      }}
    >
      <canvas ref={canvasRef} className="block" />

      {/* Text layer for selection */}
      <div
        ref={textLayerRef}
        className="absolute top-0 left-0 overflow-hidden pointer-events-auto select-text"
        style={{
          width: dimensions.width,
          height: dimensions.height,
        }}
      />

      {/* Annotation layer */}
      <div className="absolute top-0 left-0 w-full h-full pointer-events-none">
        {annotations.map((annotation) => (
          <AnnotationHighlight
            key={annotation.id}
            annotation={annotation}
            scale={scale}
            onClick={() => onAnnotationClick?.(annotation)}
          />
        ))}
      </div>
    </div>
  );
}

interface AnnotationHighlightProps {
  annotation: Annotation;
  scale: number;
  onClick: () => void;
}

function AnnotationHighlight({ annotation, scale, onClick }: AnnotationHighlightProps) {
  if (!annotation.position?.rects?.length) return null;

  const colors: Record<string, string> = {
    highlight: 'bg-yellow-300/40 hover:bg-yellow-400/50',
    note: 'bg-blue-300/40 hover:bg-blue-400/50',
    question: 'bg-purple-300/40 hover:bg-purple-400/50',
  };

  return (
    <>
      {annotation.position.rects.map((rect, i) => (
        <div
          key={i}
          className={`absolute cursor-pointer pointer-events-auto transition-colors ${
            colors[annotation.type] || colors.highlight
          }`}
          style={{
            left: rect.x * scale,
            top: rect.y * scale,
            width: rect.width * scale,
            height: rect.height * scale,
          }}
          onClick={onClick}
          title={annotation.content}
        />
      ))}
    </>
  );
}
