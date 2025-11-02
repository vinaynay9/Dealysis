import { useState, useEffect } from "react";

export function useBibliography(memoData, currentContent, setCurrentContent) {
  const [bibliography, setBibliography] = useState([]);
  const [showCitationModal, setShowCitationModal] = useState(false);
  const [selectedText, setSelectedText] = useState("");

  // Generate bibliography from reference materials
  useEffect(() => {
    if (memoData) {
      const bibItems = [];
      let counter = 1;

      // Add files from stored memo data
      if (memoData.metadata?.referenceMaterials) {
        // Try to extract from session storage data structure
        const workspaceData = sessionStorage.getItem("workspaceState");
        if (workspaceData) {
          try {
            const workspace = JSON.parse(workspaceData);

            // Add reference files
            if (workspace.referenceSummaries) {
              workspace.referenceSummaries.forEach((ref) => {
                bibItems.push({
                  id: counter++,
                  type: "document",
                  title: ref.fileName,
                  description: ref.analysisType || "Company document",
                  date: new Date().toLocaleDateString(),
                  source: "Internal document",
                });
              });
            }

            // Add text materials
            if (workspace.referenceTexts) {
              workspace.referenceTexts.forEach((text) => {
                bibItems.push({
                  id: counter++,
                  type: "text",
                  title: text.label,
                  description: "Reference material",
                  date: new Date().toLocaleDateString(),
                  source: "Direct input",
                });
              });
            }

            // Add URLs
            if (workspace.referenceUrls) {
              workspace.referenceUrls.forEach((url) => {
                bibItems.push({
                  id: counter++,
                  type: "url",
                  title: url.label,
                  description: url.url,
                  date: new Date().toLocaleDateString(),
                  source: "Web source",
                });
              });
            }
          } catch (e) {
            console.error("Error parsing workspace data:", e);
          }
        }
      }

      setBibliography(bibItems);
    }
  }, [memoData]);

  // Insert citation into current cursor position
  const insertCitation = (citationId) => {
    const citation = `[${citationId}]`;
    const textarea = document.querySelector("textarea");
    if (textarea) {
      const start = textarea.selectionStart;
      const end = textarea.selectionEnd;
      const newContent =
        currentContent.substring(0, start) +
        citation +
        currentContent.substring(end);
      setCurrentContent(newContent);

      // Move cursor after citation
      setTimeout(() => {
        textarea.selectionStart = textarea.selectionEnd =
          start + citation.length;
        textarea.focus();
      }, 0);
    }
    setShowCitationModal(false);
  };

  // Add bibliography section to content
  const addBibliographySection = () => {
    if (bibliography.length === 0) return;

    let bibSection = "\n\n---\n\n# Bibliography\n\n";
    bibliography.forEach((item) => {
      bibSection += `[${item.id}] **${item.title}** - ${item.description}`;
      if (item.source !== "Direct input") {
        bibSection += ` (${item.source})`;
      }
      bibSection += `\n\n`;
    });

    if (!currentContent.includes("# Bibliography")) {
      setCurrentContent((prev) => prev + bibSection);
    }
  };

  return {
    bibliography,
    showCitationModal,
    setShowCitationModal,
    selectedText,
    setSelectedText,
    insertCitation,
    addBibliographySection,
  };
}
