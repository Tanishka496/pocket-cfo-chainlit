# Frontend for Pocket CFO

This directory holds a simple React-based web frontend that interacts with
the FastAPI backend and provides a user interface for:

* viewing, creating and filtering transactions
* accessing the Chainlit chat interface (embedded via iframe)

## Getting started

```bash
cd frontend
npm install
npm start
```

The development server runs on port 3000 by default and proxies API calls to
`http://localhost:8000` (see `package.json` proxy field or add a `.env`).
