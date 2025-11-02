import sql from "@/app/api/utils/sql";
import { auth } from "@/auth";

export async function POST(request) {
  try {
    // Get user session if available
    const session = await auth();
    const userId = session?.user?.id || null;

    const body = await request.json();
    const {
      company_name,
      files_uploaded_count,
      reference_texts_count,
      reference_urls_count,
      company_context,
      user_notes,
      processing_time_seconds,
      sections_generated,
      generation_successful,
      user_session_id,
    } = body;

    // Insert usage record
    const result = await sql`
      INSERT INTO memo_generations (
        user_id,
        company_name,
        files_uploaded_count,
        reference_texts_count,
        reference_urls_count,
        company_context,
        user_notes,
        processing_time_seconds,
        sections_generated,
        generation_successful,
        user_session_id
      ) VALUES (
        ${userId},
        ${company_name || null},
        ${files_uploaded_count || 0},
        ${reference_texts_count || 0},
        ${reference_urls_count || 0},
        ${company_context || null},
        ${user_notes || null},
        ${processing_time_seconds || null},
        ${sections_generated || 8},
        ${generation_successful !== false},
        ${user_session_id || null}
      )
      RETURNING id, generated_at, total_reference_materials
    `;

    return Response.json({
      success: true,
      usage_id: result[0].id,
      generated_at: result[0].generated_at,
      total_materials: result[0].total_reference_materials,
    });
  } catch (error) {
    console.error("Error tracking usage:", error);
    return Response.json(
      {
        error: "Failed to track usage",
        details: error.message,
      },
      { status: 500 },
    );
  }
}

// Get usage statistics
export async function GET(request) {
  try {
    const url = new URL(request.url);
    const days = parseInt(url.searchParams.get("days")) || 30;

    const stats = await sql`
      SELECT 
        COUNT(*) as total_generations,
        COUNT(DISTINCT company_name) as unique_companies,
        AVG(files_uploaded_count)::NUMERIC(10,2) as avg_files_per_memo,
        AVG(total_reference_materials)::NUMERIC(10,2) as avg_total_materials,
        AVG(processing_time_seconds)::NUMERIC(10,2) as avg_processing_time,
        COUNT(*) FILTER (WHERE generation_successful = true) as successful_generations,
        COUNT(*) FILTER (WHERE generation_successful = false) as failed_generations
      FROM memo_generations 
      WHERE generated_at >= NOW() - INTERVAL '${days} days'
    `;

    const recentGenerations = await sql`
      SELECT 
        id,
        company_name,
        total_reference_materials,
        generated_at,
        generation_successful
      FROM memo_generations 
      WHERE generated_at >= NOW() - INTERVAL '${days} days'
      ORDER BY generated_at DESC 
      LIMIT 10
    `;

    return Response.json({
      success: true,
      period_days: days,
      statistics: stats[0],
      recent_generations: recentGenerations,
    });
  } catch (error) {
    console.error("Error getting usage stats:", error);
    return Response.json(
      {
        error: "Failed to get usage statistics",
        details: error.message,
      },
      { status: 500 },
    );
  }
}
