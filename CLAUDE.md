# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project does

Automated job application pipeline for Malena Villasboa. Three sequential steps:

1. **`agente.py`** — AI agent uses WebSearch + WebFetch to find real companies in La Plata/Berisso/Ensenada and saves them (name, sector, email, web) to `empresas.csv` via a custom MCP tool `guardar_empresa`. Only saves emails explicitly published on the company's own site; never deduces or invents them.

2. **`redactar.py`** — For each `pendiente` row in the CSV, calls Claude (with WebFetch access) to draft a personalized cover email and choose between two CV variants (`vendedora` or `cajera`). Drafts are saved to `borradores/<email>.txt`. Runs non-interactively: every draft is auto-approved with the CV Claude suggests (row → `aprobado`). No terminal prompts.

3. **`enviar.py`** — Sends `aprobado` rows via Gmail SMTP, attaching the chosen PDF, without asking for confirmation. Has a `MODO_PRUEBA` flag that redirects all mail to a test address instead of the real recipient.

The full pipeline can be run in sequence with `./LaMaquinaDeTrabajo.sh` (still interactive-friendly, prints all steps).

## Automated service (systemd)

The send pipeline runs unattended every 30 minutes via a systemd **user** timer:

- `LaMaquinaAutomatica.sh` — non-interactive wrapper: loads `GMAIL_*` from `~/.bashrc`, activates the venv, runs `agente.py` → `redactar.py` → `enviar.py`. Output is appended to `envios.log`.
- `~/.config/systemd/user/agente-cvs.service` + `agente-cvs.timer` — oneshot service triggered on boot and every 30 min (`OnUnitActiveSec=30min`). Linger is enabled so it runs even without a graphical login.
- `maquina.sh` — control CLI: `activar` / `desactivar` / `estado` / `ver` (tails `envios.log`) / `ahora` (force a run).
- User-facing instructions live in `~/Escritorio/MAQUINA DE TRABAJO - Instrucciones.txt`.

The full loop is self-feeding: `agente.py` searches ~`CANTIDAD` new companies (deduped by email), `redactar.py` drafts/approves up to `LIMITE_POR_EJECUCION` (10), `enviar.py` sends up to `LIMITE_POR_EJECUCION` (10) per run.

## Environment setup

```bash
source .venv/bin/activate
```

Dependencies are installed in `.venv`. Key packages: `claude_agent_sdk`, `anyio`.

Gmail credentials must be set as environment variables (typically in `~/.bashrc`):
```bash
export GMAIL_USUARIO="..."
export GMAIL_CLAVE="..."      # Gmail App Password, not the account password
```

## Running the scripts

```bash
# Full pipeline (interactive)
./LaMaquinaDeTrabajo.sh

# Individual steps
python agente.py      # Step 1: search and collect companies → empresas.csv
python redactar.py    # Step 2: draft cover emails interactively → borradores/
python enviar.py      # Step 3: send approved emails with CV attachments
```

## Key files and data

| File | Purpose |
|------|---------|
| `empresas.csv` | Central database. States: `pendiente` → `aprobado`/`descartado` → `enviado` |
| `borradores/<email>.txt` | One draft per company; first line is `ASUNTO: ...`, rest is the body |
| `perfil.txt` | Candidate profile fed to Claude when drafting emails |
| `CV - Malena Villasboa - Empleada Comercial.pdf` | CV for `vendedora` role |
| `CV - Malena Villasboa - Cajera.pdf` | CV for `cajera` role |

## Important configuration constants

- **`agente.py`**: `RUBRO`, `ZONA`, `CANTIDAD` — control what types of companies to search for.
- **`enviar.py`**: `MODO_PRUEBA = True` — must be changed to `False` for real sends. `LIMITE_POR_EJECUCION` limits emails per run to avoid spam filters.

## CSV column schema

`nombre, rubro, email, web, estado, cv`

The `cv` column is populated by `redactar.py` and holds either `"vendedora"` or `"cajera"`.
