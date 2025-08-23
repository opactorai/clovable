# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Claudable is a Next.js-based web app builder that combines Claude Code/Cursor CLI capabilities with an intuitive app-building experience. It allows users to describe their app idea in natural language and generates production-ready code with instant preview, Vercel deployment, and Supabase integration.

## Architecture

### Monorepo Structure
- **apps/web**: Next.js 14 frontend with TypeScript, Tailwind CSS, and shadcn/ui
- **apps/api**: FastAPI backend with Python 3.10+, SQLAlchemy, and WebSocket support
- **data/**: SQLite database storage (cc.db)
- Root workspace managed by npm workspaces

### Key Architectural Patterns

**Frontend (apps/web)**:
- WebSocket-based real-time communication for AI agent interactions
- Project-based routing: `/[project_id]/chat` for each app building session
- Component hierarchy: Page → ChatLog/Preview → MessageInput/FileTree
- State management via React hooks and context (no external state library)
- Real-time preview using iframe with hot-reload support

**Backend (apps/api)**:
- FastAPI with async/await for all endpoints
- WebSocket endpoint `/api/chat/{project_id}` for AI agent communication
- Unified CLI manager supporting both Claude Code and Cursor CLI
- SQLAlchemy ORM with SQLite (local) / PostgreSQL (production)
- Service integrations: GitHub API, Vercel API, Supabase management

### Critical Integration Points

1. **WebSocket Protocol**: Messages between frontend and backend follow specific types:
   - `user_message`: User prompts to AI
   - `assistant_message`: AI responses
   - `tool_use`: AI tool execution events
   - `preview_error`: Runtime errors from preview
   - `file_change`: File system modifications

2. **CLI Integration**: The backend proxies commands to Claude Code/Cursor CLI via:
   - `app/services/cli/unified_manager.py`: Manages CLI sessions
   - `app/services/claude_act.py`: Claude Code specific handling
   - `app/services/cursor_cli.py`: Cursor CLI specific handling

3. **Project Lifecycle**:
   - Created with initial prompt → Status: initializing
   - AI generates boilerplate → Status: active
   - Files stored in `data/projects/{project_id}/`
   - Preview runs via `npm run dev` in project directory

## Essential Commands

### Development
```bash
# Install everything (frontend + backend)
npm install

# Start both frontend and backend
npm run dev

# Frontend only (port 3000)
cd apps/web && npm run dev

# Backend only (port 8080)
cd apps/api && python -m uvicorn app.main:app --reload --port 8080

# API docs
# http://localhost:8080/docs
```

### Linting & Testing
```bash
# Frontend lint
cd apps/web && npm run lint

# Frontend build (production check)
cd apps/web && npm run build

# Backend lint (with ruff)
cd apps/api && python -m ruff check .

# Backend lint autofix
cd apps/api && python -m ruff check . --fix
```

### Database Operations
```bash
# Backup database
npm run db:backup

# Reset database (WARNING: deletes all data)
npm run db:reset

# Manual database location
# data/cc.db (SQLite)
```

### Dependency Management
```bash
# Clean everything (node_modules, venv, etc.)
npm run clean

# Reinstall Python dependencies
cd apps/api
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Windows-Specific Considerations

1. **File Encoding**: Backend sets `PYTHONIOENCODING=utf-8` for terminal output
2. **Path Handling**: Always use forward slashes in TypeScript, let Python handle OS-specific paths
3. **Terminal UI**: Uses Rich library with Windows compatibility (colorama)
4. **Git Filenames**: Avoid backslashes in filenames (breaks Windows checkout)

## Service Integration Keys

When implementing service integrations:

**GitHub**: Personal Access Token with `repo` scope
- Endpoint: `/api/github/connect`
- Creates/manages repos via GitHub API

**Vercel**: Account token from Vercel dashboard
- Endpoint: `/api/vercel/deploy`
- Deploys Next.js projects

**Supabase**: Project URL + anon/service keys
- Endpoint: `/api/projects/{id}/services`
- Database and auth setup

## Common Patterns to Follow

### Adding New API Endpoints
1. Create router in `apps/api/app/api/`
2. Import and include in `main.py`
3. Use dependency injection: `db: Session = Depends(get_db)`
4. Return proper HTTP status codes and error messages

### WebSocket Message Handling
1. Messages are JSON with `type` field
2. Use `WebSocketManager` for connection management
3. Always handle disconnections gracefully
4. Log important events via `terminal_ui`

### Frontend Component Development
1. Use TypeScript with proper types
2. Components in `apps/web/components/`
3. Hooks in `apps/web/hooks/`
4. Follow existing patterns for motion/animations (Framer Motion)

### File Operations
1. Project files stored in `data/projects/{project_id}/`
2. Use `app/services/file_service.py` for file operations
3. Always validate paths to prevent directory traversal
4. Git operations via `app/services/git_service.py`

## Error Handling

1. **Frontend**: Show user-friendly error messages in UI
2. **Backend**: Log errors with `terminal_ui`, return structured error responses
3. **WebSocket**: Reconnect automatically on connection loss
4. **Preview**: Capture and display build/runtime errors in chat

## Performance Considerations

1. **Polling**: Minimize polling frequency (use WebSocket when possible)
2. **File Watch**: Debounce file change events (300ms default)
3. **Database**: Use indexed queries, batch operations when possible
4. **Preview**: Lazy load preview iframe, kill process on navigation

## Port Configuration

Ports are auto-detected if defaults are in use:
- Frontend: 3000 (or next available)
- Backend: 8080 (or next available)
- Preview: Dynamic allocation per project

Check `.env` files for actual port assignments.