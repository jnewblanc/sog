# Powershell script to tail a logfile

$logfile = "..\.logs\$($args[0])"

Write-Output $logfile

If (test-Path $logfile) {
  Get-Content $logfile -Tail 100 -Wait
}
