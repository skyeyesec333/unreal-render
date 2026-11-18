# Windows twin of measure_job.py: what does a job really need? System RAM (working set of the process and everything
# it started), GPU memory (nvidia-smi, whole card), by time. Run it on the PC, around the smallest real job:
#   powershell -ExecutionPolicy Bypass -File measure_job.ps1 -Label lm-test -Out budget.json -Exe "C:\...\UnrealEditor-Cmd.exe" -Args "<project> <map> -game ..."
# Writes budget.json (peaks and a suggested allowance: peak plus 15%) and a CSV of the samples beside it.
param([string]$Label = "job", [string]$Out = "budget.json", [Parameter(Mandatory = $true)][string]$Exe, [string]$Args = "", [int]$Every = 5)
function Tree([int]$root) {
  $all = Get-CimInstance Win32_Process | Select-Object ProcessId, ParentProcessId
  $ids = New-Object System.Collections.Generic.List[int]; $todo = New-Object System.Collections.Generic.Queue[int]; $todo.Enqueue($root)
  while ($todo.Count) { $p = $todo.Dequeue(); if ($ids.Contains($p)) { continue }; $ids.Add($p); $all | Where-Object { $_.ParentProcessId -eq $p } | ForEach-Object { $todo.Enqueue([int]$_.ProcessId) } }
  return $ids
}
$csv = [IO.Path]::ChangeExtension($Out, ".csv"); "seconds,ram_mib,gpu_all_mib,processes" | Set-Content $csv
$p = Start-Process -FilePath $Exe -ArgumentList $Args -PassThru; $t0 = Get-Date; $ram = 0; $gpu = 0; $ramAt = 0; $np = 0
while (-not $p.HasExited) {
  $ids = Tree $p.Id; $ws = 0
  foreach ($i in $ids) { $q = Get-Process -Id $i -ErrorAction SilentlyContinue; if ($q) { $ws += $q.WorkingSet64 } }
  $r = [int]($ws / 1MB); $g = 0; try { $g = [int](nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits | Select-Object -First 1) } catch {}
  $s = [int]((Get-Date) - $t0).TotalSeconds; "$s,$r,$g,$($ids.Count)" | Add-Content $csv
  if ($r -gt $ram) { $ram = $r; $ramAt = $s }; if ($g -gt $gpu) { $gpu = $g }; if ($ids.Count -gt $np) { $np = $ids.Count }
  Start-Sleep -Seconds $Every
}
$sum = [ordered]@{ label = $Label; command = "$Exe $Args"; exit_code = $p.ExitCode; seconds = [int]((Get-Date) - $t0).TotalSeconds; stopped_at_ram_cap = $false
  peak_ram_mib = $ram; peak_ram_at_seconds = $ramAt; peak_ram_phase = "whole run"; peak_gpu_job_mib = $null; peak_gpu_all_mib = $gpu; peak_processes = $np
  ask_for = [ordered]@{ ram_gib = [int][math]::Ceiling($ram * 1.15 / 1024); gpu_mib = [int]([math]::Ceiling($gpu * 1.15 / 256) * 256) }
  note = "ask_for is the peak plus 15%. GPU memory is the whole card's: subtract what was in use before the job." }
$sum | ConvertTo-Json | Set-Content $Out
"$Label : RAM peak $ram MiB at ${ramAt}s, GPU peak $gpu MiB (whole card), $np processes -> ask for $($sum.ask_for.ram_gib) GiB RAM, $($sum.ask_for.gpu_mib) MiB GPU memory ($Out)"
