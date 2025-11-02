/**
 * Tests for /api/generate-memo-sections endpoint
 * 
 * Note: These tests mock the AI service. In production, actual AI calls
 * are expensive, so we focus on request validation and error handling.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { POST } from '../generate-memo-sections/route';

global.fetch = vi.fn();

describe('POST /api/generate-memo-sections', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should reject invalid section names', async () => {
    const request = new Request('http://localhost/api/generate-memo-sections', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        contentAnalyses: [],
        sectionToGenerate: 'invalid_section',
      }),
    });

    const response = await POST(request);
    const data = await response.json();

    expect(response.status).toBe(400);
    expect(data.error).toContain('Invalid section specified');
  });

  it('should accept valid section names', async () => {
    const validSections = [
      'executive_summary',
      'company_overview',
      'market_opportunity',
      'product_technology',
      'competitive_landscape',
      'traction_financials',
      'team_leadership',
      'risks_recommendation',
    ];

    for (const section of validSections) {
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          choices: [
            {
              message: {
                content: `# ${section}\n\nGenerated content...`,
              },
            },
          ],
        }),
      });

      const request = new Request(
        'http://localhost/api/generate-memo-sections',
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            contentAnalyses: [{ fileName: 'test.pdf', analysis: 'Company info' }],
            sectionToGenerate: section,
          }),
        }
      );

      const response = await POST(request);
      const data = await response.json();

      expect(response.status).toBe(200);
      expect(data.success).toBe(true);
      expect(data.section).toBe(section);
    }
  });

  it('should build context from multiple sources', async () => {
    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        choices: [{ message: { content: 'Generated section' } }],
      }),
    });

    const request = new Request('http://localhost/api/generate-memo-sections', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        templateAnalysis: [{ fileName: 'template.pdf', analysis: 'Template' }],
        contentAnalyses: [
          { fileName: 'doc1.pdf', analysis: 'Analysis 1' },
          { fileName: 'doc2.pdf', analysis: 'Analysis 2' },
        ],
        additionalContext: 'Additional context',
        referenceTexts: [{ label: 'Notes', content: 'Text content' }],
        referenceUrls: [{ label: 'Website', url: 'https://example.com' }],
        sectionToGenerate: 'executive_summary',
      }),
    });

    const response = await POST(request);
    const data = await response.json();

    expect(response.status).toBe(200);
    expect(data.contextLength).toBeGreaterThan(0);
    // Verify AI was called with proper context
    expect(global.fetch).toHaveBeenCalledWith(
      expect.any(String),
      expect.objectContaining({
        method: 'POST',
        body: expect.stringContaining('TEMPLATE STRUCTURE GUIDANCE'),
      })
    );
  });

  it('should truncate context if too long', async () => {
    const longContext = 'x'.repeat(25000);

    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        choices: [{ message: { content: 'Generated' } }],
      }),
    });

    const request = new Request('http://localhost/api/generate-memo-sections', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        contentAnalyses: [{ fileName: 'test.pdf', analysis: longContext }],
        sectionToGenerate: 'executive_summary',
      }),
    });

    const response = await POST(request);
    const data = await response.json();

    expect(response.status).toBe(200);
    expect(data.contextLength).toBeLessThanOrEqual(20000);
  });

  it('should handle AI service rate limits', async () => {
    global.fetch.mockResolvedValueOnce({
      ok: false,
      status: 429,
      text: async () => 'Rate limit exceeded',
    });

    const request = new Request('http://localhost/api/generate-memo-sections', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        contentAnalyses: [{ fileName: 'test.pdf', analysis: 'Content' }],
        sectionToGenerate: 'executive_summary',
      }),
    });

    const response = await POST(request);
    const data = await response.json();

    expect(response.status).toBe(500);
    expect(data.error).toContain('AI service is temporarily busy');
  });

  it('should track sources for citation numbering', async () => {
    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        choices: [
          {
            message: {
              content: 'Content with citations [1] and [2]',
            },
          },
        ],
      }),
    });

    const request = new Request('http://localhost/api/generate-memo-sections', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        contentAnalyses: [
          { fileName: 'doc1.pdf', analysis: 'Analysis 1' },
          { fileName: 'doc2.pdf', analysis: 'Analysis 2' },
        ],
        sectionToGenerate: 'executive_summary',
      }),
    });

    const response = await POST(request);
    const data = await response.json();

    expect(response.status).toBe(200);
    // Verify citation guide was included in AI prompt
    const callArgs = global.fetch.mock.calls[0][1];
    expect(JSON.parse(callArgs.body).messages[1].content).toContain(
      'SOURCE CITATION GUIDE'
    );
  });
});

