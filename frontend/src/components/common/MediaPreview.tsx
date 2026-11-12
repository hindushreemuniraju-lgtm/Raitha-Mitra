import { useState } from "react";
import { Download, Eye, FileText, ImageOff, Maximize2, X } from "lucide-react";

interface MediaPreviewProps {
  url?: string | null;
  filename?: string | null;
  mimeType?: string | null;
  kind?: "image" | "pdf" | string | null;
  alt?: string;
  aspectClass?: string;
  compact?: boolean;
}

export function MediaPreview({
  url,
  filename,
  mimeType,
  kind,
  alt = "Uploaded farm document",
  aspectClass = "h-48",
  compact = false,
}: MediaPreviewProps) {
  const [imgLoading, setImgLoading] = useState(true);
  const [imgError, setImgError] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);

  const lowerName = (filename || "").toLowerCase();
  const isPdf =
    kind === "pdf" ||
    mimeType === "application/pdf" ||
    lowerName.endsWith(".pdf");

  if (!url) {
    return null;
  }

  const downloadHref = url.includes("?") ? `${url}&download=1` : `${url}?download=1`;
  const displayName = filename || (isPdf ? "Farm Document.pdf" : "Uploaded Photo");

  return (
    <>
      {isPdf ? (
        <div className="rounded-xl border border-[#DCE8D8] bg-[#FAF9F2] p-3.5 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center gap-3 min-w-0">
            <div className="h-11 w-11 rounded-lg bg-[#FCECEC] text-[#D9534F] flex items-center justify-center shrink-0 border border-[#F5C6C5]">
              <FileText className="w-5 h-5" />
            </div>
            <div className="min-w-0">
              <p className="text-sm font-medium text-[#202820] truncate" title={displayName}>
                {displayName}
              </p>
              <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-medium bg-[#EDF5E9] text-[#176B35] mt-0.5">
                PDF Document
              </span>
            </div>
          </div>

          <div className="flex items-center gap-2 shrink-0">
            <button
              type="button"
              onClick={() => setModalOpen(true)}
              className="px-3 py-1.5 rounded-lg bg-[#176B35] hover:bg-[#104B29] text-white text-xs font-medium flex items-center gap-1.5 transition"
            >
              <Eye className="w-3.5 h-3.5" />
              View PDF
            </button>
            <a
              href={downloadHref}
              download={displayName}
              className="px-3 py-1.5 rounded-lg border border-[#DCE8D8] bg-white hover:bg-[#EDF5E9] text-[#202820] text-xs font-medium flex items-center gap-1.5 transition"
            >
              <Download className="w-3.5 h-3.5" />
              Download
            </a>
          </div>
        </div>
      ) : (
        <div className="group relative rounded-xl border border-[#DCE8D8] bg-[#FAF9F2] overflow-hidden">
          <div className={`relative w-full ${compact ? "h-32" : aspectClass} bg-[#EDF5E9]`}>
            {imgLoading && !imgError && (
              <div className="absolute inset-0 animate-pulse bg-gradient-to-r from-[#EDF5E9] via-[#E2EFDC] to-[#EDF5E9]" />
            )}

            {imgError ? (
              <div className="absolute inset-0 flex flex-col items-center justify-center text-center p-4 text-[#718071]">
                <ImageOff className="w-7 h-7 mb-1.5 text-[#D9534F]" />
                <p className="text-xs font-medium text-[#202820]">Unable to load image preview</p>
                <a
                  href={downloadHref}
                  download={displayName}
                  className="text-xs text-[#176B35] underline mt-1"
                >
                  Download file instead
                </a>
              </div>
            ) : (
              <img
                src={url}
                alt={alt || displayName}
                onLoad={() => setImgLoading(false)}
                onError={() => {
                  setImgLoading(false);
                  setImgError(true);
                }}
                onClick={() => setModalOpen(true)}
                className="w-full h-full object-cover cursor-pointer transition-transform duration-200 group-hover:scale-[1.02]"
              />
            )}

            {!imgError && (
              <button
                type="button"
                onClick={() => setModalOpen(true)}
                aria-label="Enlarge image"
                className="absolute top-2 right-2 p-1.5 rounded-lg bg-[#202820]/70 hover:bg-[#104B29] text-white opacity-90 sm:opacity-0 sm:group-hover:opacity-100 transition"
              >
                <Maximize2 className="w-4 h-4" />
              </button>
            )}
          </div>

          <div className="px-3 py-2 flex items-center justify-between gap-2 bg-white border-t border-[#E6EBE2]">
            <span className="text-xs font-medium text-[#202820] truncate" title={displayName}>
              {displayName}
            </span>
            <div className="flex items-center gap-2 shrink-0">
              <button
                type="button"
                onClick={() => setModalOpen(true)}
                className="text-xs font-medium text-[#176B35] hover:underline flex items-center gap-1"
              >
                <Eye className="w-3.5 h-3.5" /> View
              </button>
              <a
                href={downloadHref}
                download={displayName}
                className="text-xs font-medium text-[#718071] hover:text-[#176B35] flex items-center gap-1"
              >
                <Download className="w-3.5 h-3.5" />
              </a>
            </div>
          </div>
        </div>
      )}

      {/* Full Lightbox / Embedded PDF Document Viewer Modal */}
      {modalOpen && (
        <div
          className="fixed inset-0 z-50 bg-[#202820]/80 flex items-center justify-center p-3 sm:p-6"
          onClick={() => setModalOpen(false)}
        >
          <div
            className="bg-white rounded-2xl shadow-2xl max-w-4xl w-full max-h-[90vh] flex flex-col overflow-hidden"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="px-4 py-3 border-b border-[#E6EBE2] flex items-center justify-between gap-3 bg-[#FAF9F2]">
              <div className="min-w-0">
                <h3 className="text-sm font-semibold text-[#202820] truncate">{displayName}</h3>
                <p className="text-xs text-[#718071]">{isPdf ? "PDF Document Viewer" : "Full Image Preview"}</p>
              </div>
              <div className="flex items-center gap-2 shrink-0">
                <a
                  href={downloadHref}
                  download={displayName}
                  className="px-3 py-1.5 rounded-lg border border-[#DCE8D8] bg-white hover:bg-[#EDF5E9] text-xs font-medium text-[#202820] flex items-center gap-1.5"
                >
                  <Download className="w-3.5 h-3.5" />
                  Download
                </a>
                <button
                  type="button"
                  onClick={() => setModalOpen(false)}
                  className="p-1.5 rounded-lg hover:bg-[#EDF5E9] text-[#202820]"
                  aria-label="Close preview"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>

            <div className="flex-1 overflow-auto bg-[#202820]/5 flex items-center justify-center p-3">
              {isPdf ? (
                <iframe
                  src={url}
                  title={displayName}
                  className="w-full h-[75vh] rounded-lg border border-[#DCE8D8] bg-white"
                />
              ) : (
                <img
                  src={url}
                  alt={displayName}
                  className="max-w-full max-h-[75vh] object-contain rounded-lg shadow-sm"
                />
              )}
            </div>
          </div>
        </div>
      )}
    </>
  );
}
