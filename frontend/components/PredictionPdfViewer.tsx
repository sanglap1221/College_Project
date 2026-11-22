"use client";

import React, { useEffect, useRef, useState } from "react";
import { LoadingSpinner } from "./LoadingSpinner";

interface PredictionPdfViewerProps {
  pdfUrl: string;
  downloadFilename?: string;
  onReload?: () => void;
}

declare global {
  interface Window {
    pdfjsLib?: any;
  }
}

export function PredictionPdfViewer({
  pdfUrl,
  downloadFilename = "prediction_report.pdf",
  onReload,
}: PredictionPdfViewerProps) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const [pdfDoc, setPdfDoc] = useState<any>(null);
  const [currentPage, setCurrentPage] = useState<number>(1);
  const [numPages, setNumPages] = useState<number>(1);
  const [scale, setScale] = useState<number>(1.15);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string>("");
  const [useIframeFallback, setUseIframeFallback] = useState<boolean>(false);
  const [elapsedSeconds, setElapsedSeconds] = useState<number>(0);

  useEffect(() => {
    let timer: any;
    if (loading) {
      setElapsedSeconds(0);
      const startTime = Date.now();
      timer = setInterval(() => {
        setElapsedSeconds(Math.floor((Date.now() - startTime) / 1000));
      }, 1000);
    } else {
      setElapsedSeconds(0);
    }
    return () => {
      if (timer) clearInterval(timer);
    };
  }, [loading]);

  // Load PDF.js from CDN if not already loaded
  useEffect(() => {
    let isMounted = true;

    async function loadPdfJs() {
      if (typeof window === "undefined") return;

      if (!window.pdfjsLib) {
        try {
          const script = document.createElement("script");
          script.src = "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js";
          script.async = true;

          const loadPromise = new Promise((resolve, reject) => {
            script.onload = () => resolve(true);
            script.onerror = () => reject(new Error("Failed to load PDF.js from CDN"));
          });

          document.body.appendChild(script);
          await loadPromise;

          if (window.pdfjsLib) {
            window.pdfjsLib.GlobalWorkerOptions.workerSrc =
              "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js";
          }
        } catch (err) {
          console.warn("PDF.js CDN load failed, falling back to browser viewer:", err);
          if (isMounted) {
            setUseIframeFallback(true);
            setLoading(false);
          }
          return;
        }
      }

      // Load Document
      if (window.pdfjsLib && pdfUrl) {
        try {
          setLoading(true);
          setError("");
          const loadingTask = window.pdfjsLib.getDocument({
            url: pdfUrl,
            withCredentials: false,
          });
          const doc = await loadingTask.promise;
          if (isMounted) {
            setPdfDoc(doc);
            setNumPages(doc.numPages);
            setCurrentPage(1);
            setLoading(false);
          }
        } catch (err: any) {
          console.error("PDF load error:", err);
          if (isMounted) {
            setError(err.message || "Failed to load PDF");
            setUseIframeFallback(true);
            setLoading(false);
          }
        }
      }
    }

    loadPdfJs();

    return () => {
      isMounted = false;
    };
  }, [pdfUrl]);

  // Render current page onto canvas
  useEffect(() => {
    if (!pdfDoc || !canvasRef.current || useIframeFallback) return;

    let renderTask: any = null;

    async function renderPage() {
      try {
        const page = await pdfDoc.getPage(currentPage);
        const viewport = page.getViewport({ scale });
        const canvas = canvasRef.current;
        if (!canvas) return;

        const context = canvas.getContext("2d");
        if (!context) return;

        canvas.height = viewport.height;
        canvas.width = viewport.width;

        const renderContext = {
          canvasContext: context,
          viewport: viewport,
        };

        renderTask = page.render(renderContext);
        await renderTask.promise;
      } catch (err: any) {
        if (err.name !== "RenderingCancelledException") {
          console.warn("PDF page render warning:", err);
        }
      }
    }

    renderPage();

    return () => {
      if (renderTask) {
        renderTask.cancel();
      }
    };
  }, [pdfDoc, currentPage, scale, useIframeFallback]);

  const handlePrevPage = () => {
    if (currentPage > 1) setCurrentPage((prev) => prev - 1);
  };

  const handleNextPage = () => {
    if (currentPage < numPages) setCurrentPage((prev) => prev + 1);
  };

  const handleZoomIn = () => {
    setScale((prev) => Math.min(prev + 0.15, 2.2));
  };

  const handleZoomOut = () => {
    setScale((prev) => Math.max(prev - 0.15, 0.65));
  };

  const handleResetZoom = () => {
    setScale(1.15);
  };

  return (
    <div className="flex flex-col h-full w-full bg-[#f8fafc] border border-slate-200 rounded-xl overflow-hidden shadow-inner">
      {/* ── PDF Controls Toolbar ── */}
      <div className="flex items-center justify-between px-3 py-2 bg-white border-b border-slate-200 text-xs text-slate-700 select-none">
        {/* Pagination */}
        <div className="flex items-center gap-1.5">
          <button
            onClick={handlePrevPage}
            disabled={currentPage <= 1 || loading}
            className="w-7 h-7 rounded flex items-center justify-center bg-slate-100 hover:bg-slate-200 disabled:opacity-40 transition-colors"
            title="Previous Page"
          >
            <i className="fa-solid fa-chevron-left text-[11px]"></i>
          </button>
          <span className="font-semibold text-slate-700 min-w-[58px] text-center">
            {loading ? "..." : `${currentPage} / ${numPages}`}
          </span>
          <button
            onClick={handleNextPage}
            disabled={currentPage >= numPages || loading}
            className="w-7 h-7 rounded flex items-center justify-center bg-slate-100 hover:bg-slate-200 disabled:opacity-40 transition-colors"
            title="Next Page"
          >
            <i className="fa-solid fa-chevron-right text-[11px]"></i>
          </button>
        </div>

        {/* Zoom Controls */}
        <div className="flex items-center gap-1">
          <button
            onClick={handleZoomOut}
            disabled={loading}
            className="w-7 h-7 rounded flex items-center justify-center bg-slate-100 hover:bg-slate-200 transition-colors"
            title="Zoom Out"
          >
            <i className="fa-solid fa-minus text-[10px]"></i>
          </button>
          <button
            onClick={handleResetZoom}
            className="px-1.5 py-1 text-[11px] font-mono text-slate-600 hover:text-slate-900"
            title="Reset Zoom"
          >
            {Math.round(scale * 100)}%
          </button>
          <button
            onClick={handleZoomIn}
            disabled={loading}
            className="w-7 h-7 rounded flex items-center justify-center bg-slate-100 hover:bg-slate-200 transition-colors"
            title="Zoom In"
          >
            <i className="fa-solid fa-plus text-[10px]"></i>
          </button>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-1.5">
          {onReload && (
            <button
              onClick={onReload}
              className="w-7 h-7 rounded flex items-center justify-center bg-slate-100 hover:bg-slate-200 text-slate-600 transition-colors"
              title="Reload PDF"
            >
              <i className="fa-solid fa-rotate-right text-[11px]"></i>
            </button>
          )}
          <a
            href={pdfUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="w-7 h-7 rounded flex items-center justify-center bg-slate-100 hover:bg-slate-200 text-slate-600 transition-colors"
            title="Open in New Tab"
          >
            <i className="fa-solid fa-arrow-up-right-from-square text-[11px]"></i>
          </a>
          <a
            href={pdfUrl}
            download={downloadFilename}
            className="px-2.5 py-1 rounded bg-[#800020] hover:bg-[#600018] text-white text-[11px] font-medium flex items-center gap-1 transition-colors shadow-sm"
            title="Download PDF"
          >
            <i className="fa-solid fa-download text-[10px]"></i> Download
          </a>
        </div>
      </div>

      {/* ── Document View Area ── */}
      <div className="flex-1 overflow-auto p-4 flex items-center justify-center relative bg-[#475569]/10">
        {loading && (
          <div className="absolute inset-0 bg-white/80 backdrop-blur-sm flex flex-col items-center justify-center gap-3 z-10 text-slate-600">
            <LoadingSpinner />
            <span className="text-xs font-medium">Loading report preview...</span>
            <span className="text-[10px] text-slate-400">
              This may take a few seconds on first load {elapsedSeconds > 0 ? `(${elapsedSeconds}s)` : ""}
            </span>
          </div>
        )}

        {useIframeFallback ? (
          <iframe
            src={pdfUrl}
            className="w-full h-full min-h-[550px] border-0 rounded bg-white shadow-md"
            title="PDF preview fallback"
          />
        ) : (
          <div className="inline-block bg-white shadow-xl rounded-md overflow-hidden transition-all duration-150">
            <canvas ref={canvasRef} className="block max-w-full" />
          </div>
        )}
      </div>
    </div>
  );
}
