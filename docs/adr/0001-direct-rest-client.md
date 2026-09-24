# Direct REST API Client for Cloudflare Workers AI

We access `typesafe/jev` directly via Cloudflare's REST API (`https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run`) rather than bundling the Cloudflare SDK or requiring local Wrangler bindings. Jev is a synchronous, non-generative model with compact single-pass payloads; a lightweight `httpx` client allows zero-setup standalone execution via `uvx --from git+...` across any environment.
