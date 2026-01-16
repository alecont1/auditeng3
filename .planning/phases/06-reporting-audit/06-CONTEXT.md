# Phase 6: Reporting & Audit - Context

**Gathered:** 2026-01-16
**Status:** Ready for planning

<vision>
## How This Should Work

O relatório deve ser DIRETO E ACIONÁVEL — o engenheiro lê rápido e age.

**PDF Report Structure:**
1. **Executive Summary** — PASS/FAIL geral com contagem de findings por severidade + equipamentos auditados
2. **Findings (foco principal)** — Cada finding com:
   - Código (GND-01, THM-02, etc.)
   - Severidade (CRITICAL/MAJOR/MINOR)
   - O que está errado (descrição clara)
   - COMO CORRIGIR:
     - Se erro de documentação → "Corrigir relatório: adicionar X"
     - Se falha real → "Reteste necessário: medir Y novamente"
   - Referência da norma (NETA/Microsoft)
3. **Minimal branding** — Logo no header, data, número do relatório. Sem firulas.

**Foco:** Problema → Ação corretiva → Próximo passo

**Audit Trail Purpose:** Enabling EFFICIENT APPROVAL, not just compliance paperwork.
1. Sistema analisa relatório com regras determinísticas
2. Engenheiro visualiza resumo estruturado (não precisa ler PDF inteiro)
3. Se OK → Aprova com 1 clique → Sobe na plataforma
4. Se pendência → Encaminha ao responsável com finding específico

**Objetivo:** Transformar 2h de análise manual em 5min de revisão estruturada.

</vision>

<essential>
## What Must Be Nailed

- **1-click approval flow** — The structured review that enables fast, confident decisions. This is the core value: 2h manual analysis → 5min structured review.
- **Deterministic validation traceability** — The engineer confirms the system correctly identified the data. Fixed NETA/Microsoft rules, not probabilistic guessing.
- **Actionable findings** — Every finding tells the engineer WHAT is wrong and HOW to fix it (documentation correction vs retest needed).

</essential>

<specifics>
## Specific Ideas

- **API-driven architecture** — Backend provides structured data + PDF generation; frontend/workflow built separately
- **Finding codes** — Each finding type has a code (GND-01, THM-02, etc.) for quick reference
- **Two types of remediation** — Distinguish between "fix the report" (documentation error) vs "retest required" (real failure)
- **Minimal PDF design** — Engineer-focused, not exec-focused. Tables, severity badges, clear pass/fail. No firulas.

</specifics>

<notes>
## Additional Context

The audit trail isn't primarily for compliance documentation or debugging — it's for enabling the approval workflow. The engineer reviews the structured summary, confirms the system got it right, and approves with confidence.

The validation is deterministic (fixed rules from NETA/Microsoft standards), so the audit trail proves HOW each finding was generated (which rule + which input data).

</notes>

---

*Phase: 06-reporting-audit*
*Context gathered: 2026-01-16*
