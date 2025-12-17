# Install Dependencies

Install all project dependencies for backend and frontend.

## First
Read and execute `.claude/commands/prime.md`

## Check Environment
```bash
# Verify Python version (requires 3.11+)
python3 --version

# Verify Node version (requires 18+)
node --version

# Check for .env file
ls -la .env
```

## Run
```bash
# Backend (Python)
pip3 install -r requirements.txt

# Frontend (Next.js)
cd app/client && npm install
```

## Verify
```bash
# Check Python packages
pip3 list | grep -E "anthropic|supabase|httpx|feedparser"

# Check frontend build
cd app/client && npm run type-check && npm run lint

# Verify database connection
python3 scripts/diagnose_sources.py
```

## Report
Output:
1. Python packages installed
2. Node modules installed
3. TypeScript/lint status
4. Database connection status
5. Any errors encountered
