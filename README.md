# Dealysis - AI-Powered Investment Memo Generator

**Dealysis** is an intelligent platform that helps Venture Capital analysts write comprehensive investment memos faster while maintaining analytical rigor. The system uses AI to process due diligence materials and generate structured investment memos, requiring analysts to input subjective judgments and strategic insights.

## 🎯 Purpose

Dealysis accelerates the investment memo writing process by:
- **Automating Structure**: Generates 8 standard memo sections from uploaded documents
- **Maintaining Quality**: Flags missing information requiring analyst input with `[⚠️ Analyst Input Required]`
- **Enabling Collaboration**: Provides chat interface for refining sections with AI assistance
- **Ensuring Accountability**: Citations for all facts, requiring analysts to provide context

## 🏗️ Architecture

This is a monorepo containing:

```
dealysis/
├── apps/
│   ├── web/              # React Router + Hono web application
│   └── mobile/           # Expo/React Native mobile app (minimal/WIP)
├── docs/                 # Documentation and schema files
├── scripts/              # Build and deployment scripts
└── shared/               # Shared types and utilities (to be created)
```

### Technology Stack

**Web Application:**
- **Frontend**: React 18, React Router 7, TailwindCSS
- **Backend**: Hono server, React Router Node adapter
- **Database**: PostgreSQL (Neon serverless)
- **Auth**: Auth.js with credential-based authentication
- **AI**: OpenAI GPT-4 via ChatGPT API
- **File Processing**: Custom document parsing (PDF, DOCX, TXT, CSV)

**Mobile Application:**
- **Framework**: Expo 53, React Native 0.79
- **UI**: React Navigation, Reanimated
- **Status**: Minimal implementation (needs development)

## 🚀 Getting Started

### Prerequisites

- **Node.js 20+** (or Bun for web app)
- **PostgreSQL database** (recommended: Neon serverless - free tier available)
- **AI API access** (via internal ChatGPT integration - provided by platform)

### Quick Setup (5 minutes)

1. **Clone and install:**
```bash
cd apps/web
npm install
```

2. **Set up environment:**
```bash
# Copy the example file
cp ../../env.example .env

# Edit .env with your database URL and AUTH_SECRET
# Generate AUTH_SECRET: openssl rand -base64 32
```

3. **Set up database:**
```bash
# Run the schema (in your PostgreSQL database)
psql $DATABASE_URL < ../../docs/schema.sql
```

4. **Start development server:**
```bash
npm run dev
```

The app will be available at `http://localhost:5173`

### Environment Variables

See `env.example` for all options. Minimum required:

```bash
# Database (required)
DATABASE_URL=postgresql://user:password@host/database

# Auth (required - generate with: openssl rand -base64 32)
AUTH_SECRET=your-secret-key-here
```

**Note**: AI integration endpoint (`/integrations/chat-gpt/conversationgpt4`) is provided by the hosting platform.

#### Mobile Application

```bash
cd apps/mobile
npm install
npm start
```

## 📊 Database Schema

The application requires the following PostgreSQL tables:

### Authentication Tables
- `auth_users` - User accounts
- `auth_accounts` - OAuth/credential accounts
- `auth_sessions` - Active sessions
- `auth_verification_token` - Email verification tokens

### Application Tables
- `user_memos` - Saved investment memos
- `usage_tracking` - Analytics and usage metrics (optional)

See `docs/schema.sql` for complete schema.

## 🎨 User Workflow

### 1. Upload Phase (Workspace)
- Upload reference documents (pitch decks, transcripts, financials)
- Optional: Upload example memo templates for style guidance
- Add raw text content or URLs as additional references
- Provide company context (optional)

### 2. Generation Phase
The system generates 8 memo sections sequentially:
1. **Executive Summary** - Overview, market, traction, thesis, risks
2. **Company Overview** - Background, mission, business model, milestones
3. **Market Opportunity** - TAM/SAM/SOM, dynamics, customer segments
4. **Product & Technology** - Features, architecture, differentiation, roadmap
5. **Competitive Landscape** - Direct/indirect competitors, positioning, barriers
6. **Traction & Financials** - Revenue, metrics, unit economics, funding
7. **Team & Leadership** - Founders, executives, culture, equity distribution
8. **Risks & Recommendation** - Risk factors, mitigation, scenarios, investment terms

### 3. Refinement Phase (Memo Editor)
- View generated memo with proper formatting
- Chat with AI to refine specific sections
- Add media (charts, diagrams, images)
- Export to PDF or Word
- Save to personal memo library

## 🔧 Key Features

### Document Processing
- **Supported Formats**: PDF, DOCX, DOC, TXT, CSV
- **AI Analysis**: Each document analyzed separately (25k char limit per file)
- **Smart Extraction**: Separate prompts for template structure vs content analysis

### Memo Generation
- **Micro-Prompt Architecture**: Each section generated independently for better quality
- **Citation System**: All facts linked to source documents `[1], [2], etc.`
- **Quality Flags**: Missing data marked with `[⚠️ Analyst Input Required]`
- **Progress Tracking**: Real-time section generation progress

### Analyst Tools
- **Interactive Chat**: Refine sections via conversational AI
- **Bibliography Management**: Automatic source tracking and citation
- **Export Options**: PDF, Word, plain text, share links
- **Memo Library**: Save, organize, and retrieve memos
- **Favorites**: Star important memos for quick access

## 📁 Project Structure

### Web App Structure (Key Files)

```
apps/web/src/
├── app/
│   ├── page.jsx                    # Landing/onboarding page
│   ├── workspace/page.jsx          # Main workspace (upload & generate)
│   ├── memo-editor/page.jsx        # Memo editing interface
│   ├── account/                     # Auth pages (signin, signup, logout)
│   └── api/                        # API routes
│       ├── process-documents/       # 📄 Document upload & AI analysis
│       │   └── route.js            # Main processing logic (260 lines)
│       ├── generate-memo-sections/ # 🤖 Section-by-section generation
│       │   └── route.js            # Memo generation logic (585 lines)
│       ├── user-memos/              # 💾 CRUD for saved memos
│       ├── track-usage/             # 📊 Analytics
│       └── utils/
│           └── sql.js              # Database connection
│
├── components/
│   ├── Workspace/                   # Workspace UI (12 components)
│   │   ├── Header.jsx              # Top navigation
│   │   ├── UploadSection.jsx      # File upload interface
│   │   ├── ResultsSection.jsx      # Generated memo display
│   │   └── ...                     # See components/Workspace/
│   └── MemoEditor/                  # Memo editor UI (11 components)
│       ├── MemoEditor.jsx          # Main editor component
│       ├── ChatAssistant.jsx       # AI chat sidebar
│       └── ...                     # See components/MemoEditor/
│
├── hooks/
│   ├── useWorkspace.js              # 🎯 Main workspace logic (697 lines)
│   │                                # Handles: uploads, generation, chat
│   ├── useMemoEditor.js            # Editor state management
│   ├── useChatAssistant.js         # AI chat integration
│   ├── useBibliography.js          # Citation management
│   └── useExport.js                # PDF/Word export
│
└── utils/
    ├── useAuth.js                   # Authentication hook
    └── useHandleStreamResponse.js   # Streaming AI response handler
```

**💡 Tip**: Start with `useWorkspace.js` and API routes to understand the flow.

## 🐛 Critical Issues to Fix

### Platform Notes
This app uses a proprietary hosting platform that provides:
- AI endpoint: `/integrations/chat-gpt/conversationgpt4` (platform-provided)
- Auth system: `@auth/create` (platform-provided)
- `__create/` folders: Platform code (don't modify)

**⚠️ Vendor lock-in**: Can't easily migrate. AI costs unknown - implement rate limiting ASAP.

### Critical Bugs (Fix Tonight)

1. **PDF Processing Broken** 🔴
   - **Location**: `apps/web/src/app/api/process-documents/route.js:41-65`
   - **Problem**: Naive text extraction fails on most PDFs (image-based, complex formatting)
   - **Fix**: Install `pdf-parse` library
   ```bash
   npm install pdf-parse
   ```
   Replace lines 41-65 with:
   ```javascript
   import pdfParse from 'pdf-parse';
   const data = await pdfParse(arrayBuffer);
   const extractedText = data.text;
   ```
   **Time**: 2-3 hours

2. **No Rate Limiting** 🔴
   - **Location**: All API routes calling AI endpoint
   - **Problem**: Unlimited AI API calls = unbounded costs
   - **Fix**: Add rate limiting (Upstash free tier)
   ```bash
   npm install @upstash/ratelimit @upstash/redis
   ```
   Add to routes: `process-documents/route.js`, `generate-memo-sections/route.js`
   **Time**: 4-6 hours

3. **No Input Validation** 🔴
   - **Location**: All API routes
   - **Problem**: Security risk, data corruption potential
   - **Fix**: Add Zod validation
   ```bash
   npm install zod
   ```
   Create schemas for request bodies in all API routes
   **Time**: 4-6 hours

4. **No Error Boundaries** 🟠
   - **Location**: React components
   - **Problem**: App crashes show technical errors to users
   - **Fix**: Add React ErrorBoundary component
   **Time**: 2-3 hours

5. **Session Storage for Memos** 🟠
   - **Location**: `useMemoEditor.js` uses `sessionStorage`
   - **Problem**: Data lost on tab close, not synced
   - **Fix**: Move to database-backed state with auto-save
   **Time**: 2-3 hours

### Other Issues (Fix Later)
- File size limits: 50MB per file, 25k chars analyzed (may truncate)
- Context length: 20k char limit for memo generation
- No tests: Basic test structure exists but needs expansion
- TypeScript: Files have .ts extensions but minimal types
- Console logging: Replace with proper logging later

## 📝 Development Guidelines

### Code Organization
- Use feature-based folder structure
- Separate business logic into hooks and utilities
- Keep components focused and reusable
- Co-locate related files (component, styles, tests)

### Naming Conventions
- Components: PascalCase (`MemoEditor.jsx`)
- Hooks: camelCase with `use` prefix (`useWorkspace.js`)
- Utilities: camelCase (`handleStreamResponse.js`)
- API Routes: kebab-case folders (`generate-memo-sections/`)

### State Management
- Use React hooks for local state
- Zustand for global state (currently minimal usage)
- Server state managed by React Query where needed

## 🤝 Contributing

**Want to help?** We'd love your contribution!

See **[CONTRIBUTING.md](./CONTRIBUTING.md)** for development guidelines.

**Priority fixes needed** (see `TONIGHT_HACK_LIST.md`):
- PDF processing fix
- Rate limiting  
- Input validation
- Error boundaries

---

## 📄 License

[Add license information when available]

## 👥 Contributors

Contributors welcome! See `CONTRIBUTING.md` for how to get started.

---

**Last Updated**: November 2025  
**Version**: 1.0.0  
**Status**: MVP - Active Development  
**Budget**: Very Low - Focus on free/open-source solutions

