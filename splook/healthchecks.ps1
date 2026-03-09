# ==============================================================================
#  EDGE MONITOR — Enterprise Healthcheck Agent  v2.0
#  Compatible with: healthchecks.edge.evc-net.com
#  Log format   : Splunk-compatible JSON (key=value structured events)
#
#  Task Scheduler:
#    Program  : powershell.exe
#    Arguments: -ExecutionPolicy Bypass -File C:\Scripts\healthchecks.ps1
#
#  Manual run:
#    powershell.exe -ExecutionPolicy Bypass -File C:\Scripts\healthchecks.ps1
#    powershell.exe -ExecutionPolicy Bypass -File C:\Scripts\healthchecks.ps1 -Verbose
#    powershell.exe -ExecutionPolicy Bypass -File C:\Scripts\healthchecks.ps1 -DryRun
# ==============================================================================

[CmdletBinding()]
param(
    [switch]$DryRun,          # Collect everything but do NOT send the ping
    [switch]$JsonOnly,        # Print full JSON payload to stdout and exit
    [string]$ConfigOverride   # Path to an external JSON config file
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# ─────────────────────────────────────────────────────────────────────────────
#  CONFIGURATION BLOCK  (override via -ConfigOverride path\to\config.json)
# ─────────────────────────────────────────────────────────────────────────────
$DEFAULT_CONFIG = @{

    # ── Healthchecks endpoint ──────────────────────────────────────────────
    BaseUrl    = "http://healthchecks.edge.evc-net.com:80/ping"
    UUID       = "your-uuid-here"          # <<< REPLACE
    TimeoutSec = 30
    RetryCount = 3
    RetryDelaySeconds = 5                  # base delay; doubles on each retry

    # ── Logging ───────────────────────────────────────────────────────────
    LogFile      = "C:\Scripts\Logs\edge-monitor.log"
    LogMaxLines  = 2000
    LogLevel     = "INFO"                  # DEBUG | INFO | WARN | ERROR
    JsonLogFile  = "C:\Scripts\Logs\edge-monitor-events.jsonl"  # JSONL for Splunk forwarder

    # ── Thresholds (triggers /fail ping) ──────────────────────────────────
    Thresholds = @{
        CpuPct         = 90
        RamPct         = 90
        DiskPct        = 85
        DiskFreeGB     = 5          # alert if free space drops below this
        LatencyMs      = 200        # ping RTT to gateway
        EventLogErrors = 10         # Windows errors in last interval
        CertExpiryDays = 30         # TLS cert warn if expiring within N days
    }

    # ── Services to watch ─────────────────────────────────────────────────
    WatchServices = @(
        "Winmgmt",      # WMI
        "EventLog",     # Windows Event Log
        "Dnscache",     # DNS Client
        "LanmanServer", # File & Printer Sharing
        "W32Time"       # Windows Time
        # Add your own: "nginx", "postgresql", "myapp-svc", etc.
    )

    # ── TCP port reachability checks ──────────────────────────────────────
    PortChecks = @(
        @{ Host = "8.8.8.8";     Port = 53;  Label = "dns_google"   },
        @{ Host = "1.1.1.1";     Port = 53;  Label = "dns_cloudflare"},
        @{ Host = "healthchecks.edge.evc-net.com"; Port = 80; Label = "healthcheck_endpoint" }
        # @{ Host = "your-db";  Port = 5432; Label = "postgres" }
    )

    # ── TLS certificate expiry checks ─────────────────────────────────────
    TlsChecks = @(
        # @{ Host = "your-api.example.com"; Port = 443; Label = "main_api" }
    )

    # ── DNS resolution spot-checks ────────────────────────────────────────
    DnsChecks = @(
        "healthchecks.edge.evc-net.com",
        "google.com"
    )

    # ── Top-N process telemetry ───────────────────────────────────────────
    TopProcessCount = 5

    # ── Windows Event Log scrape (minutes lookback per run) ───────────────
    EventLogLookbackMinutes = 10
    EventLogMaxEntries      = 20
}

# Merge external config if supplied
$CFG = $DEFAULT_CONFIG
if ($ConfigOverride -and (Test-Path $ConfigOverride)) {
    $ext = Get-Content $ConfigOverride -Raw | ConvertFrom-Json
    $ext.PSObject.Properties | ForEach-Object { $CFG[$_.Name] = $_.Value }
}

# ─────────────────────────────────────────────────────────────────────────────
#  STRUCTURED LOGGER  (Splunk key=value + JSONL dual output)
# ─────────────────────────────────────────────────────────────────────────────
$SCRIPT_START = Get-Date
$LOG_LEVELS   = @{ DEBUG=0; INFO=1; WARN=2; ERROR=3 }
$EVENTS       = [System.Collections.Generic.List[hashtable]]::new()

function Write-Log {
    param(
        [string]$Message,
        [string]$Level = "INFO",
        [hashtable]$Fields = @{}
    )

    if ($LOG_LEVELS[$Level] -lt $LOG_LEVELS[$CFG.LogLevel]) { return }

    $ts    = Get-Date -Format "yyyy-MM-ddTHH:mm:ss.fffZ"
    $host_ = $env:COMPUTERNAME

    # Build Splunk-style key=value line
    $kv = "time=$ts level=$Level host=$host_ msg=`"$Message`""
    foreach ($k in $Fields.Keys) { $kv += " $k=$($Fields[$k])" }

    # Build JSON event (for JSONL / Splunk HEC)
    $event = @{
        time   = $ts
        level  = $Level
        host   = $host_
        msg    = $Message
        source = "edge-monitor"
    }
    $Fields.Keys | ForEach-Object { $event[$_] = $Fields[$_] }
    $EVENTS.Add($event)

    # Console
    $color = switch ($Level) { "WARN" {"Yellow"} "ERROR" {"Red"} "DEBUG" {"Gray"} default {"Cyan"} }
    Write-Host $kv -ForegroundColor $color

    # Flat log file
    $logDir = Split-Path $CFG.LogFile
    if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir -Force | Out-Null }
    Add-Content -Path $CFG.LogFile -Value $kv

    # JSONL file (Splunk forwarder picks this up)
    Add-Content -Path $CFG.JsonLogFile -Value ($event | ConvertTo-Json -Compress)

    # Rotate flat log
    $lines = @(Get-Content $CFG.LogFile -ErrorAction SilentlyContinue)
    if ($lines.Count -gt $CFG.LogMaxLines) {
        $lines | Select-Object -Last ([int]($CFG.LogMaxLines / 2)) | Set-Content $CFG.LogFile
    }
}

# ─────────────────────────────────────────────────────────────────────────────
#  HEALTHCHECKS PING  (success / fail / start)
# ─────────────────────────────────────────────────────────────────────────────
function Send-Ping {
    param(
        [string]$Suffix = "",      # "" = success | "/fail" | "/start"
        [string]$Body   = ""
    )

    if ($DryRun) {
        Write-Log "DRY-RUN: would POST to $($CFG.BaseUrl)/$($CFG.UUID)$Suffix" "INFO"
        return $true
    }

    $uri     = "$($CFG.BaseUrl)/$($CFG.UUID)$Suffix"
    $attempt = 0
    $delay   = $CFG.RetryDelaySeconds

    while ($attempt -lt $CFG.RetryCount) {
        $attempt++
        try {
            $params = @{
                Uri        = $uri
                Method     = if ($Body) { "Post" } else { "Get" }
                TimeoutSec = $CFG.TimeoutSec
            }
            if ($Body) { $params.Body = $Body }
            Invoke-RestMethod @params | Out-Null
            Write-Log "Ping sent" "INFO" @{ uri=$uri; attempt=$attempt; suffix=$Suffix }
            return $true
        } catch {
            Write-Log "Ping attempt $attempt failed: $_" "WARN" @{ uri=$uri }
            if ($attempt -lt $CFG.RetryCount) {
                Start-Sleep -Seconds $delay
                $delay *= 2   # exponential backoff
            }
        }
    }

    Write-Log "All $($CFG.RetryCount) ping attempts exhausted" "ERROR" @{ uri=$uri }
    return $false
}

# ─────────────────────────────────────────────────────────────────────────────
#  COLLECTOR FUNCTIONS
# ─────────────────────────────────────────────────────────────────────────────

function Get-CpuMetrics {
    try {
        $samples = Get-CimInstance Win32_Processor
        $avg     = [math]::Round(($samples | Measure-Object -Property LoadPercentage -Average).Average, 1)
        $cores   = ($samples | Measure-Object -Property NumberOfLogicalProcessors -Sum).Sum
        $model   = ($samples | Select-Object -First 1).Name.Trim()
        return @{ cpu_pct=$avg; cpu_cores=$cores; cpu_model=$model; cpu_ok=($avg -lt $CFG.Thresholds.CpuPct) }
    } catch {
        Write-Log "CPU collection failed: $_" "WARN"
        return @{ cpu_pct="N/A"; cpu_ok=$false; cpu_error="$_" }
    }
}

function Get-RamMetrics {
    try {
        $os       = Get-CimInstance Win32_OperatingSystem
        $total    = [math]::Round($os.TotalVisibleMemorySize / 1MB, 2)
        $free     = [math]::Round($os.FreePhysicalMemory / 1MB, 2)
        $used     = [math]::Round($total - $free, 2)
        $pct      = [math]::Round(($used / $total) * 100, 1)
        return @{
            ram_used_gb=$used; ram_free_gb=$free; ram_total_gb=$total
            ram_pct=$pct; ram_ok=($pct -lt $CFG.Thresholds.RamPct)
        }
    } catch {
        Write-Log "RAM collection failed: $_" "WARN"
        return @{ ram_pct="N/A"; ram_ok=$false; ram_error="$_" }
    }
}

function Get-DiskMetrics {
    $results = @{}
    try {
        $drives = Get-PSDrive -PSProvider FileSystem | Where-Object { $_.Used -ne $null }
        $alerts = @()
        foreach ($d in $drives) {
            $total = [math]::Round(($d.Used + $d.Free) / 1GB, 2)
            $used  = [math]::Round($d.Used / 1GB, 2)
            $free  = [math]::Round($d.Free / 1GB, 2)
            $pct   = if ($total -gt 0) { [math]::Round(($used / $total) * 100, 1) } else { 0 }
            $label = $d.Name
            $results["disk_${label}_used_gb"]  = $used
            $results["disk_${label}_free_gb"]  = $free
            $results["disk_${label}_total_gb"] = $total
            $results["disk_${label}_pct"]      = $pct
            if ($pct -ge $CFG.Thresholds.DiskPct -or $free -le $CFG.Thresholds.DiskFreeGB) {
                $alerts += "${label}:${pct}%"
            }
        }
        $results["disk_alerts"] = if ($alerts) { $alerts -join "|" } else { "none" }
        $results["disk_ok"]     = ($alerts.Count -eq 0)
    } catch {
        Write-Log "Disk collection failed: $_" "WARN"
        $results["disk_ok"]    = $false
        $results["disk_error"] = "$_"
    }
    return $results
}

function Get-NetworkMetrics {
    $results = @{}
    try {
        $adapters = Get-NetAdapter | Where-Object { $_.Status -eq "Up" -and $_.Virtual -eq $false }
        $adapterNames = @()
        foreach ($a in $adapters) {
            $stats = Get-NetAdapterStatistics -Name $a.Name -ErrorAction SilentlyContinue
            $label = ($a.Name -replace '\s+','_').ToLower()
            $adapterNames += $label
            $results["nic_${label}_speed_mbps"]    = [math]::Round($a.LinkSpeed / 1MB, 0)
            $results["nic_${label}_rx_bytes"]      = $stats.ReceivedBytes
            $results["nic_${label}_tx_bytes"]      = $stats.SentBytes
            $results["nic_${label}_rx_errors"]     = $stats.ReceivedPacketErrors
            $results["nic_${label}_tx_errors"]     = $stats.OutboundPacketErrors
            $results["nic_${label}_mac"]           = $a.MacAddress
        }
        $results["nic_active_count"] = $adapters.Count
        $results["nic_adapters"]     = $adapterNames -join "|"

        # Gateway ping
        $gw = (Get-NetRoute -DestinationPrefix "0.0.0.0/0" -ErrorAction SilentlyContinue |
               Sort-Object RouteMetric | Select-Object -First 1).NextHop
        if ($gw) {
            $ping = Test-Connection -ComputerName $gw -Count 2 -ErrorAction SilentlyContinue
            $rtt  = if ($ping) { [math]::Round(($ping | Measure-Object -Property ResponseTime -Average).Average, 1) } else { -1 }
            $results["gateway_ip"]      = $gw
            $results["gateway_rtt_ms"]  = $rtt
            $results["gateway_ok"]      = ($rtt -ge 0 -and $rtt -lt $CFG.Thresholds.LatencyMs)
        }

        # Active TCP connections count
        $tcpCount = (Get-NetTCPConnection -State Established -ErrorAction SilentlyContinue).Count
        $results["tcp_established"] = $tcpCount

    } catch {
        Write-Log "Network collection failed: $_" "WARN"
        $results["network_error"] = "$_"
    }
    return $results
}

function Get-TopProcesses {
    $results = @{}
    try {
        $procs = Get-Process | Where-Object { $_.CPU -ne $null } |
                 Sort-Object CPU -Descending |
                 Select-Object -First $CFG.TopProcessCount

        $topCpu = @()
        foreach ($p in $procs) {
            $topCpu += "$($p.ProcessName)[$($p.Id)]:$([math]::Round($p.CPU,1))s"
        }
        $results["top_cpu_procs"] = $topCpu -join "|"

        $topRam = Get-Process | Sort-Object WorkingSet64 -Descending |
                  Select-Object -First $CFG.TopProcessCount
        $topRamStr = @()
        foreach ($p in $topRam) {
            $mb = [math]::Round($p.WorkingSet64 / 1MB, 1)
            $topRamStr += "$($p.ProcessName)[$($p.Id)]:${mb}MB"
        }
        $results["top_ram_procs"]  = $topRamStr -join "|"
        $results["process_total"]  = (Get-Process).Count
        $results["process_ok"]     = $true
    } catch {
        Write-Log "Process collection failed: $_" "WARN"
        $results["process_ok"]    = $false
        $results["process_error"] = "$_"
    }
    return $results
}

function Get-ServiceMetrics {
    $results   = @{}
    $failed    = @()
    $recovered = @()
    try {
        foreach ($svc in $CFG.WatchServices) {
            $s = Get-Service -Name $svc -ErrorAction SilentlyContinue
            if (-not $s) {
                $results["svc_${svc}"] = "NOT_FOUND"
                $failed += $svc
            } elseif ($s.Status -ne "Running") {
                $results["svc_${svc}"] = $s.Status.ToString()
                $failed += $svc
                # Attempt auto-restart for non-critical services
                try {
                    Start-Service -Name $svc -ErrorAction SilentlyContinue
                    Start-Sleep -Seconds 2
                    $s.Refresh()
                    if ($s.Status -eq "Running") {
                        $recovered += $svc
                        $results["svc_${svc}"] = "RECOVERED"
                        Write-Log "Service auto-restarted: $svc" "WARN" @{ service=$svc }
                    }
                } catch { <# silent #> }
            } else {
                $results["svc_${svc}"] = "Running"
            }
        }
        $results["svc_failed"]    = if ($failed)    { $failed -join "|"    } else { "none" }
        $results["svc_recovered"] = if ($recovered) { $recovered -join "|" } else { "none" }
        $results["svc_ok"]        = ($failed.Count -eq 0 -or $failed.Count -eq $recovered.Count)
    } catch {
        Write-Log "Service check failed: $_" "WARN"
        $results["svc_ok"]    = $false
        $results["svc_error"] = "$_"
    }
    return $results
}

function Get-PortChecks {
    $results = @{}
    $failed  = @()
    foreach ($check in $CFG.PortChecks) {
        try {
            $sw  = [System.Diagnostics.Stopwatch]::StartNew()
            $tcp = New-Object System.Net.Sockets.TcpClient
            $tcp.ConnectAsync($check.Host, $check.Port).Wait($CFG.TimeoutSec * 1000) | Out-Null
            $sw.Stop()
            $latency = $sw.ElapsedMilliseconds
            $open    = $tcp.Connected
            $tcp.Close()
            $results["port_$($check.Label)_open"]       = $open
            $results["port_$($check.Label)_latency_ms"] = $latency
            if (-not $open) { $failed += $check.Label }
        } catch {
            $results["port_$($check.Label)_open"]  = $false
            $results["port_$($check.Label)_error"] = "$_"
            $failed += $check.Label
        }
    }
    $results["port_failed"] = if ($failed) { $failed -join "|" } else { "none" }
    $results["port_ok"]     = ($failed.Count -eq 0)
    return $results
}

function Get-DnsChecks {
    $results = @{}
    $failed  = @()
    foreach ($domain in $CFG.DnsChecks) {
        try {
            $sw  = [System.Diagnostics.Stopwatch]::StartNew()
            $res = [System.Net.Dns]::GetHostAddresses($domain)
            $sw.Stop()
            $label = ($domain -replace '[^a-zA-Z0-9]','_')
            $results["dns_${label}_resolved"] = $true
            $results["dns_${label}_ms"]       = $sw.ElapsedMilliseconds
            $results["dns_${label}_ip"]       = $res[0].IPAddressToString
        } catch {
            $label = ($domain -replace '[^a-zA-Z0-9]','_')
            $results["dns_${label}_resolved"] = $false
            $results["dns_${label}_error"]    = "$_"
            $failed += $domain
        }
    }
    $results["dns_failed"] = if ($failed) { $failed -join "|" } else { "none" }
    $results["dns_ok"]     = ($failed.Count -eq 0)
    return $results
}

function Get-TlsCertChecks {
    $results = @{}
    $expiring = @()
    foreach ($check in $CFG.TlsChecks) {
        try {
            $tcp  = New-Object System.Net.Sockets.TcpClient($check.Host, $check.Port)
            $ssl  = New-Object System.Net.Security.SslStream($tcp.GetStream(), $false,
                        ({ $true } -as [System.Net.Security.RemoteCertificateValidationCallback]))
            $ssl.AuthenticateAsClient($check.Host)
            $cert   = New-Object System.Security.Cryptography.X509Certificates.X509Certificate2($ssl.RemoteCertificate)
            $expiry = $cert.NotAfter
            $days   = ([math]::Floor(($expiry - (Get-Date)).TotalDays))
            $ssl.Close(); $tcp.Close()
            $results["tls_$($check.Label)_expiry"]      = $expiry.ToString("yyyy-MM-dd")
            $results["tls_$($check.Label)_days_left"]   = $days
            $results["tls_$($check.Label)_ok"]          = ($days -gt $CFG.Thresholds.CertExpiryDays)
            if ($days -le $CFG.Thresholds.CertExpiryDays) { $expiring += "$($check.Label):${days}d" }
        } catch {
            $results["tls_$($check.Label)_ok"]    = $false
            $results["tls_$($check.Label)_error"] = "$_"
            $expiring += "$($check.Label):ERROR"
        }
    }
    $results["tls_expiring"] = if ($expiring) { $expiring -join "|" } else { "none" }
    $results["tls_ok"]       = ($expiring.Count -eq 0)
    return $results
}

function Get-WindowsEventLogMetrics {
    $results = @{}
    try {
        $since   = (Get-Date).AddMinutes(-$CFG.EventLogLookbackMinutes)
        $errors  = Get-WinEvent -FilterHashtable @{
            LogName   = "System","Application"
            Level     = 1,2       # Critical=1, Error=2
            StartTime = $since
        } -MaxEvents $CFG.EventLogMaxEntries -ErrorAction SilentlyContinue

        $warnings = Get-WinEvent -FilterHashtable @{
            LogName   = "System","Application"
            Level     = 3         # Warning=3
            StartTime = $since
        } -MaxEvents $CFG.EventLogMaxEntries -ErrorAction SilentlyContinue

        $errCount  = if ($errors)   { @($errors).Count   } else { 0 }
        $warnCount = if ($warnings) { @($warnings).Count } else { 0 }

        # Summarize top error sources
        $topSources = @()
        if ($errors) {
            $topSources = @($errors) | Group-Object ProviderName |
                          Sort-Object Count -Descending |
                          Select-Object -First 5 |
                          ForEach-Object { "$($_.Name):$($_.Count)" }
        }

        $results["evtlog_errors"]       = $errCount
        $results["evtlog_warnings"]     = $warnCount
        $results["evtlog_top_sources"]  = if ($topSources) { $topSources -join "|" } else { "none" }
        $results["evtlog_lookback_min"] = $CFG.EventLogLookbackMinutes
        $results["evtlog_ok"]           = ($errCount -lt $CFG.Thresholds.EventLogErrors)

    } catch {
        Write-Log "Event log collection failed: $_" "WARN"
        $results["evtlog_ok"]    = $false
        $results["evtlog_error"] = "$_"
    }
    return $results
}

function Get-SystemIdentity {
    $results = @{}
    try {
        $os      = Get-CimInstance Win32_OperatingSystem
        $cs      = Get-CimInstance Win32_ComputerSystem
        $bios    = Get-CimInstance Win32_BIOS
        $uptime  = (Get-Date) - $os.LastBootUpTime

        $results["hostname"]        = $env:COMPUTERNAME
        $results["domain"]          = $cs.Domain
        $results["os"]              = $os.Caption.Trim()
        $results["os_build"]        = $os.BuildNumber
        $results["os_arch"]         = $os.OSArchitecture
        $results["bios_version"]    = $bios.SMBIOSBIOSVersion
        $results["uptime"]          = "{0}d {1}h {2}m" -f $uptime.Days, $uptime.Hours, $uptime.Minutes
        $results["uptime_seconds"]  = [math]::Round($uptime.TotalSeconds)
        $results["last_boot"]       = $os.LastBootUpTime.ToString("yyyy-MM-ddTHH:mm:ss")
        $results["timezone"]        = [System.TimeZoneInfo]::Local.Id
        $results["powershell_ver"]  = $PSVersionTable.PSVersion.ToString()

        # IP addresses (all non-loopback IPv4)
        $ips = (Get-NetIPAddress -AddressFamily IPv4 |
                Where-Object { $_.IPAddress -notmatch "^127\." } |
                Select-Object -ExpandProperty IPAddress) -join "|"
        $results["ip_addresses"] = $ips

        # Pending reboot check
        $rebootPending = (
            (Test-Path "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\WindowsUpdate\Auto Update\RebootRequired") -or
            (Test-Path "HKLM:\SYSTEM\CurrentControlSet\Control\Session Manager\PendingFileRenameOperations")
        )
        $results["reboot_pending"] = $rebootPending

    } catch {
        Write-Log "Identity collection failed: $_" "WARN"
        $results["identity_error"] = "$_"
    }
    return $results
}

function Get-SecurityMetrics {
    $results = @{}
    try {
        # Firewall profiles
        $fw = Get-NetFirewallProfile -ErrorAction SilentlyContinue
        foreach ($p in $fw) {
            $results["fw_$($p.Name.ToLower())_enabled"] = $p.Enabled
        }

        # Windows Defender status
        $def = Get-MpComputerStatus -ErrorAction SilentlyContinue
        if ($def) {
            $results["defender_enabled"]          = $def.AntivirusEnabled
            $results["defender_realtime"]         = $def.RealTimeProtectionEnabled
            $results["defender_sig_age_days"]     = $def.AntivirusSignatureAge
            $results["defender_last_scan"]        = $def.FullScanEndTime.ToString("yyyy-MM-dd")
            $results["defender_ok"]               = ($def.AntivirusEnabled -and $def.RealTimeProtectionEnabled)
        }

        # Failed logins in last hour
        $failedLogins = (Get-WinEvent -FilterHashtable @{
            LogName   = "Security"
            Id        = 4625
            StartTime = (Get-Date).AddHours(-1)
        } -ErrorAction SilentlyContinue | Measure-Object).Count
        $results["failed_logins_1h"] = $failedLogins

    } catch {
        Write-Log "Security metrics partially unavailable (may need elevation): $_" "WARN"
        $results["security_partial"] = $true
    }
    return $results
}

# ─────────────────────────────────────────────────────────────────────────────
#  MAIN EXECUTION
# ─────────────────────────────────────────────────────────────────────────────
Write-Log "=== Edge Monitor START ===" "INFO" @{ version="2.0"; dry_run=$DryRun }

# Signal check has started
Send-Ping -Suffix "/start" | Out-Null

$payload = [ordered]@{}
$checks  = [ordered]@{}
$allOk   = $true

# ── Collect all telemetry ────────────────────────────────────────────────────
$collectors = [ordered]@{
    "identity" = { Get-SystemIdentity       }
    "cpu"      = { Get-CpuMetrics           }
    "ram"      = { Get-RamMetrics           }
    "disk"     = { Get-DiskMetrics          }
    "network"  = { Get-NetworkMetrics       }
    "process"  = { Get-TopProcesses         }
    "services" = { Get-ServiceMetrics       }
    "ports"    = { Get-PortChecks           }
    "dns"      = { Get-DnsChecks            }
    "tls"      = { Get-TlsCertChecks        }
    "events"   = { Get-WindowsEventLogMetrics }
    "security" = { Get-SecurityMetrics      }
}

foreach ($name in $collectors.Keys) {
    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    try {
        $result = & $collectors[$name]
        $sw.Stop()
        Write-Log "Collected: $name" "DEBUG" @{ collector=$name; duration_ms=$sw.ElapsedMilliseconds }
        foreach ($k in $result.Keys) { $payload[$k] = $result[$k] }

        # Track ok status per collector
        $okKey = "${name}_ok"
        if ($result.ContainsKey($okKey) -and $result[$okKey] -eq $false) {
            $allOk = $false
            $checks[$name] = "FAIL"
        } else {
            $checks[$name] = "OK"
        }
    } catch {
        Write-Log "Collector [$name] threw: $_" "ERROR"
        $checks[$name] = "ERROR"
        $allOk = $false
    }
}

# ── Add run metadata ─────────────────────────────────────────────────────────
$elapsed = [math]::Round(((Get-Date) - $SCRIPT_START).TotalMilliseconds)
$payload["run_duration_ms"]  = $elapsed
$payload["run_timestamp"]    = (Get-Date -Format "yyyy-MM-ddTHH:mm:ss.fffZ")
$payload["run_status"]       = if ($allOk) { "ok" } else { "degraded" }
$payload["collector_status"] = ($checks.GetEnumerator() | ForEach-Object { "$($_.Key)=$($_.Value)" }) -join "|"

# ── Build body (key=value, Splunk-compatible) ────────────────────────────────
$bodyLines = foreach ($k in $payload.Keys) { "$k=$($payload[$k])" }
$body = $bodyLines -join "`n"

if ($JsonOnly) {
    $payload | ConvertTo-Json -Depth 5
    exit 0
}

Write-Log "Telemetry collected" "INFO" @{
    collectors = $collectors.Keys.Count
    fields     = $payload.Count
    status     = $payload["run_status"]
    duration_ms= $elapsed
}

# ── Emit Splunk-structured event to JSONL ────────────────────────────────────
$splunkEvent = @{
    time       = [math]::Floor((Get-Date -UFormat %s))
    host       = $env:COMPUTERNAME
    source     = "edge-monitor"
    sourcetype = "edge:healthcheck"
    event      = $payload
}
Add-Content -Path $CFG.JsonLogFile -Value ($splunkEvent | ConvertTo-Json -Depth 5 -Compress)

# ── Send ping ────────────────────────────────────────────────────────────────
if ($allOk) {
    $sent = Send-Ping -Body $body
    if ($sent) {
        Write-Log "=== Edge Monitor COMPLETE [OK] ===" "INFO" @{ duration_ms=$elapsed }
        exit 0
    } else {
        Write-Log "=== Edge Monitor COMPLETE [PING FAILED] ===" "ERROR"
        exit 2
    }
} else {
    $failedChecks = ($checks.GetEnumerator() | Where-Object { $_.Value -ne "OK" } |
                     ForEach-Object { $_.Key }) -join ","
    $failBody = "status=degraded failed_checks=$failedChecks`n$body"

    Write-Log "One or more checks FAILED — sending fail ping" "WARN" @{ failed=$failedChecks }
    Send-Ping -Suffix "/fail" -Body $failBody | Out-Null
    Write-Log "=== Edge Monitor COMPLETE [DEGRADED] ===" "WARN" @{ duration_ms=$elapsed }
    exit 1
}
