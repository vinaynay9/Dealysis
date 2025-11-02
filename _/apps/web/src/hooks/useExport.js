import { useState } from "react";

export function useExport(currentContent) {
  const [showExportDropdown, setShowExportDropdown] = useState(false);

  const exportToPDF = () => {
    // Create print-friendly version
    const printWindow = window.open("", "_blank");
    printWindow.document.write(`
      <html>
        <head>
          <title>Investment Memo</title>
          <style>
            body { font-family: 'Times New Roman', serif; max-width: 8.5in; margin: 0 auto; padding: 1in; }
            h1 { font-size: 24px; border-bottom: 2px solid #000; padding-bottom: 10px; }
            h2 { font-size: 20px; margin-top: 30px; }
            h3 { font-size: 18px; margin-top: 20px; }
            p { line-height: 1.6; margin-bottom: 12px; }
            img { max-width: 100%; height: auto; margin: 20px 0; }
            ul { margin-left: 20px; }
            @media print { body { margin: 0; padding: 0.5in; } }
          </style>
        </head>
        <body>
          ${currentContent
            .replace(/\n/g, "<br>")
            .replace(/^# (.+)$/gm, "<h1>$1</h1>")
            .replace(/^## (.+)$/gm, "<h2>$1</h2>")
            .replace(/^### (.+)$/gm, "<h3>$1</h3>")}
        </body>
      </html>
    `);
    printWindow.document.close();
    setTimeout(() => {
      printWindow.print();
      printWindow.close();
    }, 500);
  };

  const exportToWord = () => {
    // Create a more complete Word-compatible version
    const wordContent = `<!DOCTYPE html>
<html xmlns:o='urn:schemas-microsoft-com:office:office' xmlns:w='urn:schemas-microsoft-com:office:word'>
<head>
  <title>Investment Memo</title>
  <meta charset='utf-8'>
  <style>
    body { font-family: 'Times New Roman', serif; font-size: 12pt; line-height: 1.6; }
    h1 { font-size: 18pt; font-weight: bold; border-bottom: 2px solid black; padding-bottom: 6pt; }
    h2 { font-size: 16pt; font-weight: bold; margin-top: 20pt; }
    h3 { font-size: 14pt; font-weight: bold; margin-top: 16pt; }
    p { margin-bottom: 12pt; }
    ul { margin-left: 20pt; }
  </style>
</head>
<body>
  ${currentContent
    .replace(/\n/g, "<br>")
    .replace(/^# (.+)$/gm, "<h1>$1</h1>")
    .replace(/^## (.+)$/gm, "<h2>$1</h2>")
    .replace(/^### (.+)$/gm, "<h3>$1</h3>")}
</body>
</html>`;

    const blob = new Blob([wordContent], {
      type: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "investment-memo.doc";
    a.click();
    URL.revokeObjectURL(url);
  };

  const copyShareLink = () => {
    const shareUrl = `${window.location.origin}/memo-editor?shared=true`;
    navigator.clipboard.writeText(shareUrl);
    alert("Share link copied to clipboard!");
  };

  return {
    showExportDropdown,
    setShowExportDropdown,
    exportToPDF,
    exportToWord,
    copyShareLink,
  };
}
