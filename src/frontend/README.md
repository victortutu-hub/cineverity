# Functional hosted frontend

This directory contains CineVerity's functional no-build browser UI. FastAPI serves it at `/`; it submits same-origin `POST /api/runs` requests and incrementally consumes NDJSON stage events.

The repository-root `index.html` remains the GitHub Pages development landing page. No Node/npm build is required. This UI is an inspection surface for accepted structured artifacts; it does not claim rendering, simulation, or executed validation.
