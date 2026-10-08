from .lab_defs_common import lab,challenge,cmd

LABS=[
 lab("M8",1,"KQL Fundamentals","KQL fundamentals","Practice table selection, pipeline syntax, take, and project against bundled synthetic security tables.","Local KQL Training Engine includes SigninLogs, AzureActivity, SecurityAlert, SecurityIncident, DeviceEvents, DeviceProcessEvents, DeviceNetworkEvents, CommonSecurityLog, and StorageEvents.",[
  cmd("SigninLogs | take 10","10 synthetic sign-in rows returned.","kql-take"),
  cmd("SigninLogs | project TimeGenerated, UserPrincipalName, IPAddress","Projected columns returned for synthetic sign-in records.","kql-project")],"Beginner–Intermediate"),
 lab("M8",2,"Filtering & Searching","KQL filtering and search","Use where clauses to find failed sign-ins, a specific user, a specific IP, and recent events.","SigninLogs contains fictional users and documentation-range source IPs.",[
  cmd("SigninLogs | where ResultType != 0","12 failed sign-ins returned.","failed-signins-query"),
  cmd("SigninLogs | where UserPrincipalName == alice@novacloud.local","31 records for alice@novacloud.local.","user-filter-query"),
  cmd("SigninLogs | where IPAddress == 203.0.113.45","9 records for 203.0.113.45.","ip-filter-query"),
  cmd("SigninLogs | where TimeGenerated > ago(1h)","24 events from the previous simulated hour.","recent-query")],"Intermediate"),
 lab("M8",3,"Sorting","KQL sorting","Sort synthetic authentication events to identify the latest suspicious activity.","The local dataset spans a deterministic simulated timeline.",[
  cmd("SigninLogs | sort by TimeGenerated desc","Latest events sorted descending.","sort-desc"),
  cmd("SecurityAlert | order by TimeGenerated desc","Latest alerts sorted descending.","alert-sort")],"Intermediate"),
 lab("M8",4,"Aggregation","KQL summarize and aggregation","Aggregate failed sign-ins, source IPs, and alert severity using summarize.","Synthetic security tables contain repeated users, IPs, and severity values.",[
  cmd("SigninLogs | summarize FailedAttempts=count() by UserPrincipalName","alice@novacloud.local 7\nbob@novacloud.local 3\nanalyst@novacloud.local 2","failed-users-summary"),
  cmd("SigninLogs | summarize Attempts=count() by IPAddress","203.0.113.45 9\n198.51.100.22 5\n192.0.2.18 4","source-ip-summary"),
  cmd("SecurityAlert | summarize Alerts=count() by Severity","Low 2\nMedium 3\nHigh 2\nCritical 1","severity-summary")],"Intermediate"),
 lab("M8",5,"Advanced Security Queries","KQL security detections","Use multi-stage local queries to identify password spraying, port scanning, suspicious process execution, and privilege escalation.","Bundled tables contain a synthetic attack chain only; no real system is queried.",[
  cmd("SigninLogs | where ResultType != 0 | summarize Failures=count() by IPAddress","203.0.113.45 has 7 failures across 4 users.","password-spray-query"),
  cmd("CommonSecurityLog | where Action == Deny | summarize Ports=dcount(DestinationPort) by SourceIP","198.51.100.77 touched 18 destination ports.","port-scan-query"),
  cmd("DeviceProcessEvents | where FileName == powershell.exe | project DeviceName, AccountName, ProcessCommandLine","WS-001 alice powershell.exe -EncodedCommand [synthetic-redacted]","suspicious-process-query"),
  cmd("AzureActivity | where OperationName contains role | project TimeGenerated, Caller, OperationName","alice@novacloud.local Add role assignment","privilege-query")],"Intermediate"),
 lab("M8",6,"Log Investigation","KQL log investigation","Use only KQL-style queries to reconstruct a compromised-account timeline.","A large synthetic dataset contains failed authentication, success, privilege change, and sensitive storage access.",[
  cmd("SigninLogs | where IPAddress == 203.0.113.45 | sort by TimeGenerated asc","10:42 failed alice\n10:43 failed alice\n10:46 success alice","timeline-auth"),
  cmd("AzureActivity | where Caller == alice@novacloud.local","10:51 Add role assignment Global Administrator","timeline-role"),
  cmd("StorageEvents | where UserPrincipalName == alice@novacloud.local","11:02 Read customer-records/finance-q4.csv","timeline-storage"),
  cmd("DeviceEvents | where AccountName == alice | sort by TimeGenerated asc","10:49 suspicious session token use on WS-001","timeline-device"),
  cmd("SecurityIncident | where Title contains compromised","INC-2407 Compromised developer account","timeline-complete")],"Intermediate"),
 challenge("M8","KQL Threat Hunt","Discover an unknown synthetic attack sequence using only the local KQL Training Engine.",[
  cmd("SecurityAlert | summarize count() by Severity","Alert distribution reviewed.","hunt-alerts"),
  cmd("SigninLogs | where ResultType != 0 | summarize count() by IPAddress","Suspicious source isolated.","hunt-source"),
  cmd("DeviceProcessEvents | where FileName == powershell.exe","Suspicious process chain isolated.","hunt-process"),
  cmd("AzureActivity | where OperationName contains role","Privilege change isolated.","hunt-role"),
  cmd("StorageEvents | where Operation contains Read","Sensitive access isolated.","hunt-resource")
 ])
]
