import { EyeOff, Image, Video, File } from "lucide-react";

export function OutlineSidebar({
  showOutline,
  setShowOutline,
  sections,
  scrollToSection,
  uploadedMedia,
}) {
  if (!showOutline) return null;

  return (
    <aside className="w-64 bg-white border-r border-gray-200 h-screen sticky top-16 overflow-y-auto">
      <div className="p-4">
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-semibold text-gray-800">Outline</h2>
          <button
            onClick={() => setShowOutline(false)}
            className="text-gray-400 hover:text-gray-600"
          >
            <EyeOff size={16} />
          </button>
        </div>
        <nav className="space-y-1">
          {sections.map((section) => (
            <button
              key={section.id}
              onClick={() => scrollToSection(section.anchor)}
              className="w-full text-left px-2 py-1 text-sm text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded"
            >
              {section.title}
            </button>
          ))}
        </nav>

        {/* Media Library */}
        {uploadedMedia.length > 0 && (
          <div className="mt-8">
            <h3 className="font-semibold text-gray-800 mb-2">Media Library</h3>
            <div className="space-y-2">
              {uploadedMedia.map((media, index) => (
                <div key={index} className="text-xs p-2 bg-gray-50 rounded">
                  <div className="flex items-center space-x-2">
                    {media.mediaType === "image" && <Image size={12} />}
                    {media.mediaType === "video" && <Video size={12} />}
                    {media.mediaType === "document" && <File size={12} />}
                    <span className="truncate">{media.fileName}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </aside>
  );
}
