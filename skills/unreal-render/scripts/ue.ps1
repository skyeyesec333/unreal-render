# ue.ps1: runs on the Windows render PC. Runs one Python script in the Unreal project headless, or renders a level
# sequence with Movie Render Queue offscreen, with a log, a timeout and a report. Never overwrites, never deletes.
#
#   powershell -NoProfile -ExecutionPolicy Bypass -File <work>\scripts\ue.ps1 -Mode check
#   ... -Mode script -Script build_city.py [-ArgsFile <work>\args\x.json] [-TimeoutMin 90] [-Detach]
#   ... -Mode render -Map /Game/MyRenders/Maps/City_1118_0930 -Sequence /Game/MyRenders/Seq/Shot_1118_0930 `
#       -Config /Game/MyRenders/Seq/Cfg_1118_0930 [-ResX 1920 -ResY 1080] [-TimeoutMin 240] [-Detach]
#   ... -Mode status          (is a job running; last log lines and report)
#   ... -Mode renders         (prints the renders root, for fetching)
#
# Reads ue.json in the work folder (one level above this script):
#   { "engine": "C:/Program Files/Epic Games/UE_5.x", "project": "D:/Unreal/MyProject/MyProject.uproject",
#     "renders": "D:/Unreal/Renders" }
# Every name that reaches a command line is checked against a pattern first; nothing is passed through
# Invoke-Expression. Scripts run only from <work>\scripts, argument files only from <work>\args.
param(
  [ValidateSet("check", "script", "render", "status", "renders")][string]$Mode = "check",
  [string]$Script = "", [string]$ArgsFile = "",
  [string]$Map = "", [string]$Sequence = "", [string]$Config = "",
  [int]$ResX = 1920, [int]$ResY = 1080, [int]$TimeoutMin = 0, [switch]$Detach, [string]$TaskName = ""
)
$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"
function Fail($msg) { Write-Output "FAIL  $msg"; exit 2 }
if ($TaskName -and $TaskName -notmatch '^ue-render-\d{4}_\d{6}$') { Fail "bad task name" }

$Work = Split-Path -Parent $PSScriptRoot
$Lib = Join-Path $PSScriptRoot "ue"
$cfgPath = Join-Path $Work "ue.json"
if (-not (Test-Path -LiteralPath $cfgPath)) { Fail "no ue.json in $Work (see references/setup.md)" }
$cfg = Get-Content -LiteralPath $cfgPath -Raw | ConvertFrom-Json
foreach ($k in "engine", "project", "renders") { if (-not $cfg.$k) { Fail "ue.json has no '$k'" } }
$Engine = [string]$cfg.engine; $Project = [string]$cfg.project; $Renders = [string]$cfg.renders
$Cmd = Join-Path $Engine "Engine\Binaries\Win64\UnrealEditor-Cmd.exe"
$Logs = Join-Path $Work "logs"
New-Item -ItemType Directory -Force -Path $Logs | Out-Null
$Stamp = Get-Date -Format "MMdd_HHmmss"

# An asset path inside the project: /Game/... letters, digits, _ - . only (no spaces, quotes or shell characters).
$AssetRe = '^/Game(/[A-Za-z0-9_][A-Za-z0-9_.\-]*)+$'

function Report-Run($proc, $log, $report, $timeoutMin) {
  if ($timeoutMin -gt 0) {
    if (-not $proc.WaitForExit($timeoutMin * 60 * 1000)) {
      # the whole tree: UnrealEditor-Cmd starts ShaderCompileWorker children that Stop-Process would leave running
      & taskkill.exe /T /F /PID $proc.Id 2>&1 | Out-Null
      Write-Output "FAIL  timed out after $timeoutMin min; stopped it and its child processes (log: $log)"; exit 3
    }
  } else { $proc.WaitForExit() }
  $code = $proc.ExitCode
  if (Test-Path -LiteralPath $report) { Get-Content -LiteralPath $report | ForEach-Object { "      $_" } }
  $errs = @(Select-String -LiteralPath $log -Pattern "LogPython: Error|Traceback|Error: " -ErrorAction SilentlyContinue | Select-Object -First 8)
  foreach ($e in $errs) { Write-Output ("ERR   " + $e.Line.Trim()) }
  if ($code -ne 0 -or $errs.Count -gt 0) { Write-Output "FAIL  exit $code (log: $log)"; exit 1 }
  Write-Output "OK    exit 0 (log: $log)"
}

# One Unreal at a time: a headless job, or the editor open on the project, both hold the project's files.
function Assert-Free {
  $busy = @(Get-Process UnrealEditor-Cmd, UnrealEditor -ErrorAction SilentlyContinue)
  if ($busy.Count) { Fail ("Unreal is already running here ({0}): wait for the job (Mode status), or close the editor" -f (($busy | ForEach-Object { $_.ProcessName }) -join ", ")) }
}

# -Detach: processes started inside an SSH session end with it, so a long run is handed to a one-off scheduled task
# that runs this same script (without -Detach) as the signed-in user and writes its output to <logs>\<task>.txt;
# the next call to this script removes the finished task. The user must be signed in at the PC (Interactive logon); no password is stored.
function Start-Detached([string[]]$passArgs) {
  $name = "ue-render-$Stamp"
  $out = Join-Path $Logs "$name.txt"
  $argLine = "-NoProfile -NonInteractive -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$PSCommandPath`" " + ($passArgs -join " ") + " -TaskName $name"
  $act = New-ScheduledTaskAction -Execute "powershell.exe" -Argument $argLine -WorkingDirectory $Work
  $who = [Security.Principal.WindowsIdentity]::GetCurrent().Name
  $pr = New-ScheduledTaskPrincipal -UserId $who -LogonType Interactive -RunLevel Limited
  $set = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit (New-TimeSpan -Hours 24)
  Register-ScheduledTask -TaskName $name -Action $act -Principal $pr -Settings $set | Out-Null
  Start-ScheduledTask -TaskName $name
  Start-Sleep -Seconds 4
  $t = Get-ScheduledTask -TaskName $name -ErrorAction SilentlyContinue
  if ($t -and $t.State -ne "Running" -and -not (Test-Path -LiteralPath $out)) {
    $res = ($t | Get-ScheduledTaskInfo).LastTaskResult
    Unregister-ScheduledTask -TaskName $name -Confirm:$false
    Fail "the detached run did not start (task result $res). Is $who signed in at the PC? Run without --detach, or sign in."
  }
  Write-Output "STARTED task $name as $who; its output goes to $out (Mode status shows progress)"
  exit 0
}

# A task cannot remove itself while it runs, so finished one-off tasks from earlier detached runs are removed here,
# from outside, by the next call. Only this script's own tasks match (ue-render-MMdd_HHmmss).
if (-not $TaskName) {
  Get-ScheduledTask -TaskName "ue-render-*" -ErrorAction SilentlyContinue |
    Where-Object { $_.TaskName -match '^ue-render-\d{4}_\d{6}$' -and $_.State -ne "Running" } |
    ForEach-Object { Unregister-ScheduledTask -TaskName $_.TaskName -Confirm:$false -ErrorAction SilentlyContinue }
}
if ($TaskName) { Start-Transcript -LiteralPath (Join-Path $Logs "$TaskName.txt") | Out-Null }
try {
switch ($Mode) {
  "check" {
    # read-only: what this PC has for Unreal work
    if (Test-Path -LiteralPath $Cmd) { Write-Output "ok    engine $Cmd" } else { Write-Output "FAIL  no UnrealEditor-Cmd.exe under $Engine" }
    $bv = Join-Path $Engine "Engine\Build\Build.version"
    if (Test-Path -LiteralPath $bv) { $v = Get-Content -LiteralPath $bv -Raw | ConvertFrom-Json; Write-Output ("ok    Unreal {0}.{1}.{2}" -f $v.MajorVersion, $v.MinorVersion, $v.PatchVersion) }
    if (Test-Path -LiteralPath $Project) { Write-Output "ok    project $Project" } else { Write-Output "FAIL  project not found: $Project" }
    if (Test-Path -LiteralPath $Project) {
      $up = Get-Content -LiteralPath $Project -Raw | ConvertFrom-Json
      foreach ($p in "PythonScriptPlugin", "MovieRenderPipeline", "EditorScriptingUtilities") {
        $on = @($up.Plugins | Where-Object { $_.Name -eq $p -and $_.Enabled }).Count -gt 0
        if ($on) { Write-Output "ok    plugin $p enabled in the project" } else { Write-Output "WARN  plugin $p not enabled in the .uproject (enable it once in the editor: Edit > Plugins)" }
      }
      $ini = Join-Path (Split-Path -Parent $Project) "Config\DefaultEngine.ini"
      if ((Test-Path -LiteralPath $ini) -and (Select-String -LiteralPath $ini -SimpleMatch "ExtendDefaultLuminanceRange=True" -Quiet)) { Write-Output "ok    exposure in EV (ExtendDefaultLuminanceRange)" }
      else { Write-Output "WARN  DefaultEngine.ini lacks r.DefaultFeature.AutoExposure.ExtendDefaultLuminanceRange=True: exposure numbers are luminance, not EV" }
    }
    $g = (& nvidia-smi --query-gpu=name,memory.total,memory.free,driver_version --format=csv,noheader 2>$null) | Select-Object -First 1
    if ($g) { Write-Output "ok    GPU $g" } else { Write-Output "FAIL  nvidia-smi did not answer" }
    Get-PSDrive -PSProvider FileSystem | Where-Object { $_.Free } | ForEach-Object { Write-Output ("info  drive {0}: {1} GB free" -f $_.Name, [int]($_.Free / 1GB)) }
    $busy = @(Get-Process UnrealEditor-Cmd, UnrealEditor -ErrorAction SilentlyContinue)
    if ($busy.Count) { Write-Output ("WAIT  Unreal is running ({0} process(es)): one job at a time" -f $busy.Count) } else { Write-Output "ok    no Unreal process running" }
    if (Test-Path -LiteralPath $Renders) { Write-Output "ok    renders folder $Renders" } else { Write-Output "WARN  renders folder missing: $Renders (created on first render)" }
  }

  "script" {
    if ($Script -notmatch '^[A-Za-z0-9_\-]+\.py$') { Fail "script name: letters, digits, _ - and .py only, inside $PSScriptRoot" }
    $sp = Join-Path $PSScriptRoot $Script
    if (-not (Test-Path -LiteralPath $sp)) { Fail "no such script: $sp (push it first)" }
    $ap = ""
    if ($ArgsFile) {
      $full = [System.IO.Path]::GetFullPath($ArgsFile); $argsDir = [System.IO.Path]::GetFullPath((Join-Path $Work "args")) + "\"
      if (-not $full.StartsWith($argsDir, [System.StringComparison]::OrdinalIgnoreCase)) { Fail "argument files must be in $argsDir" }
      if (-not (Test-Path -LiteralPath $full)) { Fail "no such argument file: $full" }
      $ap = $full
    }
    Assert-Free
    if ($Detach) {
      $pass = @("-Mode", "script", "-Script", $Script, "-TimeoutMin", $TimeoutMin)
      if ($ap) { $pass += @("-ArgsFile", "`"$ap`"") }
      Start-Detached $pass
    }
    $name = [System.IO.Path]::GetFileNameWithoutExtension($Script)
    $log = Join-Path $Logs "$Stamp-$name.log"; $report = Join-Path $Logs "$Stamp-$name.report.txt"
    # the script finds the helpers, its arguments and where to write its report through these
    $env:UE_RENDER_LIB = $Lib; $env:UE_RENDER_ARGS = $ap; $env:UE_RENDER_REPORT = $report; $env:UE_RENDER_RENDERS = $Renders
    $argv = @("`"$Project`"", "-run=pythonscript", "`"-script=$sp`"", "-unattended", "-nosplash", "-nullrhi", "-stdout", "-FullStdOutLogOutput")
    $p = Start-Process -FilePath $Cmd -ArgumentList $argv -RedirectStandardOutput $log -RedirectStandardError "$log.err" -WindowStyle Hidden -PassThru
    $p.Id | Set-Content -LiteralPath (Join-Path $Logs "current.pid")
    Report-Run $p $log $report $TimeoutMin
  }

  "render" {
    foreach ($pair in @(@("Map", $Map), @("Sequence", $Sequence), @("Config", $Config))) {
      if ($pair[1] -notmatch $AssetRe) { Fail ("{0} must be an asset path like /Game/Folder/Name (got '{1}')" -f $pair[0], $pair[1]) }
    }
    if ($ResX -lt 64 -or $ResX -gt 8192 -or $ResY -lt 64 -or $ResY -gt 8192) { Fail "resolution out of range" }
    Assert-Free
    if ($Detach) { Start-Detached @("-Mode", "render", "-Map", $Map, "-Sequence", $Sequence, "-Config", $Config, "-ResX", $ResX, "-ResY", $ResY, "-TimeoutMin", $TimeoutMin) }
    New-Item -ItemType Directory -Force -Path $Renders | Out-Null
    $leaf = ($Sequence -split "/")[-1] -replace '\..*$', ''
    $log = Join-Path $Logs "$Stamp-render-$leaf.log"; $report = Join-Path $Logs "$Stamp-render-$leaf.report.txt"
    $argv = @("`"$Project`"", $Map, "-game", "-LevelSequence=$Sequence", "-MoviePipelineConfig=$Config", "-RenderOffscreen",
              "-windowed", "-resx=$ResX", "-resy=$ResY", "-unattended", "-nosplash", "-NoLoadingScreen", "-log", "-stdout", "-FullStdOutLogOutput")
    $p = Start-Process -FilePath $Cmd -ArgumentList $argv -RedirectStandardOutput $log -RedirectStandardError "$log.err" -WindowStyle Hidden -PassThru
    $p.Id | Set-Content -LiteralPath (Join-Path $Logs "current.pid")
    Report-Run $p $log $report $TimeoutMin
  }

  "renders" { Write-Output "renders $Renders" }

  "status" {
    $procs = @(Get-Process UnrealEditor-Cmd -ErrorAction SilentlyContinue)
    if ($procs.Count) { $procs | ForEach-Object { Write-Output ("RUNNING pid {0}, started {1}, {2:N0} MB" -f $_.Id, $_.StartTime, ($_.WorkingSet64 / 1MB)) } }
    else { Write-Output "IDLE  no Unreal job running" }
    Get-ScheduledTask -TaskName "ue-render-*" -ErrorAction SilentlyContinue | ForEach-Object { Write-Output ("TASK  {0} {1}" -f $_.TaskName, $_.State) }
    $last = Get-ChildItem -LiteralPath $Logs -Filter "*.log" -ErrorAction SilentlyContinue | Sort-Object LastWriteTime | Select-Object -Last 1
    if ($last) { Write-Output "log   $($last.FullName)"; Get-Content -LiteralPath $last.FullName -Tail 12 | ForEach-Object { "      $_" } }
    $rep = Get-ChildItem -LiteralPath $Logs -Filter "*.report.txt" -ErrorAction SilentlyContinue | Sort-Object LastWriteTime | Select-Object -Last 1
    if ($rep) { Write-Output "report $($rep.FullName)"; Get-Content -LiteralPath $rep.FullName | ForEach-Object { "      $_" } }
  }
}
} finally {
  # a detached run closes its transcript however it ends; the next call removes its finished task
  if ($TaskName) { Stop-Transcript | Out-Null }
}
