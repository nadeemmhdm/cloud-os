from copy import deepcopy

MODULES=[
 {"id":"M1","name":"Cloud Security Fundamentals","description":"Cloud models, shared responsibility, IAM, networking, storage, and baseline security tooling.","difficulty":"Beginner"},
 {"id":"M2","name":"Identity & Access Security","description":"Users, groups, policies, least privilege, sandbox access keys, and IAM auditing.","difficulty":"Beginner–Intermediate"},
 {"id":"M3","name":"Network Security","description":"Virtual networks, security groups, ACLs, exposure analysis, and synthetic network monitoring.","difficulty":"Intermediate"},
 {"id":"M4","name":"Compute Security","description":"Instance hardening, ports, patching, metadata protection, containers, and compute baselines.","difficulty":"Intermediate"},
 {"id":"M5","name":"Storage & Data Security","description":"Object storage, public access, permissions, encryption, classification, snapshots, and recovery.","difficulty":"Intermediate"},
 {"id":"M6","name":"Microsoft Azure Security","description":"Local Azure Security Lab Simulator covering Entra ID, Azure RBAC, networking, storage, compute, and monitoring.","difficulty":"Intermediate"},
 {"id":"M7","name":"Microsoft Sentinel & SIEM","description":"Local Sentinel SIEM Simulator covering ingestion, connectors, detections, alerts, and incident investigation.","difficulty":"Intermediate"},
 {"id":"M8","name":"KQL for Security Analysis","description":"Offline KQL Training Engine for filtering, sorting, aggregation, threat hunting, and log investigation.","difficulty":"Intermediate"},
 {"id":"M9","name":"Microsoft Defender XDR","description":"Local Defender XDR Simulator covering endpoint telemetry, alerts, process trees, timelines, and incidents.","difficulty":"Intermediate"},
]
AWS_MAP={
 "M1":["Virtual Compute Instance → EC2 Instance","Object Bucket → S3 Bucket","Virtual Network → VPC"],
 "M2":["Lab IAM User → AWS IAM User","Lab Role → AWS IAM Role","Lab Policy → AWS IAM Policy"],
 "M3":["Virtual Network → VPC","Virtual Security Group → EC2 Security Group","Subnet ACL → Network ACL"],
 "M4":["Virtual Compute Instance → EC2 Instance","Metadata Simulator → EC2 Instance Metadata","Sandbox Container → ECS/EC2 container workload"],
 "M5":["Object Bucket → S3 Bucket","Snapshot → EBS/S3 recovery point","Lab Encryption Key → KMS concept"],
 "M6":["Azure Security Lab Simulator","Microsoft Entra ID","Azure RBAC","Azure VNet / NSG","Azure Storage","Azure VM security"],
 "M7":["Sentinel SIEM Simulator","Data connectors","Analytics rules","Alerts","Incidents"],
 "M8":["KQL Training Engine","SigninLogs","AzureActivity","SecurityAlert","DeviceEvents"],
 "M9":["Defender XDR Simulator","Devices","Alerts","Incidents","Process trees","Attack timeline"],
}
RESOURCE_MAP={
 "M1":[
  {"id":"tenant-novacloud","type":"tenant","name":"NovaCloud Training Tenant","state":"ready"},
  {"id":"vm-web","type":"compute","name":"vm-web","state":"running"},
  {"id":"bucket-assets","type":"storage","name":"bucket-assets","state":"public"},
  {"id":"vnet-main","type":"network","name":"vnet-main","state":"10.10.0.0/16"},
  {"id":"user-analyst","type":"identity","name":"user-analyst","state":"active"},
  {"id":"baseline-security-log","type":"log","name":"security.log","state":"synthetic"}],
 "M2":[
  {"id":"iam-directory","type":"identity-store","name":"NovaCloud IAM Directory","state":"ready"},
  {"id":"iam-users","type":"users","name":"alice / bob / charlie / developer","state":"active"},
  {"id":"iam-groups","type":"groups","name":"admins / developers / auditors","state":"ready"},
  {"id":"iam-roles","type":"roles","name":"DeveloperBuild / AnalystRead / ViewerRead","state":"ready"},
  {"id":"iam-policies","type":"policies","name":"StorageReadOnly / ComputeOperator / AuditViewer","state":"ready"},
  {"id":"fake-access-keys","type":"credential-set","name":"LAB-only access keys","state":"synthetic"},
  {"id":"iam-audit-log","type":"log","name":"IAM audit events","state":"synthetic"}],
 "M3":[
  {"id":"vnet-main","type":"network","name":"vnet-main","state":"10.10.0.0/16"},
  {"id":"public-subnet","type":"subnet","name":"public","state":"10.10.1.0/24"},
  {"id":"private-subnet","type":"subnet","name":"private","state":"10.10.2.0/24"},
  {"id":"web-server","type":"compute","name":"web-server","state":"running"},
  {"id":"database-server","type":"compute","name":"database-server","state":"running"},
  {"id":"security-groups","type":"network-control","name":"web / db security groups","state":"misconfigured"},
  {"id":"network-acl","type":"network-control","name":"subnet ACL","state":"ready"},
  {"id":"network-telemetry","type":"log","name":"synthetic network telemetry","state":"ready"}],
 "M4":[
  {"id":"web-01","type":"compute","name":"web-01","state":"intentionally-insecure"},
  {"id":"api-01","type":"compute","name":"api-01","state":"running"},
  {"id":"package-registry","type":"package-db","name":"virtual package registry","state":"contains-updates"},
  {"id":"metadata-service","type":"metadata","name":"169.254.169.254 simulator","state":"synthetic"},
  {"id":"app-container","type":"container","name":"app-container","state":"intentionally-insecure"},
  {"id":"hardening-baseline","type":"baseline","name":"compute hardening checklist","state":"6-findings"}],
 "M5":[
  {"id":"public-assets","type":"bucket","name":"public-assets","state":"public"},
  {"id":"customer-data","type":"bucket","name":"customer-data","state":"private-or-lab-misconfigured"},
  {"id":"backup-data","type":"bucket","name":"backup-data","state":"private"},
  {"id":"data-catalog","type":"dataset","name":"fictional classification dataset","state":"ready"},
  {"id":"lab-key-1","type":"encryption-key","name":"LAB-KEY-1","state":"lab-only"},
  {"id":"storage-files","type":"filesystem","name":"config.txt / report.txt / archive.txt","state":"ready"},
  {"id":"snapshot-store","type":"recovery","name":"sandbox snapshot store","state":"ready"}],
 "M6":[
  {"id":"entra-tenant","type":"identity-tenant","name":"novacloud.onmicrosoft.local","state":"ready"},
  {"id":"azure-subscription","type":"subscription","name":"NovaCloud-Production","state":"simulated"},
  {"id":"azure-resource-groups","type":"resource-groups","name":"RG-Web / RG-Data / RG-Security","state":"ready"},
  {"id":"vnet-prod","type":"network","name":"VNET-PROD","state":"10.20.0.0/16"},
  {"id":"azure-nsgs","type":"network-control","name":"web-nsg / app-nsg / db-nsg","state":"contains-lab-finding"},
  {"id":"novacloudstorage","type":"storage-account","name":"novacloudstorage","state":"contains-lab-findings"},
  {"id":"azure-vms","type":"compute-set","name":"web-01 / api-01 / database-01","state":"contains-lab-findings"},
  {"id":"azure-security-tables","type":"log-set","name":"AzureActivity / SigninLogs / NSG / StorageLogs / VMEvents","state":"synthetic"}],
 "M7":[
  {"id":"sentinel-workspace","type":"siem-workspace","name":"NovaCloud-SOC","state":"ready"},
  {"id":"sentinel-connectors","type":"connectors","name":"Entra / Azure Activity / Defender / Firewall","state":"simulated"},
  {"id":"sentinel-tables","type":"log-set","name":"SigninLogs / AzureActivity / SecurityAlert / CommonSecurityLog","state":"synthetic"},
  {"id":"analytics-rules","type":"detection-rules","name":"NovaCloud analytics rules","state":"ready"},
  {"id":"sentinel-alerts","type":"alerts","name":"synthetic alert queue","state":"ready"},
  {"id":"sentinel-incidents","type":"incidents","name":"synthetic incident queue","state":"ready"}],
 "M8":[
  {"id":"kql-engine","type":"query-engine","name":"Cloud OS KQL Training Engine","state":"offline"},
  {"id":"SigninLogs","type":"table","name":"SigninLogs","state":"synthetic"},
  {"id":"AzureActivity","type":"table","name":"AzureActivity","state":"synthetic"},
  {"id":"SecurityAlert","type":"table","name":"SecurityAlert","state":"synthetic"},
  {"id":"SecurityIncident","type":"table","name":"SecurityIncident","state":"synthetic"},
  {"id":"DeviceEvents","type":"table","name":"DeviceEvents / DeviceProcessEvents / DeviceNetworkEvents","state":"synthetic"},
  {"id":"CommonSecurityLog","type":"table","name":"CommonSecurityLog","state":"synthetic"},
  {"id":"StorageEvents","type":"table","name":"StorageEvents","state":"synthetic"}],
 "M9":[
  {"id":"defender-xdr","type":"xdr-tenant","name":"NovaCloud Defender XDR Simulator","state":"offline"},
  {"id":"xdr-devices","type":"devices","name":"WS-001 / WS-002 / SERVER-01 / FILESERVER-01","state":"synthetic"},
  {"id":"xdr-alerts","type":"alerts","name":"Defender alert queue","state":"ready"},
  {"id":"xdr-incidents","type":"incidents","name":"Defender incident queue","state":"ready"},
  {"id":"process-tree","type":"telemetry","name":"synthetic process trees","state":"ready"},
  {"id":"attack-timeline","type":"telemetry","name":"cross-device attack timeline","state":"ready"},
  {"id":"advanced-hunting","type":"query-data","name":"endpoint hunting dataset","state":"synthetic"}],
}
def resources_for(module,lab_id):
 base=deepcopy(RESOURCE_MAP.get(module,[]))
 base.append({"id":"lab-workspace","type":"workspace","name":f"{lab_id} isolated workspace","state":"ready"})
 if lab_id=="M69-FINAL":
  merged=[];seen=set()
  for m in ("M6","M7","M8","M9"):
   for r in RESOURCE_MAP[m]:
    if r["id"] not in seen:merged.append(deepcopy(r));seen.add(r["id"])
  merged.append({"id":"lab-workspace","type":"workspace","name":"M69-FINAL isolated workspace","state":"ready"})
  return merged
 return base
def cmd(command,output,mark=None):return {"cmd":command,"output":output,"mark":mark}
def lab(module,num,title,topic,objective,scenario,commands,difficulty="Beginner"):
 lab_id=f"{module}-L{num}";marks=[c["mark"] for c in commands if c.get("mark")]
 return {"id":lab_id,"module":module,"number":f"{module[1:]}.{num}","title":title,"topic":topic,"difficulty":difficulty,"estimated_minutes":12 if difficulty=="Beginner" else 18,"objective":objective,"scenario":scenario,"theory":f"{topic}. Practice inside an isolated Cloud OS simulator; host security settings are never changed.","learn":[objective,"Inspect before changing configuration","Verify the final security state"],"topology":"LAB SANDBOX → simulated cloud resources → verification engine","resources":resources_for(module,lab_id),"commands":commands,"tasks":[{"id":f"{lab_id}-T{i+1}","title":m.replace('-',' ').title(),"required":m,"points":max(1,100//max(1,len(marks))),"hint":"Run help, inspect the sandbox, then apply the required practical change.","failure":f"Sandbox requirement not yet met: {m.replace('-',' ')}."} for i,m in enumerate(marks)],"hints":["Run an inspection command first.","Use help for the current lab command list."],"common_mistakes":["Changing state before inspecting it","Using broader permissions than required","Forgetting Verify Lab"],"security_explanation":"Only lab state changes. Host firewall, users, services, registry, packages, routes, credentials, production tunnels and Cloud OS production data are untouched.","aws_mapping":AWS_MAP[module]}
def challenge(module,title,objective,commands):
 x=lab(module,"C",title,"Module challenge",objective,"NovaCloud Ltd. contains intentional misconfigurations inside the isolated sandbox.",commands,"Intermediate");x["id"]=f"{module}-C";x["number"]=f"{module[1:]}.C";x["estimated_minutes"]=25;x["resources"]=resources_for(module,x["id"]);return x
