/**
 * POST /api/process-documents
 * 
 * Processes uploaded documents (PDF, DOCX, TXT, CSV) with AI analysis.
 * 
 * Accepts files and extracts text, then sends to AI for analysis:
 * - "reference" files: Extract company/investment information
 * - "example" files: Extract memo structure template
 * 
 * @param {Request} request - FormData with "file" and "fileType" fields
 * @returns {Promise<Response>} JSON with analysis results or error
 * 
 * Limitations:
 * - Max file size: 50MB
 * - Max text analyzed: 25,000 characters (truncated if longer)
 * - PDF processing is limited (needs pdf-parse library for better extraction)
 * 
 * TODO: Replace naive PDF extraction with pdf-parse library
 */
export async function POST(request) {
  try {
    const formData = await request.formData();
    const file = formData.get("file");
    const fileType = formData.get("fileType");

    if (!file) {
      return Response.json({ error: "No file provided" }, { status: 400 });
    }

    // Check file size (limit to 50MB per file)
    const maxFileSize = 50 * 1024 * 1024;
    if (file.size > maxFileSize) {
      return Response.json(
        {
          error: `File too large: ${Math.round(file.size / 1024 / 1024)}MB. Maximum size is 50MB.`,
        },
        { status: 400 },
      );
    }

    // Check file type
    const fileName = file.name.toLowerCase();
    const validExtensions = [".pdf", ".docx", ".doc", ".txt", ".csv"];
    const hasValidExtension = validExtensions.some((ext) =>
      fileName.endsWith(ext),
    );

    if (!hasValidExtension) {
      return Response.json(
        {
          error: `Unsupported file type. Please use: PDF, Word, or Text files. (${file.name})`,
        },
        { status: 400 },
      );
    }

    let extractedText;
    try {
      // Special handling for PDF files
      if (fileName.endsWith(".pdf")) {
        // PDFs require special parsing - we can't use .text() directly
        const arrayBuffer = await file.arrayBuffer();
        const uint8Array = new Uint8Array(arrayBuffer);

        // Try to extract basic text content (this is limited but may work for simple PDFs)
        try {
          const decoder = new TextDecoder("utf-8", { fatal: false });
          const rawText = decoder.decode(uint8Array);

          // Look for readable text in the PDF
          const textMatches = rawText.match(/\w+/g);
          if (textMatches && textMatches.length > 10) {
            extractedText = textMatches.join(" ");
          } else {
            throw new Error("No readable text found");
          }
        } catch (pdfError) {
          return Response.json(
            {
              error: `Cannot extract text from PDF "${file.name}". This PDF may be image-based, password-protected, or use complex formatting. Please convert to plain text (TXT) or Word (DOCX) format first, or try uploading the content as raw text instead.`,
            },
            { status: 400 },
          );
        }
      } else {
        // Handle text-based files normally
        extractedText = await file.text();
      }

      if (!extractedText || extractedText.trim().length === 0) {
        return Response.json(
          {
            error: `Unable to extract text from "${file.name}". The file may be empty, password-protected, or use an unsupported encoding. Try converting to plain text (TXT) format first.`,
          },
          { status: 400 },
        );
      }

      // For PDFs, the extracted text might be messy, so let's clean it up
      if (fileName.endsWith(".pdf")) {
        extractedText = extractedText
          .replace(/[^\w\s\.\,\!\?\;\:\-\(\)]/g, " ") // Remove special chars
          .replace(/\s+/g, " ") // Normalize whitespace
          .trim();
      }
    } catch (error) {
      console.error(`Error reading file ${file.name}:`, error);

      if (fileName.endsWith(".pdf")) {
        return Response.json(
          {
            error: `Cannot process PDF "${file.name}". This PDF may be image-based, encrypted, or corrupted. Please try: 1) Converting to Word (DOCX) or plain text (TXT), 2) Copy-pasting the text content using the Text tab instead, or 3) Using a different PDF file.`,
          },
          { status: 400 },
        );
      } else {
        return Response.json(
          {
            error: `Cannot read "${file.name}". The file may be corrupted, password-protected, or in an unsupported format. Error details: ${error.message}`,
          },
          { status: 400 },
        );
      }
    }

    // Limit text size to prevent prompt overload (max 25k chars per analysis)
    const maxTextLength = 25000;
    const textToAnalyze =
      extractedText.length > maxTextLength
        ? extractedText.substring(0, maxTextLength) +
          "...\n\n[Text truncated for analysis]"
        : extractedText;

    // Create focused prompts based on file type
    const prompt =
      fileType === "example"
        ? `Analyze this example investment memo to extract ONLY the structural template. Focus on format, not content.

Extract and return:
1. **Section Structure**: List all major sections (e.g., Executive Summary, Market Analysis, etc.)
2. **Writing Style**: Tone and approach (formal/analytical/narrative/bullet-heavy)  
3. **Format Patterns**: How are headings styled? Tables? Bullets? Lists?
4. **Length Guidelines**: Rough paragraph/section lengths
5. **Key Elements**: What makes this memo effective?

Be concise but thorough - this template will guide new memo creation.

Document: ${file.name}
Sample Content: ${textToAnalyze}`
        : `Extract key investment information from this document. Be systematic and comprehensive.

Analyze and extract:
1. **Company Basics**: Name, stage, business model, location, founding info
2. **Financial Profile**: Revenue, growth rates, funding history, burn rate, runway
3. **Market Context**: Market size, TAM, competitive landscape, positioning  
4. **Product Details**: Core product, features, technology, differentiation
5. **Traction Metrics**: User growth, revenue growth, key partnerships, customers
6. **Team Information**: Founder backgrounds, key team members, advisors
7. **Key Risks**: Major concerns, challenges, or red flags mentioned

Document: ${file.name}
Content: ${textToAnalyze}`;

    try {
      console.log(
        `Analyzing ${file.name} (${fileType}) with micro-prompt approach...`,
      );

      const aiResponse = await fetch(
        "/integrations/chat-gpt/conversationgpt4",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            messages: [
              {
                role: "system",
                content:
                  fileType === "example"
                    ? "You are a document structure analyzer. Extract formatting and structural templates from investment memos. Focus on style and format, not content details."
                    : "You are an expert document analyzer for investment research. Extract comprehensive information systematically and concisely for investment memo creation.",
              },
              {
                role: "user",
                content: prompt,
              },
            ],
          }),
        },
      );

      if (!aiResponse.ok) {
        const errorText = await aiResponse.text();
        console.error("ChatGPT analysis error:", errorText);

        if (aiResponse.status === 429) {
          throw new Error(
            "AI service is temporarily busy. Please try again in a moment.",
          );
        } else if (aiResponse.status === 413) {
          throw new Error(
            "Document too large for AI analysis. Try a smaller file.",
          );
        } else {
          throw new Error(
            `AI analysis failed (${aiResponse.status}): ${errorText.substring(0, 200)}`,
          );
        }
      }

      const aiResult = await aiResponse.json();

      if (
        !aiResult.choices ||
        !aiResult.choices[0] ||
        !aiResult.choices[0].message
      ) {
        throw new Error("Invalid response from AI service. Please try again.");
      }

      const analysis = aiResult.choices[0].message.content;

      return Response.json({
        success: true,
        fileName: file.name,
        fileType: fileType,
        originalSize: file.size,
        analysis: analysis,
        timestamp: new Date().toISOString(),
        analysisType:
          fileType === "example" ? "Template Structure" : "Content Analysis",
        textLength: extractedText.length,
        analyzedLength: textToAnalyze.length,
      });
    } catch (error) {
      console.error("Error in AI analysis:", error);

      // Provide fallback for example files
      if (fileType === "example") {
        const basicStructure = `Basic template detected in ${file.name}:
- Document length: ~${extractedText.length.toLocaleString()} characters
- Estimated sections: ${Math.max(1, extractedText.split(/\n\s*\n/).length)} major sections
- Standard memo format detected

Note: AI analysis unavailable, using basic structure detection.`;

        return Response.json({
          success: true,
          fileName: file.name,
          fileType: fileType,
          originalSize: file.size,
          analysis: basicStructure,
          timestamp: new Date().toISOString(),
          note: "Basic structure analysis due to AI service issue",
          analysisType: "Basic Template Detection",
        });
      }

      return Response.json(
        {
          error: `AI analysis failed for ${file.name}: ${error.message}`,
          fileName: file.name,
          fileType: fileType,
        },
        { status: 500 },
      );
    }
  } catch (error) {
    console.error("Error processing document:", error);
    return Response.json(
      {
        error: `Failed to process document: ${error.message}`,
        details: error.stack?.substring(0, 500),
      },
      { status: 500 },
    );
  }
}
