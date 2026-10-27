# Vigil — unattended build status (for Mridul's return)

Built while you were at dinner. Branch `feat/phase-1-core`. Deadline ~00:30 IST Oct 24.
Full suite: **165/165 green** (was 150; +15 from the auth layer). Nothing pushed.

---

## ✅ COMMITTED this session (4 commits, all tested)
- `b0060cb` OAuth 2.1 + PKCE(S256) + PRM/AS discovery — pure logic (12 tests)
- `d1d5f45` discovery endpoints wired into the MCP server ASGI app (3 tests)
- `d945f96` transport-security fix: allow-list the public tunnel host (fixed a real
  421 + a missing import, root-caused not patched)
- (this file + brief cleanup)

The server-side **Alexa+ MCP auth checklist is now met in code**:
PRM doc (RFC 9728), AS metadata (RFC 8414) advertising **S256**, OAuth2.1 auth-code
+ PKCE flow, resource binding, Bearer validation. All tested.

## ✅ LIVE right now (verified end-to-end over the public internet)
Public base: `https://thermal-entire-sandbank.ngrok-free.dev`
- `GET /.well-known/oauth-protected-resource` → 200 (PRM)
- `GET /.well-known/oauth-authorization-server` → 200, S256 advertised
- `/mcp` → MCP initialize + 8 tools, proto 2025-11-25

**Infra note:** the live server runs with discovery enabled via:
```
cd C:\Mridul\Programs\Vigil
$env:VIGIL_PUBLIC_URL="https://thermal-entire-sandbank.ngrok-free.dev"
uv run python -m src.server --with-discovery
```
and ngrok via `& "$env:LOCALAPPDATA\Microsoft\WinGet\Links\ngrok.exe" http 8000 --host-header=rewrite`.
If either stopped while you were out, those two commands bring it back. (The server
was last running as a PowerShell background job tied to the build session — if it's
gone, just re-run the command above.)

## ⛔ NEEDS MRIDUL — the first true wall (why I stopped here)
The **Alexa AI CLI** (`@alexa-ai/cli`) installs only from Amazon's **private
CodeArtifact registry**, which requires, in order:
1. Create a new **IAM user** + inline `sts:AssumeRole` to
   `arn:aws:iam::372468808636:role/AddOn3PDeveloperToolsRead`, and generate access keys.
2. Configure AWS profiles `alexa-ai-user` (base) + `alexa-ai` (assume-role).
3. `aws codeartifact login --tool npm --domain alexa-ai --repository npm-packages
   --domain-owner 372468808636 --region us-west-2 --namespace @alexa-ai --profile alexa-ai`
4. `npm install -g @alexa-ai/cli` (in WSL — Node v24.12.0 already present ✅)
5. `alexa-ai configure` → **opens a browser for Login with Amazon** (only you can consent)
6. `alexa-ai new mcp` → scaffold the add-on against the tunnel URL; validate;
   dev-stage deploy (free-tier). STOP before `submit`/certification.

I did **not** do step 1 unattended: minting long-lived IAM access keys with your admin
credential is a standing-secret side-effect you should make consciously, and the chain
can't finish without your browser (step 5) and your cert decision anyway. ~15 min with you.

**Cost:** $0 spent, $120 EC2/SageMaker credits untouched (task needs no compute).

---

## 🎬 DEMO FILM SCRIPT (ready to record NOW — no account needed)
1. **The thesis (10s):** "Vigil — a provably-safe home-security reasoning mesh,
   Alexa+ MCP-native." 
2. **Three surfaces (60s):** run the web console
   (`uv run python -m src.web.server`), show Mission Control reasoning through a
   scenario, the Nightstand Phone CAD-authorization, the Fire TV deterrence state.
   Click scenario 06 (prowler) and 10 (silent duress) to show the dramatic states.
3. **The safety moat (30s):** silence-under-duress (empty actuator tuple), no
   auto-911 (stage + hash only), L3 corroboration gate. These are caps in code.
4. **Live MCP + Alexa+ compliance (40s):** open the public URL's
   `/.well-known/oauth-authorization-server` in a browser — show S256. Then show a
   real MCP client connecting to `…/mcp` and listing 8 tools over the internet.
   "The server meets Alexa+'s published OAuth/PKCE requirements — here are the 165
   passing tests."
5. **Honesty close (10s):** "Every device coded to its real vendor API; modeled
   organs badged MODELED. Device-optional by design."

That is a complete, honest, strong submission video. The only thing it does NOT show
is a physical Echo invoking the skill — that needs the CLI chain above (you + browser).
