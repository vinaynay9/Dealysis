import { Download, FileText, Share2 } from "lucide-react";

export function ExportDropdown({
  showExportDropdown,
  setShowExportDropdown,
  exportToPDF,
  exportToWord,
  copyShareLink,
}) {
  return (
    <div className="relative">
      <button
        onClick={() => setShowExportDropdown(!showExportDropdown)}
        className="flex items-center space-x-2 px-3 py-1.5 bg-blue-600 text-white rounded-md hover:bg-blue-700"
      >
        <Download size={16} />
        <span>Export</span>
      </button>
      {showExportDropdown && (
        <div className="absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg border border-gray-200 z-50">
          <button
            onClick={() => {
              exportToPDF();
              setShowExportDropdown(false);
            }}
            className="w-full text-left px-4 py-2 hover:bg-gray-100 flex items-center space-x-2"
          >
            <FileText size={16} />
            <span>Export as PDF</span>
          </button>
          <button
            onClick={() => {
              exportToWord();
              setShowExportDropdown(false);
            }}
            className="w-full text-left px-4 py-2 hover:bg-gray-100 flex items-center space-x-2"
          >
            <FileText size={16} />
            <span>Export as Word</span>
          </button>
          <button
            onClick={() => {
              copyShareLink();
              setShowExportDropdown(false);
            }}
            className="w-full text-left px-4 py-2 hover:bg-gray-100 flex items-center space-x-2"
          >
            <Share2 size={16} />
            <span>Copy Share Link</span>
          </button>
        </div>
      )}
    </div>
  );
}
