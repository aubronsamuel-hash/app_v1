param([string]$File,[switch]$NoWipe)
$hdr=@{Authorization="Bearer $env:TOKEN"}
$body=Get-Content $File -Raw
$wipe = $NoWipe.IsPresent ? "false" : "true"
Invoke-RestMethod "http://localhost:8001/admin/restore?wipe=$wipe" -Method Post -Headers $hdr -Body $body -ContentType "application/json"
