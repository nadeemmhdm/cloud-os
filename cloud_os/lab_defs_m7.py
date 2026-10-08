from .lab_defs_common import lab,challenge,cmd

LABS=[
 lab("M7",1,"SIEM Fundamentals","SIEM fundamentals","Practice collection, normalization, search, correlation, alerts, and incidents using local synthetic logs.","Identity, firewall, server, endpoint, and storage sources feed the local MiniSIEM.",[
  cmd("siem sources","identity 120\nfirewall 180\nserver 90\nendpoint 160\nstorage 70","sources-reviewed"),
  cmd("siem events","620 normalized synthetic events loaded."),cmd("siem stats","620 events | 5 sources | 8 alerts | 2 incidents","siem-stats-reviewed")],"Beginner–Intermediate"),
 lab("M7",2,"Sentinel Workspace Simulation","Microsoft Sentinel workspace concepts","Enable a disabled connector and validate log ingestion in the local Sentinel simulator.","Workspace NovaCloud-SOC has EntraID, AzureActivity, Firewall, Endpoint, and Storage connectors.",[
  cmd("sentinel workspace","NovaCloud-SOC | status=healthy | local-simulator=true"),
  cmd("sentinel connectors","EntraID enabled\nAzureActivity enabled\nFirewall disabled\nEndpoint enabled\nStorage enabled","connectors-reviewed"),
  cmd("sentinel connector enable Firewall","Firewall connector enabled in simulated workspace.","firewall-connector-enabled"),
  cmd("sentinel ingestion-status","All 5 connectors ingesting. Firewall received 180 events.","ingestion-verified")],"Intermediate"),
 lab("M7",3,"Log Ingestion","Sentinel log ingestion","Map bundled source files to the correct SIEM tables and validate record counts.","signin.json, firewall.json, endpoint.json, and storage.json are bundled synthetic datasets.",[
  cmd("siem ingest map signin.json SigninLogs","signin.json mapped to SigninLogs: 120 records.","signin-mapped"),
  cmd("siem ingest map firewall.json CommonSecurityLog","firewall.json mapped to CommonSecurityLog: 180 records.","firewall-mapped"),
  cmd("siem ingest map endpoint.json DeviceEvents","endpoint.json mapped to DeviceEvents: 160 records.","endpoint-mapped"),
  cmd("siem ingest map storage.json StorageEvents","storage.json mapped to StorageEvents: 70 records.","storage-mapped"),
  cmd("siem ingestion validate","Validation PASS: 530 mapped records, 0 rejected.","ingestion-counts-verified")],"Intermediate"),
 lab("M7",4,"Detection Rules","Sentinel analytics and detection rules","Enable detection rules and generate matching alerts from synthetic events.","The rule builder contains disabled analytics for failed logins, role grants, storage exposure, port scans, and suspicious PowerShell telemetry.",[
  cmd("sentinel rules","R1 Repeated failed logins disabled\nR2 Administrative role granted disabled\nR3 Public storage enabled disabled\nR4 Port scanning disabled\nR5 Suspicious PowerShell execution disabled"),
  cmd("sentinel rule enable R1","R1 enabled.","rule-r1-enabled"),cmd("sentinel rule enable R4","R4 enabled.","rule-r4-enabled"),
  cmd("sentinel rule test","Generated ALERT-101 Repeated failed logins and ALERT-104 Port scanning.","detection-alerts-generated")],"Intermediate"),
 lab("M7",5,"Security Alerts","Sentinel alert triage","Triage synthetic alerts, classify true/false positives, and assign severity.","The alert queue contains Low, Medium, High, and Critical simulated findings.",[
  cmd("sentinel alerts","A-10 Low backup-test\nA-11 Medium unusual-login\nA-12 High port-scan\nA-13 Critical admin-role-after-login"),
  cmd("sentinel alert classify A-10 false-positive","A-10 classified false positive.","false-positive-classified"),
  cmd("sentinel alert classify A-13 true-positive","A-13 classified true positive.","true-positive-classified"),
  cmd("sentinel alert severity A-13 critical","A-13 severity set to Critical.","severity-assigned")],"Intermediate"),
 lab("M7",6,"Incident Investigation","Sentinel incident investigation","Reconstruct incident INC-2407 from authentication, role, resource, and alert evidence.","Repeated failures are followed by a successful login, privilege assignment, and sensitive file access.",[
  cmd("sentinel incident show INC-2407","Timeline: failures -> success -> role grant -> sensitive file access\nEntities: alice@novacloud.local, 203.0.113.45, WS-001, customer-records"),
  cmd("sentinel incident finding target alice","Target account identified: alice@novacloud.local.","incident-target-found"),
  cmd("sentinel incident finding source 203.0.113.45","Source documentation IP identified.","incident-source-found"),
  cmd("sentinel incident finding privilege Global-Administrator","Privilege change identified.","incident-privilege-found"),
  cmd("sentinel incident finding resource customer-records","Affected sensitive resource identified.","incident-resource-found")],"Intermediate"),
 challenge("M7","SOC Analyst Investigation","Investigate a multi-stage local SIEM incident and close it with correct findings.",[
  cmd("soc challenge inspect","Incident SOC-900: identity + firewall + endpoint + storage evidence correlated."),
  cmd("soc challenge identify user","Compromised user identified.","soc-user"),cmd("soc challenge identify source","Source IP identified.","soc-source"),
  cmd("soc challenge identify device","Affected device identified.","soc-device"),cmd("soc challenge identify resource","Sensitive resource identified.","soc-resource"),
  cmd("soc challenge close confirmed","Incident closed as confirmed compromise with remediation notes.","soc-closed")
 ])
]
