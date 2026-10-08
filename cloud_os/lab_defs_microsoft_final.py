from .lab_defs_common import cmd

LABS=[{
 "id":"M69-FINAL","module":"M9","number":"6–9 Final","title":"NovaCloud SOC Breach Investigation","topic":"Azure, Sentinel, KQL and Defender XDR correlation","difficulty":"Intermediate","estimated_minutes":40,
 "objective":"Investigate a synthetic NovaCloud breach across local Azure, SIEM, KQL and XDR simulators and reconstruct the complete attack chain.",
 "scenario":"A compromised developer account is used to access NovaCloud, gain privilege, execute a suspicious process, move laterally, access sensitive storage, and change network exposure. All telemetry and resources are fictional and local.",
 "theory":"Cross-domain investigations correlate identity, cloud control-plane, network, storage, SIEM and endpoint telemetry. This challenge runs entirely inside the Cloud OS lab sandbox.",
 "learn":["Correlate identity and endpoint evidence","Use KQL-style queries to validate findings","Build an incident timeline and remediation plan"],
 "topology":"203.0.113.45 -> Entra ID -> WS-001 -> WS-002 -> SERVER-01 -> FILESERVER-01 -> customer-records | Sentinel + KQL + XDR",
 "commands":[
  cmd("breach azure inspect","Azure simulator: failed logins, successful login, Global Administrator assignment, public NSG change, sensitive storage access."),
  cmd("breach sentinel inspect","Sentinel simulator: correlated alerts and incident INC-6900."),
  cmd("breach kql investigate","KQL engine: SigninLogs, AzureActivity, DeviceProcessEvents, CommonSecurityLog and StorageEvents correlated."),
  cmd("breach xdr inspect","XDR simulator: WS-001 suspicious execution, privilege escalation and lateral movement to FILESERVER-01."),
  cmd("breach finding user alice@novacloud.local","Initial compromised user recorded.","final-user"),
  cmd("breach finding source 203.0.113.45","Initial source documentation IP recorded.","final-source"),
  cmd("breach finding login 10:46","First suspicious successful login recorded.","final-login"),
  cmd("breach finding privilege Global-Administrator","Privilege escalation event recorded.","final-privilege"),
  cmd("breach finding device WS-001","Affected device recorded.","final-device"),
  cmd("breach finding process powershell.exe","Suspicious process recorded.","final-process"),
  cmd("breach finding movement WS-001 WS-002 SERVER-01 FILESERVER-01","Lateral movement path recorded.","final-movement"),
  cmd("breach finding resource customer-records","Sensitive resource recorded.","final-resource"),
  cmd("breach finding misconfiguration public-db-nsg","Exploited network misconfiguration recorded.","final-misconfig"),
  cmd("breach remediation least-privilege-mfa-network-storage-xdr","Remediation plan recorded: least privilege, MFA, network restriction, private storage, endpoint isolation and detection tuning.","final-remediation")
 ],
 "tasks":[
  {"id":"M69-FINAL-T1","title":"Identify compromised user","required":"final-user","points":10,"hint":"Correlate SigninLogs and incident entities.","failure":"Compromised user not identified."},
  {"id":"M69-FINAL-T2","title":"Identify source IP","required":"final-source","points":10,"hint":"Use the synthetic sign-in evidence.","failure":"Initial source IP not identified."},
  {"id":"M69-FINAL-T3","title":"Identify first suspicious login","required":"final-login","points":10,"hint":"Build the authentication timeline.","failure":"First suspicious login not identified."},
  {"id":"M69-FINAL-T4","title":"Identify privilege escalation","required":"final-privilege","points":10,"hint":"Inspect AzureActivity and XDR privilege telemetry.","failure":"Privilege escalation not identified."},
  {"id":"M69-FINAL-T5","title":"Identify affected device","required":"final-device","points":10,"hint":"Inspect endpoint alerts and process telemetry.","failure":"Affected device not identified."},
  {"id":"M69-FINAL-T6","title":"Identify suspicious process","required":"final-process","points":10,"hint":"Inspect the XDR process tree.","failure":"Suspicious process not identified."},
  {"id":"M69-FINAL-T7","title":"Reconstruct lateral movement","required":"final-movement","points":10,"hint":"Correlate remote logon and service events.","failure":"Lateral movement path not reconstructed."},
  {"id":"M69-FINAL-T8","title":"Identify sensitive resource","required":"final-resource","points":10,"hint":"Inspect storage telemetry.","failure":"Sensitive resource not identified."},
  {"id":"M69-FINAL-T9","title":"Identify exploited misconfiguration","required":"final-misconfig","points":10,"hint":"Inspect NSG and public-access changes.","failure":"Exploited misconfiguration not identified."},
  {"id":"M69-FINAL-T10","title":"Recommend remediation","required":"final-remediation","points":10,"hint":"Cover identity, network, storage and endpoint controls.","failure":"Remediation plan not completed."}
 ],
 "hints":["Start with identity events, then pivot to endpoint and cloud activity.","Use the same timestamp window across all simulators."],
 "common_mistakes":["Treating each alert in isolation","Skipping timeline correlation","Using real infrastructure instead of the lab sandbox"],
 "security_explanation":"The challenge uses only local synthetic state. It cannot modify Azure, Microsoft accounts, Defender, host firewall, real users, routes, registry, services or Cloud OS production data.",
 "aws_mapping":["Cross-platform cloud-security concepts only; this challenge uses Microsoft terminology inside a local simulator."]
}]
