# V2 Minute Autoresearch — Test Plan

## Mission

Prove the planning package is structurally sound and aligned to the clarified architecture before any implementation begins.

## Verification Families

### Planning integrity

- [ ] one canonical docs root only
- [ ] umbrella + child issue drafts exist
- [ ] all child issues map to sprint docs
- [ ] merge target is documented as `main-dev`

### Architecture integrity

- [ ] minute-level mission appears in the main plan and issue drafts
- [ ] backtester authority appears in the main plan and issue drafts
- [ ] TradingAgents is framed as selective borrowing, not system archetype
- [ ] factor mining is optional, not mandatory

### Publication integrity

- [ ] GitLab publication blocker is explicit
- [ ] no artifact falsely claims the issues were already published

## Commands

```bash
git branch --show-current
find docs/feature/v2-minute-autoresearch -maxdepth 3 -type f | sort
rg -n "minute-level|autoresearch|TradingAgents|factor mining|backtester|GitLab publication blocker|main-dev" docs/feature/v2-minute-autoresearch -S
```

## Update Space

### Command Results

- leave blank until verification run

### Blockers

- leave blank until verification run

### Follow-ups

- publish issue-card drafts to GitLab later

