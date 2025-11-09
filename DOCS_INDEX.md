# 📚 DOCUMENTATION INDEX

**Last Updated**: 2025-11-02 21:00 UTC

---

## 🎯 FOR NEXT AGENT

**Start here**: [`START_HERE.md`](./START_HERE.md)

**Main handoff**: [`HANDOFF_FOR_NEXT_AGENT.md`](./HANDOFF_FOR_NEXT_AGENT.md)

---

## 📁 DOCUMENT CATEGORIES

### 1️⃣ CURRENT SESSION (2025-11-02)

**Handoff & Status**:
- [`HANDOFF_FOR_NEXT_AGENT.md`](./HANDOFF_FOR_NEXT_AGENT.md) ⭐ **READ THIS**
- [`START_HERE.md`](./START_HERE.md) - Quick navigation
- [`DOCS_INDEX.md`](./DOCS_INDEX.md) - This file

**Technical Details**:
- [`PROOF_OF_DATA_CAPTURE.md`](./PROOF_OF_DATA_CAPTURE.md) - How code works
- [`CRITICAL_FINDING_CORRELATION_WORKS.md`](./CRITICAL_FINDING_CORRELATION_WORKS.md) - Breakthrough discovery
- [`CRITICAL_FINDING_SUPABASE_DELETED.md`](./CRITICAL_FINDING_SUPABASE_DELETED.md) - Credential issue

**Data Quality**:
- [`BAD_VS_GOOD_DATA_COMPARISON.csv`](./BAD_VS_GOOD_DATA_COMPARISON.csv) - Expected vs actual
- [`SUPABASE_EXPORT.csv`](./SUPABASE_EXPORT.csv) - Current bad data (200 records)
- [`MULTI_URL_TEST_RESULTS.csv`](./MULTI_URL_TEST_RESULTS.csv) - Test output (1 record)

---

### 2️⃣ PROJECT DOCUMENTATION

**Configuration**:
- [`CLAUDE.md`](./CLAUDE.md) - Project overview, credentials, architecture

**Code**:
- [`src/parser/yclients_parser.py`](./src/parser/yclients_parser.py) - Main parser
  - Lines 617: Dedup fix
  - Lines 769: Requires date+time
  - Lines 563-630: Correlation logic
- [`src/database/db_manager.py`](./src/database/db_manager.py) - Supabase integration

**Tests**:
- [`test_production_code.py`](./test_production_code.py) - Production code wrapper
- [`export_supabase_csv.py`](./export_supabase_csv.py) - Export current data
- [`test_multiple_urls_dates.py`](./test_multiple_urls_dates.py) - Multi-URL test
- [`test_and_export_csv.py`](./test_and_export_csv.py) - Combined test+export

---

### 3️⃣ ARCHIVED (OUTDATED)

**All previous session docs** → [`archive/old-handoffs-2025-11-02/`](./archive/old-handoffs-2025-11-02/)

Includes:
- NEXT_AGENT_START_HERE.md (superseded by HANDOFF_FOR_NEXT_AGENT.md)
- SCOUT_REPORT_NEXT_AGENT.md (outdated analysis)
- SESSION_COMPLETE_SUMMARY.md (old status)
- And 10 more old handoffs...

**⚠️ Do not use archived docs** - they're outdated and conflicting

---

### 4️⃣ ANALYSIS & DIAGNOSTICS

**Session Records**:
- [`COMPLETE_HANDOFF_FINAL.md`](./COMPLETE_HANDOFF_FINAL.md) - Historical context
- [`DATA_QUALITY_ANALYSIS.md`](./DATA_QUALITY_ANALYSIS.md) - Data quality issues
- [`LOG_ANALYSIS_FINDINGS.md`](./LOG_ANALYSIS_FINDINGS.md) - Log analysis

**Technical Investigations**:
- [`DEEP_CODE_REVIEW_FINDINGS.md`](./DEEP_CODE_REVIEW_FINDINGS.md) - Code review
- [`YCLIENTS_ROOT_CAUSE_ANALYSIS.md`](./YCLIENTS_ROOT_CAUSE_ANALYSIS.md) - Root cause

**Deployment**:
- [`DEPLOYMENT_STATUS_2025-10-13.md`](./DEPLOYMENT_STATUS_2025-10-13.md) - Oct deployment
- [`CRITICAL_DNS_ISSUE.md`](./CRITICAL_DNS_ISSUE.md) - DNS/Supabase issue

---

## 🗺️ NAVIGATION GUIDE

**New agent joining?**
1. Read [`START_HERE.md`](./START_HERE.md) (2 min)
2. Read [`HANDOFF_FOR_NEXT_AGENT.md`](./HANDOFF_FOR_NEXT_AGENT.md) (5 min)
3. Run test: `python3 test_production_code.py`
4. Done!

**Need technical details?**
- How code works: [`PROOF_OF_DATA_CAPTURE.md`](./PROOF_OF_DATA_CAPTURE.md)
- Code location: `src/parser/yclients_parser.py:563-630`
- Credentials: [`CLAUDE.md`](./CLAUDE.md) lines 217-219

**Need historical context?**
```bash
git log --oneline -20
git show d57b2cd  # Line 754 + dedup fix
git show 3c20202  # Proof of data capture
```

**Confused by old docs?**
- All pre-2025-11-02 docs → `archive/old-handoffs-2025-11-02/`
- They're outdated, don't read them
- Current state → `HANDOFF_FOR_NEXT_AGENT.md`

---

## 📊 DOCUMENT STATUS

| Document | Status | Last Updated | Read? |
|----------|--------|--------------|-------|
| START_HERE.md | ✅ Current | 2025-11-02 | ⭐ YES |
| HANDOFF_FOR_NEXT_AGENT.md | ✅ Current | 2025-11-02 | ⭐ YES |
| CLAUDE.md | ✅ Current | 2025-11-02 | If needed |
| PROOF_OF_DATA_CAPTURE.md | ✅ Current | 2025-11-02 | If needed |
| archive/* | ⚠️ Outdated | Various | ❌ NO |

---

## 🔧 MAINTENANCE

**When creating new docs:**
1. Update this index
2. Add to appropriate category
3. Archive old docs if superseded
4. Update STATUS table above

**When archiving:**
1. Move to `archive/old-[reason]-[date]/`
2. Create ARCHIVE_README.md in folder
3. Update this index
4. Remove from current docs list

---

**Questions?** Check `HANDOFF_FOR_NEXT_AGENT.md` or `START_HERE.md`
