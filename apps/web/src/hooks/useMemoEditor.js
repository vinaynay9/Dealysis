import { useState, useEffect } from "react";

export function useMemoEditor() {
  const [memoData, setMemoData] = useState(null);
  const [currentContent, setCurrentContent] = useState("");
  const [isEditing, setIsEditing] = useState(false);
  const [activeTab, setActiveTab] = useState("preview");
  const [pageWidth, setPageWidth] = useState("standard");
  const [showOutline, setShowOutline] = useState(true);
  const [sections, setSections] = useState([]);
  const [uploadedMedia, setUploadedMedia] = useState([]);

  // Load memo data from sessionStorage
  useEffect(() => {
    const storedMemo = sessionStorage.getItem("generatedMemo");
    if (storedMemo) {
      try {
        const parsedMemo = JSON.parse(storedMemo);
        setMemoData(parsedMemo);
        setCurrentContent(parsedMemo.content);

        // Extract sections from content for outline
        const sectionMatches = parsedMemo.content.match(/^# (.+)$/gm);
        if (sectionMatches) {
          const extractedSections = sectionMatches.map((match, index) => ({
            id: `section-${index}`,
            title: match.replace("# ", ""),
            anchor: match.replace("# ", "").toLowerCase().replace(/\s+/g, "-"),
          }));
          setSections(extractedSections);
        }
      } catch (error) {
        console.error("Error parsing memo data:", error);
      }
    }
  }, []);

  const getPageWidthClass = () => {
    switch (pageWidth) {
      case "narrow":
        return "max-w-2xl";
      case "wide":
        return "max-w-6xl";
      default:
        return "max-w-4xl";
    }
  };

  const scrollToSection = (anchor) => {
    const element = document.getElementById(anchor);
    if (element) {
      element.scrollIntoView({ behavior: "smooth" });
    }
  };

  const handleMediaUpload = (mediaData) => {
    setUploadedMedia((prev) => [...prev, mediaData]);

    // Insert media into content based on type
    let mediaMarkdown = "";
    if (mediaData.mediaType === "image") {
      mediaMarkdown = `\n\n![${mediaData.caption || mediaData.fileName}](${mediaData.url})\n`;
      if (mediaData.caption) {
        mediaMarkdown += `*${mediaData.caption}*\n`;
      }
    } else if (mediaData.mediaType === "video") {
      mediaMarkdown = `\n\n<video controls width="100%">\n  <source src="${mediaData.url}" type="${mediaData.mimeType}">\n  Your browser does not support the video tag.\n</video>\n`;
      if (mediaData.caption) {
        mediaMarkdown += `*${mediaData.caption}*\n`;
      }
    } else {
      mediaMarkdown = `\n\n[📄 ${mediaData.fileName}](${mediaData.url})\n`;
      if (mediaData.caption) {
        mediaMarkdown += `*${mediaData.caption}*\n`;
      }
    }

    setCurrentContent((prev) => prev + mediaMarkdown);
  };

  return {
    memoData,
    currentContent,
    setCurrentContent,
    isEditing,
    setIsEditing,
    activeTab,
    setActiveTab,
    pageWidth,
    setPageWidth,
    showOutline,
    setShowOutline,
    sections,
    uploadedMedia,
    getPageWidthClass,
    scrollToSection,
    handleMediaUpload,
  };
}
