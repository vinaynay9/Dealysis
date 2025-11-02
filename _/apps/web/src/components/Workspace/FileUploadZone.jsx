import {
  Upload,
  FileText,
  FileCheck,
  Clock,
  CheckCircle,
  AlertCircle,
} from "lucide-react";

export function FileUploadZone({
  title,
  description,
  subtitle,
  files,
  onFileUpload,
  onRemoveFile,
  uploadId,
  icon: Icon = Upload,
  fileProcessingStatus = {},
}) {
  const getFileStatus = (fileName) => {
    const statusKey = Object.keys(fileProcessingStatus).find(
      (key) => fileProcessingStatus[key].fileName === fileName,
    );
    return statusKey ? fileProcessingStatus[statusKey] : null;
  };

  const getStatusIcon = (status) => {
    if (!status) return <FileCheck size={16} className="text-[#6366F1]" />;

    switch (status.status) {
      case "processing":
        return <Clock size={16} className="text-blue-400 animate-spin" />;
      case "completed":
        return <CheckCircle size={16} className="text-green-400" />;
      case "error":
        return <AlertCircle size={16} className="text-red-400" />;
      default:
        return <FileCheck size={16} className="text-[#6366F1]" />;
    }
  };

  const getStatusText = (status, fileName) => {
    if (!status) return fileName;

    switch (status.status) {
      case "processing":
        return `${fileName} • Analyzing with AI...`;
      case "completed":
        return `${fileName} • Ready for memo`;
      case "error":
        return `${fileName} • Error: ${status.error}`;
      default:
        return fileName;
    }
  };

  return (
    <div className="bg-[#1A1B23] rounded-2xl p-6 border border-[#374151]">
      <h3
        className="text-lg font-semibold text-white mb-4"
        style={{ fontFamily: "Inter, sans-serif" }}
      >
        {title}
      </h3>
      <div
        className="border-2 border-dashed border-[#4B5563] rounded-xl p-8 text-center hover:border-[#6366F1] transition-colors cursor-pointer"
        onDragOver={(e) => e.preventDefault()}
        onDrop={(e) => {
          e.preventDefault();
          onFileUpload(e.dataTransfer.files);
        }}
        onClick={() => document.getElementById(uploadId).click()}
      >
        <Icon size={32} className="text-[#6366F1] mx-auto mb-4" />
        <p
          className="text-white font-medium mb-2"
          style={{ fontFamily: "Inter, sans-serif" }}
        >
          {description}
        </p>
        <p
          className="text-sm text-[#9CA3AF]"
          style={{ fontFamily: "Inter, sans-serif" }}
        >
          {subtitle}
        </p>
        {title === "Reference Materials" && (
          <div className="space-y-1 mt-2">
            <p className="text-xs text-[#6B7280]">
              PDF, DOCX, TXT • Max 5 files • 50MB each
            </p>
            <p className="text-xs text-blue-400">
              ✨ Files automatically analyzed by AI as you upload
            </p>
          </div>
        )}
      </div>
      <input
        id={uploadId}
        type="file"
        multiple
        accept=".pdf,.docx,.txt"
        className="hidden"
        onChange={(e) => onFileUpload(e.target.files)}
      />

      {files.length > 0 && (
        <div className="mt-4 space-y-2">
          {files.map((file, index) => {
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
                  onClick={() => onRemoveFile(index)}
                  className="ml-2 text-[#9CA3AF] hover:text-[#EF4444] transition-colors text-lg"
                >
                  ×
                </button>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
