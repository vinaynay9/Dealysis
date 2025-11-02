# Contributing to Dealysis

Thanks for helping improve Dealysis! This guide will help you get started.

## 🚀 Quick Start

1. **Read the [README.md](./README.md)** - Understand the project
2. **Set up environment** - Copy `env.example` to `.env` in `apps/web/`
3. **Install dependencies** - `cd apps/web && npm install`
4. **Run tests** - `npm test` (once tests are set up)
5. **Start dev server** - `npm run dev`

## 📋 Development Workflow

### 1. Pick an Issue
- Check `docs/QUALITY_REPORT.md` for known issues
- Look for issues labeled "good first issue" or "help wanted"
- Focus on critical issues first (PDF processing, rate limiting, validation)

### 2. Create a Branch
```bash
git checkout -b fix/pdf-processing
# or
git checkout -b feature/new-validation
```

### 3. Make Changes
- Follow existing code style
- Add JSDoc comments to new functions
- Write tests for new features
- Update documentation if needed

### 4. Test Your Changes
```bash
# Run tests (when available)
npm test

# Test manually
npm run dev
# Then test the feature in browser
```

### 5. Submit Pull Request
- Write clear description of changes
- Reference any related issues
- Add screenshots if UI changes
- Make sure tests pass

## 🎯 Priority Areas

Based on `docs/QUALITY_REPORT.md`, here are high-impact areas:

### Critical (Do First)
1. **PDF Processing** - Replace naive extraction with `pdf-parse`
2. **Rate Limiting** - Prevent unlimited AI costs
3. **Input Validation** - Add Zod schemas to API routes
4. **Error Boundaries** - Prevent app crashes

### High Priority
1. **Test Coverage** - Add tests for critical paths
2. **TypeScript** - Add proper types to functions
3. **Error Handling** - Standardize error responses
4. **Documentation** - Add comments to complex logic

## 📝 Code Style

### JavaScript/TypeScript
- Use camelCase for variables and functions
- Use PascalCase for components
- Use descriptive names (avoid abbreviations)
- Add JSDoc comments to public functions
- Keep functions small and focused

### Example:
```javascript
/**
 * Processes a file and extracts text content.
 * 
 * @param {File} file - The file to process
 * @returns {Promise<string>} Extracted text content
 */
async function extractText(file) {
  // Implementation
}
```

### React Components
- Use functional components with hooks
- Keep components focused (single responsibility)
- Extract complex logic to custom hooks
- Use meaningful prop names

### API Routes
- Validate all inputs
- Return consistent error format
- Add JSDoc comments
- Handle errors gracefully

## 🧪 Testing

### Current Status
- Test infrastructure exists (Vitest)
- Basic tests in `src/app/api/__tests__/`
- Need more coverage!

### Writing Tests
```javascript
import { describe, it, expect } from 'vitest';

describe('Feature Name', () => {
  it('should do something', () => {
    expect(true).toBe(true);
  });
});
```

### Test Priorities
1. API routes (critical business logic)
2. Custom hooks (complex state logic)
3. Utility functions (pure functions easiest)
4. Components (last, requires React Testing Library)

## 📚 Documentation

### When to Update Docs
- Adding new API endpoints → Update `docs/API.md`
- Changing database schema → Update `docs/schema.sql`
- Adding features → Update `README.md`
- Finding bugs → Document in code comments

### Code Comments
Add comments above functions explaining:
- What the function does
- Parameters and return values
- Any important limitations
- TODO items if incomplete

## 🐛 Bug Reports

When reporting bugs, include:
1. **What happened** - Clear description
2. **Expected behavior** - What should happen
3. **Steps to reproduce** - How to trigger the bug
4. **Environment** - Browser, OS, Node version
5. **Error messages** - Full error text
6. **Screenshots** - If UI issue

## 💡 Feature Requests

When suggesting features:
1. **Problem** - What problem does it solve?
2. **Solution** - How should it work?
3. **Use case** - Who benefits?
4. **Mockups** - If UI change, add mockups

## 🔍 Code Review Process

### What We Look For
- ✅ Code works and solves the problem
- ✅ Follows existing patterns
- ✅ Has tests (for new features)
- ✅ Documentation updated
- ✅ No obvious bugs
- ✅ Performance considerations
- ✅ Security considerations

### Review Checklist
- [ ] Code follows style guidelines
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] No console.logs left behind
- [ ] Error handling appropriate
- [ ] Comments for complex logic

## 🚨 Critical Rules

### Don't
- ❌ Break existing functionality
- ❌ Add dependencies without discussion
- ❌ Commit sensitive data (API keys, passwords)
- ❌ Push directly to main/master
- ❌ Remove platform code (`__create/` folders)

### Do
- ✅ Test your changes
- ✅ Ask questions if unsure
- ✅ Keep PRs focused (one feature/bug)
- ✅ Update relevant docs
- ✅ Follow existing patterns

## 💰 Budget Constraints

**Important**: This project has a very low budget. Focus on:
- Free/open-source solutions
- Minimal new dependencies
- Quick wins over perfect solutions
- Documentation over expensive tools

**Avoid**:
- Paid services/APIs
- Heavy new frameworks
- Over-engineering

**Prefer**:
- Simple, maintainable code
- Well-documented solutions
- Reusing existing patterns

## 🤝 Getting Help

### Questions?
- Check existing documentation first
- Review `docs/` folder
- Look at similar code in codebase
- Ask in PR comments
- Check `docs/QUALITY_REPORT.md` for context

### Stuck?
1. Read relevant code carefully
2. Add console.logs to understand flow
3. Check browser dev tools
4. Review error messages
5. Ask for help with specific question

## 📦 Dependencies

### Adding New Dependencies
**Think twice before adding!**

Ask yourself:
- Is there a built-in solution?
- Can we use an existing dependency?
- Is it actively maintained?
- Does it add significant value?

**For budget constraints, prefer:**
- Native JavaScript/Node APIs
- Existing dependencies
- Lightweight alternatives
- Documentation over tools

## 🎉 Recognition

Contributors will be:
- Listed in README (when added)
- Thanked in PR comments
- Acknowledged in release notes

## 📞 Questions?

- Read the docs in `/docs/`
- Check `README.md` for setup
- Review `docs/QUALITY_REPORT.md` for context
- Look at existing code for patterns

---

**Remember**: Small, focused improvements are better than big, complex changes. Every contribution helps! 🚀

