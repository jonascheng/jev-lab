# Jev Lab

Interactive desktop studio to evaluate application state using the [TypeSafe Jev decision model](https://dash.cloudflare.com/ebe52b653e78340564a3d8ddfad44c36/ai/models/typesafe/jev) on Cloudflare Workers AI.

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

- **Desktop Studio (`pywebview`)**: Native OS desktop window embedding a responsive 3-pane evaluation studio with zero local port exposure.
- **Three Core Primitives**:
  - `noul`: Binary hypothesis evaluation returning probability $P(\text{true})$ with optional true/false criteria.
  - `choice`: Categorical classification with candidate-specific criteria, returning predicted label, confidence, and distribution.
  - `score`: Ordinal rating along ordered scale levels, returning calibrated numeric score, confidence, and distribution.
- **Visual Question Builder**: Interactively author, rename, edit criteria, duplicate, and delete typed Question primitives with live validation.
- **Pre-built Presets**: One-click demo scenarios for Support Ticket Triage, Content Moderation, and Financial Fraud Review.
- **Persistent Credentials**: Manage Cloudflare `ACCOUNT_ID` and `API_TOKEN` in the Settings drawer with connection verification, saved locally to `~/.config/jev/credentials.json` (mode `0600`).
- **Session Auto-Save & Export**: Work is continuously cached in local storage; full Question suites and State can be exported or imported as JSON files.
- **Rich Dashboard**: Colored probability bars, confidence ratings, distribution breakdowns, token counts, and execution latency.

## Configuration & Environment Variables

You can also provide credentials via environment variables, which take precedence over stored credentials:

```bash
export CLOUDFLARE_ACCOUNT_ID="your-account-id"
export CLOUDFLARE_API_TOKEN="your-api-token"
```

Credentials file path: `~/.config/jev/credentials.json`.
