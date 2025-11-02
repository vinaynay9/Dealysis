/**
 * Tests for /api/process-documents endpoint
 * 
 * Note: These tests are basic and may need updates as the code evolves.
 * Focus is on critical paths and error handling.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { POST } from '../process-documents/route';

// Mock fetch for AI API calls
global.fetch = vi.fn();

describe('POST /api/process-documents', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should reject requests without a file', async () => {
    const formData = new FormData();
    const request = new Request('http://localhost/api/process-documents', {
      method: 'POST',
      body: formData,
    });

    const response = await POST(request);
    const data = await response.json();

    expect(response.status).toBe(400);
    expect(data.error).toBe('No file provided');
  });

  it('should reject files that are too large', async () => {
    const formData = new FormData();
    const largeFile = new File(['x'.repeat(60 * 1024 * 1024)], 'large.pdf', {
      type: 'application/pdf',
    });
    formData.append('file', largeFile);
    formData.append('fileType', 'reference');

    const request = new Request('http://localhost/api/process-documents', {
      method: 'POST',
      body: formData,
    });

    const response = await POST(request);
    const data = await response.json();

    expect(response.status).toBe(400);
    expect(data.error).toContain('File too large');
  });

  it('should reject unsupported file types', async () => {
    const formData = new FormData();
    const invalidFile = new File(['content'], 'test.exe', {
      type: 'application/x-msdownload',
    });
    formData.append('file', invalidFile);
    formData.append('fileType', 'reference');

    const request = new Request('http://localhost/api/process-documents', {
      method: 'POST',
      body: formData,
    });

    const response = await POST(request);
    const data = await response.json();

    expect(response.status).toBe(400);
    expect(data.error).toContain('Unsupported file type');
  });

  it('should process valid text files', async () => {
    const formData = new FormData();
    const textFile = new File(['Sample company information'], 'info.txt', {
      type: 'text/plain',
    });
    formData.append('file', textFile);
    formData.append('fileType', 'reference');

    // Mock successful AI response
    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        choices: [
          {
            message: {
              content: 'Analysis: Company is a Series B SaaS startup...',
            },
          },
        ],
      }),
    });

    const request = new Request('http://localhost/api/process-documents', {
      method: 'POST',
      body: formData,
    });

    const response = await POST(request);
    const data = await response.json();

    expect(response.status).toBe(200);
    expect(data.success).toBe(true);
    expect(data.fileName).toBe('info.txt');
    expect(data.analysisType).toBe('Content Analysis');
  });

  it('should handle AI service errors gracefully', async () => {
    const formData = new FormData();
    const textFile = new File(['Sample content'], 'info.txt', {
      type: 'text/plain',
    });
    formData.append('file', textFile);
    formData.append('fileType', 'reference');

    // Mock AI API error
    global.fetch.mockResolvedValueOnce({
      ok: false,
      status: 429,
      text: async () => 'Rate limit exceeded',
    });

    const request = new Request('http://localhost/api/process-documents', {
      method: 'POST',
      body: formData,
    });

    const response = await POST(request);
    const data = await response.json();

    expect(response.status).toBe(500);
    expect(data.error).toContain('AI service is temporarily busy');
  });

  it('should truncate text longer than 25k characters', async () => {
    const formData = new FormData();
    const largeTextFile = new File(
      ['x'.repeat(30000)],
      'large.txt',
      { type: 'text/plain' }
    );
    formData.append('file', largeTextFile);
    formData.append('fileType', 'reference');

    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        choices: [{ message: { content: 'Analysis...' } }],
      }),
    });

    const request = new Request('http://localhost/api/process-documents', {
      method: 'POST',
      body: formData,
    });

    const response = await POST(request);
    const data = await response.json();

    expect(response.status).toBe(200);
    expect(data.analyzedLength).toBe(25000);
    expect(data.textLength).toBe(30000);
  });
});

