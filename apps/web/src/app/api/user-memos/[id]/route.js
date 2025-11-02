import sql from "@/app/api/utils/sql";
import { auth } from "@/auth";

// Get a specific memo
export async function GET(request, { params }) {
  try {
    const session = await auth();
    console.log("Session:", session);

    if (!session || !session.user?.id) {
      console.error("No session or user ID");
      return Response.json({ error: "Unauthorized" }, { status: 401 });
    }

    const userId = session.user.id;
    const memoId = params.id;

    console.log("Looking for memo:", { memoId, userId });

    const result = await sql`
      SELECT * FROM user_memos 
      WHERE id = ${memoId} AND user_id = ${userId}
      LIMIT 1
    `;

    console.log("SQL result:", result);

    if (result.length === 0) {
      return Response.json({ error: "Memo not found" }, { status: 404 });
    }

    const memo = result[0];
    // Parse JSON fields
    if (memo.sections) {
      memo.sections = JSON.parse(memo.sections);
    }
    if (memo.metadata) {
      memo.metadata = JSON.parse(memo.metadata);
    }

    return Response.json({
      success: true,
      memo: memo,
    });
  } catch (error) {
    console.error("Error fetching memo:", error);
    return Response.json(
      { error: "Failed to fetch memo", details: error.message },
      { status: 500 },
    );
  }
}

// Update a memo
export async function PUT(request, { params }) {
  try {
    const session = await auth();
    if (!session || !session.user?.id) {
      return Response.json({ error: "Unauthorized" }, { status: 401 });
    }

    const userId = session.user.id;
    const memoId = params.id;
    const body = await request.json();
    const { title, content, sections, metadata, company_name, is_favorite } =
      body;

    // Build dynamic update query
    const setClauses = [];
    const values = [];
    let paramIndex = 1;

    if (title !== undefined) {
      setClauses.push(`title = $${paramIndex}`);
      values.push(title);
      paramIndex++;
    }

    if (content !== undefined) {
      setClauses.push(`content = $${paramIndex}`);
      values.push(content);
      paramIndex++;
    }

    if (sections !== undefined) {
      setClauses.push(`sections = $${paramIndex}`);
      values.push(sections ? JSON.stringify(sections) : null);
      paramIndex++;
    }

    if (metadata !== undefined) {
      setClauses.push(`metadata = $${paramIndex}`);
      values.push(metadata ? JSON.stringify(metadata) : null);
      paramIndex++;
    }

    if (company_name !== undefined) {
      setClauses.push(`company_name = $${paramIndex}`);
      values.push(company_name);
      paramIndex++;
    }

    if (is_favorite !== undefined) {
      setClauses.push(`is_favorite = $${paramIndex}`);
      values.push(is_favorite);
      paramIndex++;
    }

    // Always update the updated_at timestamp
    setClauses.push(`updated_at = CURRENT_TIMESTAMP`);

    if (setClauses.length === 1) {
      // Only updated_at was added
      return Response.json({ error: "No fields to update" }, { status: 400 });
    }

    // Add WHERE clause parameters
    const whereClause = `WHERE id = $${paramIndex} AND user_id = $${paramIndex + 1}`;
    values.push(memoId, userId);

    const query = `
      UPDATE user_memos 
      SET ${setClauses.join(", ")} 
      ${whereClause}
      RETURNING id, title, company_name, created_at, updated_at, is_favorite
    `;

    const result = await sql(query, values);

    if (result.length === 0) {
      return Response.json({ error: "Memo not found" }, { status: 404 });
    }

    return Response.json({
      success: true,
      memo: result[0],
    });
  } catch (error) {
    console.error("Error updating memo:", error);
    return Response.json(
      { error: "Failed to update memo", details: error.message },
      { status: 500 },
    );
  }
}

// Delete a memo
export async function DELETE(request, { params }) {
  try {
    const session = await auth();
    if (!session || !session.user?.id) {
      return Response.json({ error: "Unauthorized" }, { status: 401 });
    }

    const userId = session.user.id;
    const memoId = params.id;

    const result = await sql`
      DELETE FROM user_memos 
      WHERE id = ${memoId} AND user_id = ${userId}
      RETURNING id
    `;

    if (result.length === 0) {
      return Response.json({ error: "Memo not found" }, { status: 404 });
    }

    return Response.json({
      success: true,
      message: "Memo deleted successfully",
    });
  } catch (error) {
    console.error("Error deleting memo:", error);
    return Response.json(
      { error: "Failed to delete memo", details: error.message },
      { status: 500 },
    );
  }
}
