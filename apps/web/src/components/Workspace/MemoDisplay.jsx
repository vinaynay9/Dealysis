import { MessageSquare, Copy, Download, Edit } from "lucide-react";

export function MemoDisplay({
  generatedMemo,
  streamingMemo,
  showResults,
  showChat,
  onToggleChat,
  onCopy,
  onDownload,
}) {
  return (
    <div className="bg-[#1A1B23] rounded-2xl p-6 border border-[#374151]">
      <div className="flex items-center justify-between mb-6">
        <h3
          className="text-lg font-semibold text-white"
          style={{ fontFamily: "Inter, sans-serif" }}
        >
          Generated Investment Memo
        </h3>
        {showResults && (
          <div className="flex space-x-3">
            <button
              onClick={() => window.open("/memo-editor", "_blank")}
              className="flex items-center space-x-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
              style={{ fontFamily: "Inter, sans-serif" }}
            >
              <Edit size={16} />
              <span>Edit</span>
            </button>
            <button
              onClick={onToggleChat}
              className={`flex items-center space-x-2 px-4 py-2 ${showChat ? "bg-[#6366F1]" : "bg-[#374151]"} text-white rounded-lg hover:bg-[#6366F1] transition-colors`}
              style={{ fontFamily: "Inter, sans-serif" }}
            >
              <MessageSquare size={16} />
              <span>Chat</span>
            </button>
            <button
              onClick={onCopy}
              className="flex items-center space-x-2 px-4 py-2 bg-[#374151] text-white rounded-lg hover:bg-[#4B5563] transition-colors"
              style={{ fontFamily: "Inter, sans-serif" }}
            >
              <Copy size={16} />
              <span>Copy</span>
            </button>
            <button
              onClick={onDownload}
              className="flex items-center space-x-2 px-4 py-2 bg-gradient-to-r from-[#6366F1] to-[#8B5CF6] text-white rounded-lg hover:from-[#5B61F0] hover:to-[#7C3AED] transition-colors"
              style={{ fontFamily: "Inter, sans-serif" }}
            >
              <Download size={16} />
              <span>Download</span>
            </button>
          </div>
        )}
      </div>

      <div className="bg-[#374151] rounded-xl p-6 max-h-[600px] overflow-y-auto">
        <div
          className="prose max-w-none text-white"
          style={{
            fontFamily: "Inter, sans-serif",
            lineHeight: "1.6",
          }}
        >
          {showResults ? (
            <pre className="whitespace-pre-wrap font-sans text-sm leading-relaxed">
              {generatedMemo}
            </pre>
          ) : (
            <div className="text-gray-300 italic">
              {streamingMemo || "Generating your investment memo..."}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
