# AuditEng

## What This Is

Sistema de auditoria automatizada de relatórios de comissionamento elétrico para data centers. Usa IA (Claude) para extrair dados estruturados de PDFs/imagens e código Python para validar contra normas técnicas (NETA, IEEE, Microsoft CxPOR), gerando findings categorizados por severidade com aprovação/reprovação automática.

## Core Value

**"IA extrai, código valida"** — Extração com IA + validação determinística garante reprodutibilidade, explicabilidade e rastreabilidade de cada finding.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] Extração estruturada de PDFs com Instructor + Claude
- [ ] Validação determinística contra normas NETA/IEEE/Microsoft
- [ ] 5 tipos de equipamento: PANEL, UPS, ATS, GEN, XFMR
- [ ] 3 tipos de teste MVP: Grounding, Megger, Thermography
- [ ] Sistema de findings com severidade (CRITICAL, MAJOR, MINOR, INFO)
- [ ] Score de compliance e confidence
- [ ] Veredicto automático (APPROVED, REVIEW, REJECTED)
- [ ] RAG pipeline para consulta de normas técnicas
- [ ] API REST com FastAPI
- [ ] Background processing com Redis + RQ
- [ ] Multi-agent orchestration para desenvolvimento

### Out of Scope

- App mobile nativo — foco em web/API primeiro
- Integração com sistemas externos (Procore, etc) — MVP standalone
- Geração automática de relatórios PDF — fora do MVP
- Multi-idioma — inglês apenas para MVP
- Frontend web completo — API-first, UI básica

## Context

**Problema:** Engenheiros de comissionamento auditam manualmente centenas de relatórios (15-30 min cada), com alta taxa de erro humano (15%) e sem padronização de critérios.

**Solução:** Automação reduz tempo para 2 min/relatório, taxa de erro para 2%, e aumenta throughput 8x.

**Especificação completa:** Documentação detalhada disponível em:
- `/mnt/c/Users/xande/OneDrive/Documentos/auditenga/.claude/company/` — Visão e produto
- `/mnt/c/Users/xande/OneDrive/Documentos/auditenga/.claude/specs/` — Arquitetura e API
- `/mnt/c/Users/xande/OneDrive/Documentos/auditenga/.claude/knowledge/` — Regras de validação e normas
- `/mnt/c/Users/xande/OneDrive/Documentos/auditenga/.claude/team/` — Personas de agentes

**Abordagem:** Fresh start usando Python, seguindo os specs existentes como blueprint.

## Constraints

- **Stack**: Python + FastAPI + Instructor + Pydantic v2 + SQLAlchemy 2.0 + PostgreSQL + Redis — Escolha deliberada para tipagem forte e async
- **AI**: Claude Sonnet 4 via Instructor — Melhor custo-benefício para extração estruturada
- **Validation**: 100% determinística — Mesmos dados sempre geram mesmos findings
- **Files**: Max 50MB por PDF — Limite prático para processamento
- **Deploy**: Railway/Render — Simplicidade, sem DevOps complexo

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Fresh start (não usar código existente) | Specs bem documentados, código existente incompleto | — Pending |
| RAG desde o início | Consulta a normas técnicas é core para validação inteligente | — Pending |
| Python-only (sem TypeScript) | Instructor, melhor ecossistema de IA, tipagem com Pydantic | — Pending |
| Multi-agent development | Especialização por domínio (Backend, AI, Domain, QA) | — Pending |

---
*Last updated: 2026-01-15 after initialization*
