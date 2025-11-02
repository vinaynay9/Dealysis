import {
  Upload,
  FileText,
  Type,
  Link,
  File,
  Clock,
  CheckCircle,
  AlertCircle,
} from "lucide-react";
import { FileUploadZone } from "./FileUploadZone";
import { ContextInput } from "./ContextInput";
import { GenerateButton } from "./GenerateButton";

export function UploadSection({
  referenceFiles,
  exampleFiles,
  companyContext,
  isProcessing,
  processingStage,
  generationProgress, // NEW: Progress tracking for micro-prompt flow
  onReferenceUpload,
  onExampleUpload,
  onRemoveReferenceFile,
  onRemoveExampleFile,
  onContextChange,
  onGenerate,
  // Add new props for text and URL inputs
  activeTab,
  onTabChange,
  rawTextInput,
  onRawTextChange,
  rawTextLabel,
  onRawTextLabelChange,
  urlInput,
  onUrlChange,
  urlLabel,
  onUrlLabelChange,
  onAddText,
  onAddUrl,
  referenceTexts,
  referenceUrls,
  onRemoveText,
  onRemoveUrl,
  fileProcessingStatus = {},
}) {
  // Get total count of all reference materials
  const totalMaterials =
    referenceFiles.length + referenceTexts.length + referenceUrls.length;

  const getFileStatus = (fileName) => {
    const statusKey = Object.keys(fileProcessingStatus).find(
      (key) => fileProcessingStatus[key].fileName === fileName,
    );
    return statusKey ? fileProcessingStatus[statusKey] : null;
  };

  const getStatusIcon = (status) => {
    if (!status) return <File size={14} className="text-[#6366F1]" />;

    switch (status.status) {
      case "processing":
        return <Clock size={14} className="text-blue-400 animate-spin" />;
      case "completed":
        return <CheckCircle size={14} className="text-green-400" />;
      case "error":
        return <AlertCircle size={14} className="text-red-400" />;
      default:
        return <File size={14} className="text-[#6366F1]" />;
    }
  };

  const getStatusText = (status, fileName) => {
    if (!status) return fileName;

    switch (status.status) {
      case "processing":
        return `${fileName} • Analyzing...`;
      case "completed":
        return `${fileName} • Ready`;
      case "error":
        // Show the actual error message
        const errorMsg = status.error || "Processing failed";
        return `${fileName} • Error: ${errorMsg}`;
      default:
        return fileName;
    }
  };

  return (
    <section className="mb-8">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
        {/* Reference Materials with Tabs */}
        <div className="bg-[#1A1B23] rounded-2xl p-6 border border-[#374151]">
          <h3
            className="text-lg font-semibold text-white mb-4"
            style={{ fontFamily: "Inter, sans-serif" }}
          >
            Reference Materials{" "}
            {totalMaterials > 0 && (
              <span className="text-[#6366F1]">({totalMaterials})</span>
            )}
          </h3>

          {/* Tab Navigation */}
          <div className="flex space-x-1 mb-4 bg-[#374151] rounded-lg p-1">
            <button
              onClick={() => onTabChange("files")}
              className={`flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                activeTab === "files"
                  ? "bg-[#6366F1] text-white"
                  : "text-[#9CA3AF] hover:text-white"
              }`}
              style={{ fontFamily: "Inter, sans-serif" }}
            >
              <File size={16} />
              <span>Files</span>
              {referenceFiles.length > 0 && (
                <span className="bg-[#8B5CF6] text-white text-xs px-1.5 py-0.5 rounded-full">
                  {referenceFiles.length}
                </span>
              )}
            </button>
            <button
              onClick={() => onTabChange("text")}
              className={`flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                activeTab === "text"
                  ? "bg-[#6366F1] text-white"
                  : "text-[#9CA3AF] hover:text-white"
              }`}
              style={{ fontFamily: "Inter, sans-serif" }}
            >
              <Type size={16} />
              <span>Text</span>
              {referenceTexts.length > 0 && (
                <span className="bg-[#8B5CF6] text-white text-xs px-1.5 py-0.5 rounded-full">
                  {referenceTexts.length}
                </span>
              )}
            </button>
            <button
              onClick={() => onTabChange("urls")}
              className={`flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                activeTab === "urls"
                  ? "bg-[#6366F1] text-white"
                  : "text-[#9CA3AF] hover:text-white"
              }`}
              style={{ fontFamily: "Inter, sans-serif" }}
            >
              <Link size={16} />
              <span>URLs</span>
              {referenceUrls.length > 0 && (
                <span className="bg-[#8B5CF6] text-white text-xs px-1.5 py-0.5 rounded-full">
                  {referenceUrls.length}
                </span>
              )}
            </button>
          </div>

          {/* Tab Content */}
          {activeTab === "files" && (
            <div>
              <div
                className="border-2 border-dashed border-[#4B5563] rounded-xl p-8 text-center hover:border-[#6366F1] transition-colors cursor-pointer"
                onDragOver={(e) => e.preventDefault()}
                onDrop={(e) => {
                  e.preventDefault();
                  onReferenceUpload(e.dataTransfer.files);
                }}
                onClick={() =>
                  document.getElementById("reference-upload").click()
                }
              >
                <Upload size={32} className="text-[#6366F1] mx-auto mb-4" />
                <p
                  className="text-white font-medium mb-2"
                  style={{ fontFamily: "Inter, sans-serif" }}
                >
                  Drop files here or click to upload
                </p>
                <p
                  className="text-sm text-[#9CA3AF]"
                  style={{ fontFamily: "Inter, sans-serif" }}
                >
                  Pitch decks, transcripts, notes, market docs
                </p>
                <div className="space-y-1 mt-2">
                  <p className="text-xs text-[#6B7280]">
                    PDF, DOCX, TXT • Max 5 files • 50MB each
                  </p>
                  <p className="text-xs text-blue-400">
                    ✨ Files automatically analyzed by AI as you upload
                  </p>
                </div>
              </div>
              <input
                id="reference-upload"
                type="file"
                multiple
                accept=".pdf,.docx,.txt"
                className="hidden"
                onChange={(e) => onReferenceUpload(e.target.files)}
              />

              {referenceFiles.length > 0 && (
                <div className="mt-4 space-y-2">
                  {referenceFiles.map((file, index) => {
                    const status = getFileStatus(file.name);
                    return (
                      <div
                        key={index}
                        className="flex items-center justify-between p-3 bg-[#374151] rounded-lg"
                      >
                        <div className="flex items-center space-x-3 flex-1 min-w-0">
                          {getStatusIcon(status)}
                          <div className="flex-1 min-w-0">
                            <span
                              className="text-sm text-white block truncate"
                              style={{ fontFamily: "Inter, sans-serif" }}
                            >
                              {getStatusText(status, file.name)}
                            </span>
                            <span className="text-xs text-[#9CA3AF]">
                              {(file.size / 1024 / 1024).toFixed(2)} MB
                            </span>
                          </div>
                        </div>
                        <button
                          onClick={() => onRemoveReferenceFile(index)}
                          className="ml-2 text-[#9CA3AF] hover:text-[#EF4444] transition-colors"
                        >
                          ×
                        </button>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          )}

          {activeTab === "text" && (
            <div className="space-y-4">
              <div className="space-y-3">
                <input
                  type="text"
                  value={rawTextLabel}
                  onChange={(e) => onRawTextLabelChange(e.target.value)}
                  placeholder="Label this content (e.g., 'Introduction call with founder')"
                  className="w-full p-3 border border-[#4B5563] rounded-xl bg-[#374151] text-white placeholder-[#9CA3AF] focus:outline-none focus:ring-2 focus:ring-[#6366F1]"
                  style={{ fontFamily: "Inter, sans-serif" }}
                />
                <textarea
                  value={rawTextInput}
                  onChange={(e) => onRawTextChange(e.target.value)}
                  placeholder="Paste meeting notes, transcripts, or any relevant text content..."
                  className="w-full p-4 border border-[#4B5563] rounded-xl bg-[#374151] text-white placeholder-[#9CA3AF] resize-none focus:outline-none focus:ring-2 focus:ring-[#6366F1]"
                  rows="6"
                  style={{ fontFamily: "Inter, sans-serif" }}
                />
                <button
                  onClick={onAddText}
                  disabled={!rawTextInput.trim()}
                  className="w-full px-4 py-2 bg-gradient-to-r from-[#6366F1] to-[#8B5CF6] text-white font-medium rounded-lg hover:from-[#5B61F0] hover:to-[#7C3AED] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  style={{ fontFamily: "Inter, sans-serif" }}
                >
                  Add Text Content
                </button>
              </div>

              {referenceTexts.length > 0 && (
                <div className="space-y-2">
                  {referenceTexts.map((textEntry, index) => (
                    <div
                      key={index}
                      className="flex items-start justify-between p-3 bg-[#374151] rounded-lg"
                    >
                      <div className="flex items-start space-x-3">
                        <Type size={16} className="text-[#6366F1] mt-0.5" />
                        <div className="flex-1">
                          <span
                            className="text-sm text-white block"
                            style={{ fontFamily: "Inter, sans-serif" }}
                          >
                            {textEntry.label}
                          </span>
                          <span
                            className="text-xs text-[#9CA3AF] block truncate max-w-xs"
                            style={{ fontFamily: "Inter, sans-serif" }}
                          >
                            {textEntry.content
                              ? textEntry.content.substring(0, 100)
                              : textEntry.substring(0, 100)}
                            ...
                          </span>
                        </div>
                      </div>
                      <button
                        onClick={() => onRemoveText(index)}
                        className="text-[#9CA3AF] hover:text-[#EF4444] transition-colors ml-2"
                      >
                        ×
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {activeTab === "urls" && (
            <div className="space-y-4">
              <div className="space-y-3">
                <input
                  type="text"
                  value={urlLabel}
                  onChange={(e) => onUrlLabelChange(e.target.value)}
                  placeholder="Label this URL (e.g., 'TechCrunch article about market')"
                  className="w-full p-3 border border-[#4B5563] rounded-xl bg-[#374151] text-white placeholder-[#9CA3AF] focus:outline-none focus:ring-2 focus:ring-[#6366F1]"
                  style={{ fontFamily: "Inter, sans-serif" }}
                />
                <input
                  type="url"
                  value={urlInput}
                  onChange={(e) => onUrlChange(e.target.value)}
                  placeholder="https://example.com/document or news article..."
                  className="w-full p-4 border border-[#4B5563] rounded-xl bg-[#374151] text-white placeholder-[#9CA3AF] focus:outline-none focus:ring-2 focus:ring-[#6366F1]"
                  style={{ fontFamily: "Inter, sans-serif" }}
                />
                <button
                  onClick={onAddUrl}
                  disabled={!urlInput.trim()}
                  className="w-full px-4 py-2 bg-gradient-to-r from-[#6366F1] to-[#8B5CF6] text-white font-medium rounded-lg hover:from-[#5B61F0] hover:to-[#7C3AED] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  style={{ fontFamily: "Inter, sans-serif" }}
                >
                  Add URL
                </button>
              </div>

              {referenceUrls.length > 0 && (
                <div className="space-y-2">
                  {referenceUrls.map((urlEntry, index) => (
                    <div
                      key={index}
                      className="flex items-center justify-between p-3 bg-[#374151] rounded-lg"
                    >
                      <div className="flex items-center space-x-3">
                        <Link size={16} className="text-[#6366F1]" />
                        <div className="flex-1">
                          <span
                            className="text-sm text-white block"
                            style={{ fontFamily: "Inter, sans-serif" }}
                          >
                            {urlEntry.label || urlEntry}
                          </span>
                          {urlEntry.url && (
                            <span
                              className="text-xs text-[#9CA3AF] block truncate"
                              style={{ fontFamily: "Inter, sans-serif" }}
                            >
                              {urlEntry.url}
                            </span>
                          )}
                        </div>
                      </div>
                      <button
                        onClick={() => onRemoveUrl(index)}
                        className="text-[#9CA3AF] hover:text-[#EF4444] transition-colors"
                      >
                        ×
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Combined list of all reference materials */}
          {totalMaterials > 0 && (
            <div className="mt-6 pt-4 border-t border-[#4B5563]">
              <h4
                className="text-sm font-medium text-[#D4D4D8] mb-3"
                style={{ fontFamily: "Inter, sans-serif" }}
              >
                All Reference Materials ({totalMaterials})
              </h4>
              <div className="space-y-2 max-h-40 overflow-y-auto">
                {/* Files */}
                {referenceFiles.map((file, index) => {
                  const status = getFileStatus(file.name);
                  return (
                    <div
                      key={`file-${index}`}
                      className="flex items-center justify-between p-2 bg-[#374151] rounded-lg"
                    >
                      <div className="flex items-center space-x-3">
                        {getStatusIcon(status)}
                        <span
                          className="text-sm text-white truncate"
                          style={{ fontFamily: "Inter, sans-serif" }}
                        >
                          {getStatusText(status, file.name)}
                        </span>
                        <span className="text-xs text-[#9CA3AF] bg-[#4B5563] px-2 py-0.5 rounded">
                          File
                        </span>
                      </div>
                      <button
                        onClick={() => onRemoveReferenceFile(index)}
                        className="text-[#9CA3AF] hover:text-[#EF4444] transition-colors"
                      >
                        ×
                      </button>
                    </div>
                  );
                })}

                {/* Text entries */}
                {referenceTexts.map((textEntry, index) => (
                  <div
                    key={`text-${index}`}
                    className="flex items-center justify-between p-2 bg-[#374151] rounded-lg"
                  >
                    <div className="flex items-center space-x-3">
                      <Type size={14} className="text-[#6366F1]" />
                      <span
                        className="text-sm text-white truncate"
                        style={{ fontFamily: "Inter, sans-serif" }}
                      >
                        {textEntry.label}
                      </span>
                      <span className="text-xs text-[#9CA3AF] bg-[#4B5563] px-2 py-0.5 rounded">
                        Text
                      </span>
                    </div>
                    <button
                      onClick={() => onRemoveText(index)}
                      className="text-[#9CA3AF] hover:text-[#EF4444] transition-colors"
                    >
                      ×
                    </button>
                  </div>
                ))}

                {/* URL entries */}
                {referenceUrls.map((urlEntry, index) => (
                  <div
                    key={`url-${index}`}
                    className="flex items-center justify-between p-2 bg-[#374151] rounded-lg"
                  >
                    <div className="flex items-center space-x-3">
                      <Link size={14} className="text-[#6366F1]" />
                      <span
                        className="text-sm text-white truncate"
                        style={{ fontFamily: "Inter, sans-serif" }}
                      >
                        {urlEntry.label}
                      </span>
                      <span className="text-xs text-[#9CA3AF] bg-[#4B5563] px-2 py-0.5 rounded">
                        URL
                      </span>
                    </div>
                    <button
                      onClick={() => onRemoveUrl(index)}
                      className="text-[#9CA3AF] hover:text-[#EF4444] transition-colors"
                    >
                      ×
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        <FileUploadZone
          title="Example Memos (Optional)"
          description="Upload template memos"
          subtitle="Previous investment memos for tone/structure"
          files={exampleFiles}
          onFileUpload={onExampleUpload}
          onRemoveFile={onRemoveExampleFile}
          uploadId="example-upload"
          icon={FileText}
          fileProcessingStatus={fileProcessingStatus}
        />
      </div>

      <ContextInput value={companyContext} onChange={onContextChange} />

      <GenerateButton
        onClick={onGenerate}
        isProcessing={isProcessing}
        processingStage={processingStage}
        generationProgress={generationProgress}
        disabled={totalMaterials === 0}
      />
    </section>
  );
}
