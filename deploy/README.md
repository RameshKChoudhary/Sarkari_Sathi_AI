# Deployment

Both options use the root `Dockerfile` (API + built UI in one container). **Not tested here** (no deploy target from the build sandbox).

* **Hugging Face Spaces** – new Space → SDK *Docker* → push this repo. README front-matter needs `app_port: 7860`. Add `GROQ_API_KEY` under *Settings → Secrets*.
* **Render** – New → Blueprint → select `deploy/render.yaml`; add `GROQ_API_KEY` in the dashboard.
* Free tiers have ~512 MB–16 GB RAM: keep `EMBED_MODEL=offline-lsa`/`RETRIEVAL_MODE=hybrid_lex` unless the instance can hold BGE-M3 (~2.3 GB).
