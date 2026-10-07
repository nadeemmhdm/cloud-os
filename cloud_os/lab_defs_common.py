MODULES=[
 {"id":"M1","name":"Cloud Security Fundamentals","description":"Cloud models, shared responsibility, IAM, networking, storage, and baseline security tooling.","difficulty":"Beginner"},
 {"id":"M2","name":"Identity & Access Security","description":"Users, groups, policies, least privilege, sandbox access keys, and IAM auditing.","difficulty":"Beginner–Intermediate"},
 {"id":"M3","name":"Network Security","description":"Virtual networks, security groups, ACLs, exposure analysis, and synthetic network monitoring.","difficulty":"Intermediate"},
 {"id":"M4","name":"Compute Security","description":"Instance hardening, ports, patching, metadata protection, containers, and compute baselines.","difficulty":"Intermediate"},
 {"id":"M5","name":"Storage & Data Security","description":"Object storage, public access, permissions, encryption, classification, snapshots, and recovery.","difficulty":"Intermediate"},
]
AWS_MAP={
 "M1":["Virtual Compute Instance → EC2 Instance","Object Bucket → S3 Bucket","Virtual Network → VPC"],
 "M2":["Lab IAM User → AWS IAM User","Lab Role → AWS IAM Role","Lab Policy → AWS IAM Policy"],
 "M3":["Virtual Network → VPC","Virtual Security Group → EC2 Security Group","Subnet ACL → Network ACL"],
 "M4":["Virtual Compute Instance → EC2 Instance","Metadata Simulator → EC2 Instance Metadata","Sandbox Container → ECS/EC2 container workload"],
 "M5":["Object Bucket → S3 Bucket","Snapshot → EBS/S3 recovery point","Lab Encryption Key → KMS concept"],
}
def cmd(command,output,mark=None):return {"cmd":command,"output":output,"mark":mark}
def lab(module,num,title,topic,objective,scenario,commands,difficulty="Beginner"):
 lab_id=f"{module}-L{num}";marks=[c["mark"] for c in commands if c.get("mark")]
 return {"id":lab_id,"module":module,"number":f"{module[1:]}.{num}","title":title,"topic":topic,"difficulty":difficulty,"estimated_minutes":12 if difficulty=="Beginner" else 18,"objective":objective,"scenario":scenario,"theory":f"{topic}. Practice inside an isolated Cloud OS simulator; host security settings are never changed.","learn":[objective,"Inspect before changing configuration","Verify the final security state"],"topology":"LAB SANDBOX → simulated cloud resources → verification engine","commands":commands,"tasks":[{"id":f"{lab_id}-T{i+1}","title":m.replace('-',' ').title(),"required":m,"points":max(1,100//max(1,len(marks))),"hint":"Run help, inspect the sandbox, then apply the required practical change.","failure":f"Sandbox requirement not yet met: {m.replace('-',' ')}."} for i,m in enumerate(marks)],"hints":["Run an inspection command first.","Use help for the current lab command list."],"common_mistakes":["Changing state before inspecting it","Using broader permissions than required","Forgetting Verify Lab"],"security_explanation":"Only lab state changes. Host firewall, users, services, registry, packages, routes, credentials, production tunnels and Cloud OS production data are untouched.","aws_mapping":AWS_MAP[module]}
def challenge(module,title,objective,commands):
 x=lab(module,"C",title,"Module challenge",objective,"NovaCloud Ltd. contains intentional misconfigurations inside the isolated sandbox.",commands,"Intermediate");x["id"]=f"{module}-C";x["number"]=f"{module[1:]}.C";x["estimated_minutes"]=25;return x
