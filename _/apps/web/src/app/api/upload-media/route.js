import { upload } from "@/app/api/utils/upload";

export async function POST(request) {
  try {
    const formData = await request.formData();
    const file = formData.get("file");
    const sectionId = formData.get("sectionId");
    const caption = formData.get("caption") || "";

    if (!file) {
      return Response.json({ error: "No file provided" }, { status: 400 });
    }

    // Check file size (limit to 100MB for media files)
    const maxFileSize = 100 * 1024 * 1024;
    if (file.size > maxFileSize) {
      return Response.json(
        {
          error: `File too large: ${Math.round(file.size / 1024 / 1024)}MB. Maximum size is 100MB.`,
        },
        { status: 400 },
      );
    }

    // Check file type
    const fileName = file.name.toLowerCase();
    const imageExtensions = [".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg"];
    const videoExtensions = [".mp4", ".mov", ".avi", ".mkv", ".webm"];
    const documentExtensions = [
      ".pdf",
      ".docx",
      ".doc",
      ".txt",
      ".xlsx",
      ".pptx",
    ];

    const allowedExtensions = [
      ...imageExtensions,
      ...videoExtensions,
      ...documentExtensions,
    ];
    const hasValidExtension = allowedExtensions.some((ext) =>
      fileName.endsWith(ext),
    );

    if (!hasValidExtension) {
      return Response.json(
        {
          error: `Unsupported file type. Please use images (JPG, PNG, GIF), videos (MP4, MOV), or documents (PDF, DOCX).`,
        },
        { status: 400 },
      );
    }

    // Determine media type
    let mediaType = "document";
    if (imageExtensions.some((ext) => fileName.endsWith(ext))) {
      mediaType = "image";
    } else if (videoExtensions.some((ext) => fileName.endsWith(ext))) {
      mediaType = "video";
    }

    try {
      // Upload file using the existing upload utility
      const uploadResult = await upload(file);

      // Generate thumbnail for images and videos (placeholder logic)
      let thumbnailUrl = null;
      if (mediaType === "image") {
        thumbnailUrl = uploadResult.url; // Use the original image as thumbnail
      } else if (mediaType === "video") {
        // For videos, we would normally generate a thumbnail
        // For now, using a placeholder
        thumbnailUrl = "/api/placeholder-video-thumbnail";
      }

      const mediaData = {
        id: Date.now().toString(), // Simple ID generation
        url: uploadResult.url,
        thumbnailUrl: thumbnailUrl,
        fileName: file.name,
        fileSize: file.size,
        mediaType: mediaType,
        caption: caption,
        sectionId: sectionId,
        uploadedAt: new Date().toISOString(),
        mimeType: file.type,
      };

      return Response.json({
        success: true,
        media: mediaData,
      });
    } catch (uploadError) {
      console.error("Error uploading media:", uploadError);
      return Response.json(
        {
          error: `Upload failed: ${uploadError.message}`,
          details: uploadError.stack?.substring(0, 500),
        },
        { status: 500 },
      );
    }
  } catch (error) {
    console.error("Error processing media upload:", error);
    return Response.json(
      {
        error: `Media upload failed: ${error.message}`,
        details: error.stack?.substring(0, 500),
      },
      { status: 500 },
    );
  }
}
