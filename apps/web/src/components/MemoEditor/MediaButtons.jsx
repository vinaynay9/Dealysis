import { Image, Video, File } from "lucide-react";

export function MediaButtons({ openMediaModal }) {
  return (
    <div className="mt-6 flex justify-center">
      <div className="flex space-x-2 bg-white rounded-full shadow-md border border-gray-200 p-2">
        <button
          onClick={() => openMediaModal("image")}
          className="flex items-center space-x-2 px-3 py-2 text-gray-600 hover:text-blue-600 hover:bg-blue-50 rounded-full transition-colors"
        >
          <Image size={16} />
          <span className="text-sm">Add Image</span>
        </button>
        <button
          onClick={() => openMediaModal("video")}
          className="flex items-center space-x-2 px-3 py-2 text-gray-600 hover:text-purple-600 hover:bg-purple-50 rounded-full transition-colors"
        >
          <Video size={16} />
          <span className="text-sm">Add Video</span>
        </button>
        <button
          onClick={() => openMediaModal("document")}
          className="flex items-center space-x-2 px-3 py-2 text-gray-600 hover:text-green-600 hover:bg-green-50 rounded-full transition-colors"
        >
          <File size={16} />
          <span className="text-sm">Add File</span>
        </button>
      </div>
    </div>
  );
}
