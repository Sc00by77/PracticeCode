# Edge Monitor — Enterprise Healthcheck Agent v2.0

A Splunk-grade PowerShell monitoring agent that sends structured telemetry
to `healthchecks.edge.evc-net.com` on every scheduled run.

---

## Files

| File | Purpose |
|---|---|
| `healthchecks.ps1` | Main agent — collect & ping |
| `Setup-EdgeMonitor.ps1` | One-time Task Scheduler registration (run as Admin) |
| `Logs\edge-monitor.log` | Human-readable flat log (auto-rotated) |
| `Logs\edge-monitor-events.jsonl` | **Splunk-ready JSONL** — point your Universal Forwarder here |

---

## Quick Start

```powershell
# 1. Place both .ps1 files in C:\Scripts\
# 2. Edit healthchecks.ps1 — set your UUID:
#       $UUID = "your-actual-uuid-here"
# 3. Register the scheduled task (as Administrator):
powershell.exe -ExecutionPolicy Bypass -File C:\Scripts\Setup-EdgeMonitor.ps1
```

---

## What Gets Collected

### System Identity
- Hostname, domain, IP addresses, OS version + build
- BIOS version, timezone, PowerShell version
- Uptime, last boot time, **pending reboot flag**

### Performance
- CPU % (averaged across all cores) + model + core count
- RAM used/free/total GB + %
- All drives: used/free/total GB + % per drive letter

### Network
- All physical NICs: speed, RX/TX bytes, error counts, MAC
- Default gateway RTT (ms)
- Active established TCP connection count

### Process Intelligence
- Top-N processes by CPU time
- Top-N processes by RAM (Working Set)
- Total process count

### Services Watchdog
- Monitors configurable list of Windows services
- **Auto-restarts** stopped services and reports recovery

### Connectivity Checks
- TCP port reachability with latency (ms) per target
- DNS resolution time + resolved IP per domain
- TLS certificate expiry (days remaining) per HTTPS endpoint

### Windows Event Log
- Error/Critical event count (System + Application) in last N minutes
- Warning count
- Top error sources by event provider name

### Security Posture
- Windows Firewall status per profile (Domain/Private/Public)
- Windows Defender: enabled, real-time protection, signature age, last scan
- Failed login attempts (Event ID 4625) in last hour

---

## Ping Behaviour

| Condition | Endpoint called |
|---|---|
| Script starts | `/ping/<uuid>/start` |
| All checks pass | `POST /ping/<uuid>` with full telemetry body |
| Any check fails threshold | `POST /ping/<uuid>/fail` with degraded summary |
| Ping request itself fails | Retried up to 3× with exponential backoff |

---

## Splunk Integration

The agent writes a `.jsonl` file at `C:\Scripts\Logs\edge-monitor-events.jsonl`
with one JSON object per run in Splunk HEC format:

```json
{
  "time": 1712345678,
  "host": "EDGE-NODE-01",
  "source": "edge-monitor",
  "sourcetype": "edge:healthcheck",
  "event": { "cpu_pct": 12.3, "ram_pct": 54.1, ... }
}
```

**Universal Forwarder inputs.conf:**
```ini
[monitor://C:\Scripts\Logs\edge-monitor-events.jsonl]
sourcetype = edge:healthcheck
index      = edge_monitoring
```

---

## CLI Flags

```powershell
# Dry run — collect everything, print logs, but don't send the ping
.\healthchecks.ps1 -DryRun

# Print full JSON payload to stdout (pipe into jq, etc.)
.\healthchecks.ps1 -JsonOnly

# Use an external JSON config file
.\healthchecks.ps1 -ConfigOverride C:\Scripts\monitor-config.json

# Verbose debug logging
.\healthchecks.ps1 -Verbose
```

---

## Thresholds (edit in $DEFAULT_CONFIG)

| Key | Default | Meaning |
|---|---|---|
| `CpuPct` | 90 | CPU % to trigger fail |
| `RamPct` | 90 | RAM % to trigger fail |
| `DiskPct` | 85 | Disk % to trigger fail |
| `DiskFreeGB` | 5 | Minimum free GB on any drive |
| `LatencyMs` | 200 | Gateway RTT threshold |
| `EventLogErrors` | 10 | Max Windows errors in window |
| `CertExpiryDays` | 30 | Warn if cert expires within N days |

---

## Exit Codes

| Code | Meaning |
|---|---|
| 0 | All checks passed, ping sent |
| 1 | One or more checks degraded, fail ping sent |
| 2 | Checks passed but ping request failed after retries |
