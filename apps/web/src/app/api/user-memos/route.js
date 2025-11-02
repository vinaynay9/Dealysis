import sql from "@/app/api/utils/sql";
import { auth } from "@/auth";

/**
 * GET /api/user-memos
 * 
 * Retrieves all memos for the authenticated user.
 * 
 * Query parameters:
 * - search: Filter by title, company, or content (optional)
 * - sortBy: Sort field (created_at, updated_at, title) - default: updated_at
 * - limit: Max results - default: 50
 * 
 * @param {Request} request - URL with optional query parameters
 * @returns {Promise<Response>} JSON array of memo summaries
 */
export async function GET(request) {
  try {
    const session = await auth();
    if (!session || !session.user?.id) {
      return Response.json({ error: "Unauthorized" }, { status: 401 });
    }

    const userId = session.user.id;
    const url = new URL(request.url);
    const search = url.searchParams.get("search");
    const sortBy = url.searchParams.get("sortBy") || "updated_at";
    const limit = parseInt(url.searchParams.get("limit")) || 50;

    let query = `
      SELECT 
        id, 
        title, 
        company_name, 
        created_at, 
        updated_at, 
        is_favorite,
        LEFT(content, 200) as preview
      FROM user_memos 
      WHERE user_id = $1
    `;
    const values = [userId];

    if (search) {
      query += ` AND (
        LOWER(title) LIKE LOWER($2) OR 
        LOWER(company_name) LIKE LOWER($2) OR 
        LOWER(content) LIKE LOWER($2)
      )`;
      values.push(`%${search}%`);
    }

    // Sort by created_at, updated_at, or title
    const validSortFields = ["created_at", "updated_at", "title"];
    const sortField = validSortFields.includes(sortBy) ? sortBy : "updated_at";
    query += ` ORDER BY ${sortField} DESC LIMIT $${values.length + 1}`;
    values.push(limit);

    const memos = await sql(query, values);

    return Response.json({
      success: true,
      memos: memos,
    });
  } catch (error) {
    console.error("Error fetching user memos:", error);
    return Response.json(
      { error: "Failed to fetch memos", details: error.message },
      { status: 500 },
    );
  }
}

/**
 * POST /api/user-memos
 * 
 * Creates a new memo and saves it to the database.
 * 
 * Request body:
 * - title: Memo title (required)
 * - content: Full memo markdown content (required)
 * - company_name: Company name (optional)
 * - sections: JSON object with section data (optional)
 * - metadata: JSON object with generation metadata (optional)
 * 
 * @param {Request} request - JSON body with memo data
 * @returns {Promise<Response>} JSON with created memo ID and metadata
 */
export async function POST(request) {
  try {
    const session = await auth();
    if (!session || !session.user?.id) {
      return Response.json({ error: "Unauthorized" }, { status: 401 });
    }

    const userId = session.user.id;
    const body = await request.json();
    const { title, content, sections, metadata, company_name } = body;

    if (!title || !content) {
      return Response.json(
        { error: "Title and content are required" },
        { status: 400 },
      );
    }

    const result = await sql`
      INSERT INTO user_memos (
        user_id, 
        title, 
        content, 
        sections, 
        metadata, 
        company_name
      ) VALUES (
        ${userId},
        ${title},
        ${content},
        ${sections ? JSON.stringify(sections) : null},
        ${metadata ? JSON.stringify(metadata) : null},
        ${company_name || null}
      )
      RETURNING id, title, company_name, created_at, updated_at
    `;

    return Response.json({
      success: true,
      memo: result[0],
    });
  } catch (error) {
    console.error("Error saving memo:", error);
    return Response.json(
      { error: "Failed to save memo", details: error.message },
      { status: 500 },
    );
  }
}
