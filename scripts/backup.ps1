$hdr=@{Authorization="Bearer $env:TOKEN"}
Invoke-RestMethod http://localhost:8001/admin/backup -Headers $hdr -OutFile ("backup_{0:yyyyMMdd_HHmmss}.json" -f (Get-Date))
