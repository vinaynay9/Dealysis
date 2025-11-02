import { useState } from "react";
import { Upload, X, Image, Video, File, Camera } from "lucide-react";

export function MediaUploadModal({ isOpen, onClose, onUpload, sectionId }) {
  const [dragActive, setDragActive] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [caption, setCaption] = useState("");
  const [uploadType, setUploadType] = useState("image");

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFiles(e.dataTransfer.files);
    }
  };

  const handleFileInput = (e) => {
    if (e.target.files && e.target.files[0]) {
      handleFiles(e.target.files);
    }
  };

  const handleFiles = async (files) => {
    const file = files[0];
    if (!file) return;

    setUploading(true);
    try {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("sectionId", sectionId);
      formData.append("caption", caption);

      const response = await fetch("/api/upload-media", {
        method: "POST",
        body: formData,
      });

      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.error || "Upload failed");
      }

      onUpload(result.media);
      onClose();
      setCaption("");
    } catch (error) {
      console.error("Upload error:", error);
      alert(`Upload failed: ${error.message}`);
    } finally {
      setUploading(false);
    }
  };

  const getAcceptedTypes = () => {
    switch (uploadType) {
      case "image":
        return ".jpg,.jpeg,.png,.gif,.webp,.svg";
      case "video":
        return ".mp4,.mov,.avi,.mkv,.webm";
      case "document":
        return ".pdf,.docx,.doc,.txt,.xlsx,.pptx";
      default:
        return ".jpg,.jpeg,.png,.gif,.webp,.svg,.mp4,.mov,.pdf,.docx,.doc,.txt";
    }
  };

  const getUploadIcon = () => {
    switch (uploadType) {
      case "image":
        return <Image size={48} className="text-blue-500" />;
      case "video":
        return <Video size={48} className="text-purple-500" />;
      case "document":
        return <File size={48} className="text-green-500" />;
      default:
        return <Upload size={48} className="text-gray-500" />;
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
        <div className="flex items-center justify-between p-4 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-800">Add Media</h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <X size={20} />
          </button>
        </div>

        <div className="p-4">
          {/* Media Type Selector */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Media Type
            </label>
            <div className="flex space-x-2">
              <button
                onClick={() => setUploadType("image")}
                className={`flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                  uploadType === "image"
                    ? "bg-blue-100 text-blue-700 border border-blue-300"
                    : "bg-gray-100 text-gray-600 hover:bg-gray-200"
                }`}
              >
                <Image size={16} />
                <span>Image</span>
              </button>
              <button
                onClick={() => setUploadType("video")}
                className={`flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                  uploadType === "video"
                    ? "bg-purple-100 text-purple-700 border border-purple-300"
                    : "bg-gray-100 text-gray-600 hover:bg-gray-200"
                }`}
              >
                <Video size={16} />
                <span>Video</span>
              </button>
              <button
                onClick={() => setUploadType("document")}
                className={`flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                  uploadType === "document"
                    ? "bg-green-100 text-green-700 border border-green-300"
                    : "bg-gray-100 text-gray-600 hover:bg-gray-200"
                }`}
              >
                <File size={16} />
                <span>Document</span>
              </button>
            </div>
          </div>

          {/* Caption Input */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Caption (optional)
            </label>
            <input
              type="text"
              value={caption}
              onChange={(e) => setCaption(e.target.value)}
              placeholder="Add a caption for this media..."
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Upload Area */}
          <div
            className={`relative border-2 border-dashed rounded-lg p-8 text-center transition-colors cursor-pointer ${
              dragActive
                ? "border-blue-500 bg-blue-50"
                : "border-gray-300 hover:border-gray-400"
            } ${uploading ? "pointer-events-none opacity-50" : ""}`}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
            onClick={() => document.getElementById("media-file-input").click()}
          >
            {uploading ? (
              <div className="flex flex-col items-center">
                <div className="w-8 h-8 border-2 border-blue-600 border-t-transparent rounded-full animate-spin mb-4"></div>
                <p className="text-gray-600">Uploading...</p>
              </div>
            ) : (
              <div className="flex flex-col items-center">
                {getUploadIcon()}
                <p className="text-gray-600 mt-4 mb-2">
                  Drop {uploadType}s here or click to upload
                </p>
                <p className="text-sm text-gray-500">
                  {uploadType === "image" && "JPG, PNG, GIF up to 100MB"}
                  {uploadType === "video" && "MP4, MOV, AVI up to 100MB"}
                  {uploadType === "document" && "PDF, DOCX, TXT up to 100MB"}
                </p>
              </div>
            )}

            <input
              id="media-file-input"
              type="file"
              accept={getAcceptedTypes()}
              onChange={handleFileInput}
              className="hidden"
            />
          </div>

          {/* Upload Guidelines */}
          <div className="mt-4 text-xs text-gray-500">
            <p>
              <strong>Tips:</strong>
            </p>
            <ul className="mt-1 space-y-1">
              <li>• Images will be displayed inline with the content</li>
              <li>• Videos will show a thumbnail with play button</li>
              <li>• Documents will appear as downloadable links</li>
              <li>• All media will be included in exports</li>
            </ul>
          </div>
        </div>

        <div className="flex justify-end space-x-3 p-4 border-t border-gray-200">
          <button
            onClick={onClose}
            className="px-4 py-2 text-gray-600 hover:text-gray-800"
            disabled={uploading}
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
}
