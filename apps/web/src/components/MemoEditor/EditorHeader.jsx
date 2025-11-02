import {
  ArrowLeft,
  Eye,
  Edit3,
  Download,
  Quote,
  BookOpen,
  MessageCircle,
} from "lucide-react";
import { ExportDropdown } from "./ExportDropdown";

export function EditorHeader({
  memoData,
  activeTab,
  setActiveTab,
  pageWidth,
  setPageWidth,
  showExportDropdown,
  setShowExportDropdown,
  exportToPDF,
  exportToWord,
  copyShareLink,
  setShowCitationModal,
  addBibliographySection,
  showChat,
  setShowChat,
}) {
  return (
    <header className="bg-white border-b border-gray-200 sticky top-0 z-40">
      <div className="flex items-center justify-between px-6 py-3">
        <div className="flex items-center space-x-4">
          <button
            onClick={() => (window.location.href = "/workspace")}
            className="flex items-center space-x-2 text-gray-600 hover:text-gray-800"
          >
            <ArrowLeft size={20} />
            <span>Back to Workspace</span>
          </button>
          <div className="h-6 border-l border-gray-300"></div>
          <h1 className="text-lg font-semibold text-gray-800">
            Investment Memo
          </h1>
          <span className="text-sm text-gray-500">
            {memoData?.metadata?.generated &&
              new Date(memoData.metadata.generated).toLocaleDateString()}
          </span>
        </div>

        {/* Toolbar */}
        <div className="flex items-center space-x-2">
          {/* View Mode Tabs */}
          <div className="flex bg-gray-100 rounded-lg p-1">
            <button
              onClick={() => setActiveTab("preview")}
              className={`px-3 py-1.5 text-sm font-medium rounded-md transition-colors ${
                activeTab === "preview"
                  ? "bg-white text-gray-800 shadow-sm"
                  : "text-gray-600 hover:text-gray-800"
              }`}
            >
              <Eye size={16} className="inline mr-1" />
              Preview
            </button>
            <button
              onClick={() => setActiveTab("edit")}
              className={`px-3 py-1.5 text-sm font-medium rounded-md transition-colors ${
                activeTab === "edit"
                  ? "bg-white text-gray-800 shadow-sm"
                  : "text-gray-600 hover:text-gray-800"
              }`}
            >
              <Edit3 size={16} className="inline mr-1" />
              Edit
            </button>
          </div>

          <div className="h-6 border-l border-gray-300"></div>

          {/* Page Width Control */}
          <select
            value={pageWidth}
            onChange={(e) => setPageWidth(e.target.value)}
            className="text-sm border border-gray-300 rounded-md px-2 py-1"
          >
            <option value="narrow">Narrow</option>
            <option value="standard">Standard</option>
            <option value="wide">Wide</option>
          </select>

          {/* Export Dropdown */}
          <ExportDropdown
            showExportDropdown={showExportDropdown}
            setShowExportDropdown={setShowExportDropdown}
            exportToPDF={exportToPDF}
            exportToWord={exportToWord}
            copyShareLink={copyShareLink}
          />

          {/* Citation Tools */}
          {activeTab === "edit" && (
            <>
              <button
                onClick={() => setShowCitationModal(true)}
                className="flex items-center space-x-2 px-3 py-1.5 bg-gray-100 text-gray-600 rounded-md hover:bg-gray-200"
              >
                <Quote size={16} />
                <span>Insert Citation</span>
              </button>
              <button
                onClick={addBibliographySection}
                className="flex items-center space-x-2 px-3 py-1.5 bg-gray-100 text-gray-600 rounded-md hover:bg-gray-200"
              >
                <BookOpen size={16} />
                <span>Add Bibliography</span>
              </button>
            </>
          )}

          {/* Chat Toggle */}
          <button
            onClick={() => setShowChat(!showChat)}
            className={`flex items-center space-x-2 px-3 py-1.5 rounded-md transition-colors ${
              showChat
                ? "bg-green-100 text-green-700"
                : "bg-gray-100 text-gray-600 hover:bg-gray-200"
            }`}
          >
            <MessageCircle size={16} />
            <span>AI Assistant</span>
          </button>
        </div>
      </div>
    </header>
  );
}
