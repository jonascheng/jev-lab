# Jev Lab

Interactive CLI to evaluate application state using the [TypeSafe Jev decision model](https://dash.cloudflare.com/ebe52b653e78340564a3d8ddfad44c36/ai/models/typesafe/jev) on Cloudflare Workers AI.

Jev is a non-generative, structured decision model purpose-built for ultra-fast, cost-effective evaluation, classification, and routing.

## Run Directly with `uv`

You do not need to clone or install manually. Run directly via `uvx`:

```bash
uvx --from git+https://github.com/jonascheng/jev-lab jev
```

Or using `uv run` in this repository:

```bash
uv run jev
```

## Features

- **Three Core Primitives**:
  - `noul`: Binary hypothesis evaluation returning probability $P(\text{true})$.
  - `choice`: Categorical classification with option-specific criteria, returning predicted label, confidence, and distribution.
  - `score`: Ordinal rating along defined levels, returning calibrated numeric score, confidence, and distribution.
- **Persistent Credentials**: First-time wizard prompts for Cloudflare `ACCOUNT_ID` and `API_TOKEN`, verifies them with a lightweight test call, and saves to `~/.config/jev/credentials.json` (mode `0600`).
- **Pre-built Presets**:
  - Support Ticket Triage (Noul + Choice + Score)
  - Content Moderation (Noul + Choice + Score)
  - Financial Fraud & Refund Review (Noul + Choice + Score)
- **Custom Playground**: Input custom State (inline text, JSON file, or `$EDITOR`) and build custom typed Questions interactively.
- **Rich Dashboard**: Colored probability bars, confidence ratings, token counts, and execution latency.

## Configuration & Environment Variables

You can also provide credentials via environment variables, which take precedence over stored credentials:

```bash
export CLOUDFLARE_ACCOUNT_ID="your-account-id"
export CLOUDFLARE_API_TOKEN="your-api-token"
```

Credentials file path: `~/.config/jev/credentials.json`.
