# Yehor Hrabovskyi

Backend-first .NET developer in Kyiv. I write backends, and I fix the ones that fail quietly.

By day I work on trade and payment flows, reconciliation and third-party integrations for a European crypto brokerage. Off hours I run everything on one Hetzner box, deploy it from Git, and write down what breaks. Open to contract work.

[hrabovskyi.online](https://hrabovskyi.online) · [Writing](https://hrabovskyi.online/writing) · [LinkedIn](https://www.linkedin.com/in/yehor-hrabovskyi)

## Built

| | |
|---|---|
| [**Attest**](https://github.com/Egoushka/attest) | Validates national ID, tax ID, VAT and postal codes for 87 countries, each against the rule the country publishes. A fork of CountryValidator with 197 defects fixed. On [NuGet](https://www.nuget.org/packages/Attest). |
| [**chargehand**](https://github.com/Egoushka/chargehand) | Runs a question about a codebase on coding agents and returns an answer whose every citation is checked against a pinned commit. CLI, HTTP and MCP. |
| [**Chronicle**](https://github.com/Egoushka/chronicle) | Seven years of my chat history, searchable by an assistant over MCP. It refuses to index the 65% that says "ok". |
| [**switchboard**](https://github.com/Egoushka/switchboard) | One MCP front door to every homelab tool: search, describe, read, approved write. |
| [**devbox-mcp**](https://github.com/Egoushka/devbox-mcp) | Runs a project's real test suite and SonarQube scans in throwaway, socket-proxied containers. |
| [**agent-skills**](https://github.com/Egoushka/agent-skills) | Commit-pinned skills for Claude Code, OpenCode and Codex, with a self-hosted reference search. |

## Writing

- [The library rejected all 36 million valid Hungarian tax numbers](https://hrabovskyi.online/writing/attest)
- [The deploy said success. Nothing had deployed for 51 days.](https://hrabovskyi.online/writing/silent-deploys)
- [My private services were on the public internet. DNS was the only thing hiding them.](https://hrabovskyi.online/writing/dns-is-not-access-control)

## Stack

- **Day job:** C#, ASP.NET Core, EF Core, MediatR, SQL Server, Angular, NgRx, xUnit
- **Own projects:** C#, Python, PostgreSQL, MCP, Testcontainers, Moq, FluentAssertions
- **The box:** Docker Compose, Caddy, Cloudflare, Tailscale, GitOps with SOPS + age
