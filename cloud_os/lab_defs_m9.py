from .lab_defs_common import lab,challenge,cmd

LABS=[
 lab("M9",1,"XDR Fundamentals","Microsoft Defender XDR fundamentals","Inspect synthetic devices, users, alerts, incidents, and timeline data in the local Defender XDR Simulator.","NovaCloud endpoint telemetry is fully synthetic and local.",[
  cmd("xdr devices","WS-001\nWS-002\nSERVER-01\nFILESERVER-01","xdr-devices-reviewed"),
  cmd("xdr alerts","XDR-A101 High suspicious script WS-001\nXDR-A102 Medium abnormal login WS-002\nXDR-A103 High network connection SERVER-01","xdr-alerts-reviewed"),
  cmd("xdr incidents","XDR-INC-01 Open Multi-stage endpoint incident","xdr-incidents-reviewed"),
  cmd("xdr timeline","10:46 login alice@WS-001\n10:49 powershell.exe\n10:51 privilege change\n10:58 remote logon WS-002","xdr-timeline-reviewed")],"Beginner–Intermediate"),
 lab("M9",2,"Threat Detection","Defender XDR threat detection","Triage synthetic file, script, login, and network alerts and identify affected entities.","No malicious payload is executed; the lab uses generated telemetry only.",[
  cmd("xdr alert show XDR-A101","High | suspicious-script.ps1 | device=WS-001 | user=alice","xdr-alert-inspected"),
  cmd("xdr finding device WS-001","Affected device recorded: WS-001.","xdr-device-found"),
  cmd("xdr finding user alice","Affected user recorded: alice.","xdr-user-found"),
  cmd("xdr triage XDR-A101 true-positive","XDR-A101 classified as true positive.","xdr-alert-triaged")],"Intermediate"),
 lab("M9",3,"Execution","Execution telemetry analysis","Analyze a synthetic process tree and identify suspicious execution without running code.","Process telemetry shows explorer.exe -> powershell.exe -> suspicious-script.ps1.",[
  cmd("xdr process-tree WS-001","explorer.exe\n  -> powershell.exe\n       -> suspicious-script.ps1","process-tree-reviewed"),
  cmd("xdr process show powershell.exe","Parent=explorer.exe Child=suspicious-script.ps1 Account=alice CommandLine=[synthetic-redacted]","powershell-reviewed"),
  cmd("xdr finding execution suspicious-script.ps1","Suspicious execution identified.","execution-found")],"Intermediate"),
 lab("M9",4,"Defense Evasion","Defense evasion telemetry","Identify synthetic security-tool disablement, log clearing, hidden process, and encoded-command behavior.","All events are generated simulator records; no host security controls are changed.",[
  cmd("xdr evasion events","SecurityToolDisabled WS-001\nLogClearAttempt WS-001\nHiddenProcess WS-001\nEncodedCommand WS-001","evasion-events-reviewed"),
  cmd("xdr finding evasion SecurityToolDisabled","Defense-evasion finding recorded.","evasion-tool-disable-found"),
  cmd("xdr finding evasion LogClearAttempt","Defense-evasion finding recorded.","evasion-logclear-found"),
  cmd("xdr finding evasion EncodedCommand","Defense-evasion finding recorded.","evasion-encoded-found")],"Intermediate"),
 lab("M9",5,"Credential Access","Credential access telemetry","Investigate synthetic credential-access indicators without dumping credentials or touching the host.","Telemetry represents LSASS access attempt, browser credential access, token theft behavior, and password-store access.",[
  cmd("xdr credential events","LSASSAccessAttempt WS-001\nBrowserCredentialAccess WS-001\nTokenTheftBehavior WS-001\nPasswordStoreAccess WS-001","credential-events-reviewed"),
  cmd("xdr finding credential LSASSAccessAttempt","Credential-access behavior identified.","lsass-attempt-found"),
  cmd("xdr finding credential TokenTheftBehavior","Token-theft behavior identified.","token-theft-found"),
  cmd("xdr finding credential PasswordStoreAccess","Password-store access behavior identified.","password-store-found")],"Intermediate"),
 lab("M9",6,"Privilege Escalation","Privilege escalation telemetry","Reconstruct a simulated transition from standard user to local administrator and privileged process execution.","Synthetic events record a group membership change followed by privileged execution.",[
  cmd("xdr privilege timeline","10:51 alice added to local Administrators on WS-001\n10:52 elevated powershell.exe started","privilege-timeline-reviewed"),
  cmd("xdr finding initial-user alice","Initial user identified.","privilege-user-found"),
  cmd("xdr finding change Administrators","Privilege change identified.","privilege-change-found"),
  cmd("xdr finding process powershell.exe","Responsible privileged process identified.","privilege-process-found")],"Intermediate"),
 lab("M9",7,"Lateral Movement","Lateral movement telemetry","Identify the simulated lateral-movement path across NovaCloud endpoints and servers.","WS-001 -> WS-002 -> SERVER-01 -> FILESERVER-01 contains remote logon, admin-share, remote-process, and service-creation telemetry.",[
  cmd("xdr movement topology","WS-001 -> WS-002 -> SERVER-01 -> FILESERVER-01","movement-topology-reviewed"),
  cmd("xdr movement events","RemoteLogon WS-001->WS-002\nAdminShareAccess WS-002->SERVER-01\nRemoteProcess SERVER-01\nServiceCreation FILESERVER-01","movement-events-reviewed"),
  cmd("xdr finding path WS-001 WS-002 SERVER-01 FILESERVER-01","Lateral movement path recorded.","movement-path-found")],"Intermediate"),
 challenge("M9","Defender XDR Full Incident Investigation","Reconstruct a complete synthetic attack chain from execution through defense evasion, credential access, privilege escalation, and lateral movement.",[
  cmd("xdr challenge inspect","Synthetic incident stages: execution -> defense evasion -> credential access -> privilege escalation -> lateral movement."),
  cmd("xdr challenge identify execution","Execution stage identified.","xdr-chain-execution"),
  cmd("xdr challenge identify evasion","Defense evasion stage identified.","xdr-chain-evasion"),
  cmd("xdr challenge identify credential","Credential access stage identified.","xdr-chain-credential"),
  cmd("xdr challenge identify privilege","Privilege escalation stage identified.","xdr-chain-privilege"),
  cmd("xdr challenge identify movement","Lateral movement stage identified.","xdr-chain-movement")
 ])
]
