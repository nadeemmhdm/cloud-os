from .lab_defs_common import lab,challenge,cmd

LABS=[
 lab("M6",1,"Microsoft Entra ID Fundamentals","Microsoft Entra ID","Inspect identities, privileged roles, and group memberships in a fictional NovaCloud tenant.","Tenant novacloud.onmicrosoft.local contains synthetic users, groups, and role assignments.",[
  cmd("entra users","alice@novacloud.local\nbob@novacloud.local\nanalyst@novacloud.local\nadmin@novacloud.local"),
  cmd("entra groups","Developers\nSecurityTeam\nStorageTeam"),cmd("entra roles","Global Administrator: admin@novacloud.local, alice@novacloud.local\nSecurity Reader: analyst@novacloud.local\nUser Administrator: bob@novacloud.local"),
  cmd("entra user show alice","alice@novacloud.local | Developers | Global Administrator","privileged-user-found"),
  cmd("entra group members Developers","alice@novacloud.local\nbob@novacloud.local","group-membership-checked"),
  cmd("entra flag excessive alice","Finding recorded: alice has excessive Global Administrator privilege.","excessive-privilege-found")],"Beginner–Intermediate"),
 lab("M6",2,"Azure RBAC & Permissions","Azure IAM and RBAC","Detect an excessive Azure role assignment and replace it with least privilege.","NovaCloud-Production contains RG-Web, RG-Data, RG-Security and simulated Azure resources.",[
  cmd("azlab role assignments","alice: Owner @ subscription\nbob: Reader @ RG-Web\nanalyst: Security Reader @ RG-Security"),
  cmd("azlab role show Owner","Owner grants full management and access delegation."),
  cmd("azlab role remove alice Owner","Removed Owner from alice.","broad-role-removed"),
  cmd("azlab role assign alice Virtual Machine Contributor RG-Web","Assigned least-privilege VM Contributor at RG-Web.","least-privilege-assigned"),
  cmd("azlab access-check alice VM-WEB-01","ALLOW: VM operations only. DENY: role assignment and storage administration.","access-verified")],"Intermediate"),
 lab("M6",3,"Azure Networking","Azure VNet and NSG security","Identify and fix a publicly exposed database port.","VNET-PROD 10.20.0.0/16 contains web, app, and db subnets with one intentional NSG error.",[
  cmd("aznet topology","Internet -> web-nsg -> web-subnet 10.20.1.0/24 -> app-subnet 10.20.2.0/24 -> db-subnet 10.20.3.0/24"),
  cmd("aznet nsg list","web-nsg\napp-nsg\ndb-nsg"),cmd("aznet nsg rules db-nsg","ALLOW tcp/1433 source=0.0.0.0/0 destination=db-01 [MISCONFIGURED]","public-db-found"),
  cmd("aznet modify db-nsg 1433 source app-subnet","db-nsg updated: tcp/1433 now allowed only from app-subnet.","public-db-fixed"),
  cmd("aznet test internet db-01 1433","DENY: Internet cannot reach db-01:1433.","network-fix-verified")],"Intermediate"),
 lab("M6",4,"Azure Storage Security","Azure Storage security","Audit and remediate public access, broad permissions, and missing encryption.","novacloudstorage includes public-assets, internal-docs, customer-records, and backups.",[
  cmd("azstorage list","novacloudstorage"),cmd("azstorage container list","public-assets public\ninternal-docs private\ncustomer-records public [MISCONFIGURED]\nbackups private broad-write"),
  cmd("azstorage audit","Findings: customer-records public; backups broad-write; customer-records encryption disabled","storage-findings"),
  cmd("azstorage permissions customer-records private","Public access disabled for customer-records.","storage-private"),
  cmd("azstorage permissions backups read-only","Backups permissions reduced to read-only recovery role.","storage-least-privilege"),
  cmd("azstorage encryption customer-records enable","Simulated encryption enabled.","storage-encrypted")],"Intermediate"),
 lab("M6",5,"Azure Compute Security","Azure Compute security","Harden virtual machines by reducing exposure, patching, and removing an unused account.","web-01, api-01, and database-01 contain synthetic hardening findings.",[
  cmd("azcompute inspect","web-01: outdated packages, SSH public\napi-01: weak service permission, unused account=tempops\ndatabase-01: RDP public"),
  cmd("azcompute close web-01 ssh","SSH exposure removed from Internet.","ssh-closed"),cmd("azcompute close database-01 rdp","RDP exposure removed from Internet.","rdp-closed"),
  cmd("azcompute patch all","Simulated security patches applied to all VMs.","compute-patched"),cmd("azcompute user remove api-01 tempops","Unused synthetic account removed.","unused-user-removed"),
  cmd("azcompute harden api-01","Service permissions hardened.","compute-hardened")],"Intermediate"),
 lab("M6",6,"Azure Security Monitoring","Azure security monitoring","Use synthetic Azure logs to identify suspicious authentication and configuration changes.","AzureActivity, SigninLogs, NetworkSecurityGroupEvent, StorageLogs, and VMEvents contain suspicious events.",[
  cmd("azmonitor tables","AzureActivity\nSigninLogs\nNetworkSecurityGroupEvent\nStorageLogs\nVMEvents"),
  cmd("azmonitor suspicious","2026-10-07T10:42:10Z failed sign-in alice source=203.0.113.45\n2026-10-07T10:51:02Z NSG rule changed by alice source=203.0.113.45\n2026-10-07T11:02:18Z storage public access enabled","suspicious-events-found"),
  cmd("azmonitor filter failed-auth","alice@novacloud.local 203.0.113.45 ResultType=50126","failed-auth-found"),
  cmd("azmonitor filter public-network-change","db-nsg changed source to 0.0.0.0/0 by alice","network-change-found")],"Intermediate"),
 challenge("M6","Secure NovaCloud Azure Environment","Find and correct at least eight Azure security issues across identity, RBAC, networking, storage, and compute.",[
  cmd("azure challenge audit","8 findings: excessive admin, broad Owner, public DB, public customer-records, broad backups, encryption disabled, public SSH, outdated VMs"),
  *[cmd(f"azure challenge fix issue{i}",f"Issue {i} remediated.",f"azure-fix-{i}") for i in range(1,9)]
 ])
]
