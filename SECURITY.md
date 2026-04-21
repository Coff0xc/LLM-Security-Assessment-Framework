# Security Policy

## Supported Versions

| Version | Supported          |
|---------|--------------------|
| 1.2.x   | :white_check_mark: |
| < 1.2   | :x:                |

## Reporting a Vulnerability

If you discover a security vulnerability in FORGEDAN, please report it responsibly:

1. **DO NOT** open a public GitHub issue
2. Email: https://github.com/Coff0xc/LLM-Security-Assessment-Framework/security/advisories/new
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

We will acknowledge receipt within 48 hours and provide a timeline for a fix.

## Security Measures

FORGEDAN implements the following security measures:

- **No Pickle serialization** — JSON-based checkpoint system to prevent RCE
- **HMAC API key comparison** — Timing-attack resistant authentication
- **CORS configuration** — Configurable allowed origins (no wildcard in production)
- **Path traversal protection** — Filename validation on all file access endpoints
- **API key masking** — Sensitive data redacted in all logs
- **Header-only authentication** — API keys never passed via URL parameters

## Responsible Use

This tool is designed for **authorized security testing only**. Users must:

- Obtain explicit authorization before testing any LLM system
- Follow responsible disclosure practices for any vulnerabilities found
- Comply with applicable laws and regulations
- Never use this tool for malicious purposes
