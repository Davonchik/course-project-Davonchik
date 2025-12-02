# SCA Summary

**Generated at:** 2025-12-02 18:36:05 UTC
**Commit:** `5e10738c6b10887006bf0e3161c75ccb886fa671`
**Workflow Run:** [\#29](https://github.com/Davonchik/course-project-Davonchik/actions/runs/19869528168)
**Branch:** `hotfix`

## Vulnerability Summary by Severity

| Severity | Count |
|----------|-------|
| High | 4 |
| Low | 1 |
| Medium | 6 |

**Waived findings:** 0

## ⚠️ Critical/High Vulnerabilities

**Critical:** 0 | **High:** 4

### Top 10 Critical/High Findings

#### GHSA-5j98-mcp5-4vw2
- **Package**: `glob@10.4.5`
- **Severity**: High
- **Type**: npm
- **Description**: glob CLI: Command injection via -c/--cmd executes matches with shell:true
- **Fixed in**: 10.5.0

#### GHSA-5gfm-wpxj-wjgq
- **Package**: `node-forge@1.3.1`
- **Severity**: High
- **Type**: npm
- **Description**: node-forge has an Interpretation Conflict vulnerability via its ASN.1 Validator Desynchronization
- **Fixed in**: 1.3.2

#### GHSA-554w-wpv2-vw27
- **Package**: `node-forge@1.3.1`
- **Severity**: High
- **Type**: npm
- **Description**: node-forge has ASN.1 Unbounded Recursion
- **Fixed in**: 1.3.2

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
