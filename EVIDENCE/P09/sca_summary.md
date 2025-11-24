# SCA Summary

**Generated at:** 2025-11-24 17:25:27 UTC
**Commit:** `8d06432f8748fe145df8b7e50100ab66d3cef31b`
**Workflow Run:** [\#6](https://github.com/Davonchik/course-project-Davonchik/actions/runs/19643208216)
**Branch:** `p09-sbom-sca`

## Vulnerability Summary by Severity

| Severity | Count |
|----------|-------|
| High | 2 |
| Medium | 5 |

**Waived findings:** 0

## ⚠️ Critical/High Vulnerabilities

**Critical:** 0 | **High:** 2

### Top 10 Critical/High Findings

#### GHSA-5j98-mcp5-4vw2
- **Package**: `glob@10.4.5`
- **Severity**: High
- **Type**: npm
- **Description**: glob CLI: Command injection via -c/--cmd executes matches with shell:true
- **Fixed in**: 10.5.0

#### GHSA-rp65-9cf3-cjxr
- **Package**: `nth-check@1.0.2`
- **Severity**: High
- **Type**: npm
- **Description**: Inefficient Regular Expression Complexity in nth-check
- **Fixed in**: 2.0.1


## Next Steps

1. Review Critical/High vulnerabilities above
2. Update dependencies or create waivers in `policy/waivers.yml`
3. See full report in `sca_report.json` for details
