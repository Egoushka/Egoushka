# Yehor Hrabovskyi

**I write .NET backends and fix the ones that fail quietly.**

Kyiv. By day, trade and payment flows, reconciliation and third-party integrations on a European crypto brokerage. After hours, one Hetzner box that runs everything I build, and notes on what broke. Open to contract work.

[hrabovskyi.online](https://hrabovskyi.online) · [LinkedIn](https://www.linkedin.com/in/yehor-hrabovskyi) · [RSS](https://hrabovskyi.online/feed.xml)

## I assumed. Then I counted.

| Assumed | Counted | |
|---|---|---|
| The pipeline is green, so the site is current | Nothing had shipped for **51 days** | [read](https://hrabovskyi.online/writing/silent-deploys) |
| Services on tailnet addresses are private | Every one answered **200** to the open internet | [read](https://hrabovskyi.online/writing/dns-is-not-access-control) |
| A popular NuGet package validates tax IDs | It rejected all **36 million** valid Hungarian ones, one of **197** defects | [read](https://hrabovskyi.online/writing/attest) |
| An assistant's memory improves as it grows | **5,357** stored facts, **0** ever marked wrong | [read](https://hrabovskyi.online/writing/synapse) |
| My orchestrator beats a plain agent session | It lost the blind test **0.333 to 0.667** | [read](https://hrabovskyi.online/writing/chargehand-blind-test) |
| Seven years of my chats are worth indexing | **Two thirds** of them say "ок" | [read](https://hrabovskyi.online/writing/chronicle) |

## Right now

<!-- status:start -->
```text
one Hetzner box, Nuremberg                     read 2026-09-29 13:20 UTC
containers    123 running, 0 unhealthy
coding        32 h in the last 30 days: C# 31%, Markdown 28%, Html 11%
attest        v1.2.1, 495 NuGet installs
```
<!-- status:end -->
<!-- latest:start -->
Latest post: [My agent orchestrator lost its first blind test, 0.333 to 0.667](https://hrabovskyi.online/writing/chargehand-blind-test/) (29 September 2026)
<!-- latest:end -->

<sub>Not typed. A cron job on the box writes [status.json](https://hrabovskyi.online/status.json), and a [daily Action](https://github.com/Egoushka/Egoushka/blob/main/.github/workflows/refresh.yml) copies it here. If the box stops reporting, this block says so.</sub>

## Built, and still running

- **[Attest](https://github.com/Egoushka/attest)** · C# · [NuGet](https://www.nuget.org/packages/Attest). National ID, tax ID, VAT and postal codes for 87 countries, each checked against the rule the country publishes.
- **[chargehand](https://github.com/Egoushka/chargehand)** · C#. Runs a question about a codebase on coding agents and checks every citation in the answer against a pinned commit.
- **[Chronicle](https://github.com/Egoushka/chronicle)** · Python, pgvector. Seven years of chat history, searchable by an assistant over MCP.
- **[Nytka](https://github.com/nytka-app/server)** · ASP.NET Core, Android. A self-hosted home for an Omi necklace's conversations and memories. Building it now.
- **[switchboard](https://github.com/Egoushka/switchboard)** · Python. One MCP front door to every tool on the box.
- **[devbox-mcp](https://github.com/Egoushka/devbox-mcp)**. A project's real test suite and SonarQube scan, in throwaway containers.
- **[agent-skills](https://github.com/Egoushka/agent-skills)**. Commit-pinned skills for Claude Code, OpenCode and Codex.

<sub>C# · ASP.NET Core · EF Core · SQL Server · PostgreSQL · Angular · Python · Docker Compose · Tailscale · SOPS + age</sub>
