from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class ErrorInfo:
    code:str
    message:str
    suggestion:str

ERRORS={
 "AUTH-001":ErrorInfo("AUTH-001","Invalid username or password.","Check the credentials and try again."),
 "AUTH-002":ErrorInfo("AUTH-002","Too many login attempts.","Wait a few minutes before trying again."),
 "AUTH-003":ErrorInfo("AUTH-003","Login required or session expired.","Sign in to Cloud OS again."),
 "PERM-001":ErrorInfo("PERM-001","Permission denied.","Ask an Owner or Admin to grant the required role or permission."),
 "FILE-001":ErrorInfo("FILE-001","File or folder was not found.","Refresh the file list and verify the path."),
 "FILE-002":ErrorInfo("FILE-002","Invalid or unsafe file path.","Use a path inside the configured Cloud OS storage root."),
 "FILE-003":ErrorInfo("FILE-003","Upload exceeds the 1 GiB limit.","Upload a smaller file or split it into parts."),
 "FILE-004":ErrorInfo("FILE-004","The storage root cannot be deleted.","Delete items inside the storage root instead."),
 "FILE-005":ErrorInfo("FILE-005","File operation failed.","Check disk space, path and host filesystem permissions."),
 "TERM-001":ErrorInfo("TERM-001","Requested shell or command is invalid.","Use an available host shell and a valid command."),
 "TERM-002":ErrorInfo("TERM-002","Command timed out.","Check the command and try again."),
 "TERM-003":ErrorInfo("TERM-003","Privileged terminal access is not authorized.","Use an Owner/Admin account and satisfy the host OS authorization requirements."),
 "USER-001":ErrorInfo("USER-001","User operation failed.","Check username, password strength and requested role."),
 "TEAM-001":ErrorInfo("TEAM-001","Team operation failed.","Check the team, user and requested role."),
 "DB-001":ErrorInfo("DB-001","Access database is unreadable or corrupt.","Restore access.json from a trusted backup or repair it locally before restarting Cloud OS."),
 "BACKUP-001":ErrorInfo("BACKUP-001","Backup operation failed.","Check storage space and Cloud OS data-directory permissions."),
 "AI-001":ErrorInfo("AI-001","AI is not configured or the configuration is invalid.","Ask an Owner/Admin to configure an AI provider in Settings."),
 "AI-002":ErrorInfo("AI-002","AI prompt is invalid.","Enter a non-empty prompt within the supported length."),
 "AI-003":ErrorInfo("AI-003","AI provider request failed.","Check the configured provider, model, network connection and API account."),
 "LAB-1001":ErrorInfo("LAB-1001","Lab sandbox failed to initialize.","Retry the lab. If it still fails, run cloud-os doctor and check the Cloud OS data-directory permissions."),
 "LAB-1002":ErrorInfo("LAB-1002","Lab runtime or definition is unavailable.","Refresh Labs and verify that the lab is enabled."),
 "LAB-1003":ErrorInfo("LAB-1003","Lab verification or state operation failed.","Review the practical task state, retry the required commands, and run Verify Lab again."),
 "LAB-1004":ErrorInfo("LAB-1004","Lab session expired.","Start the lab again to create a fresh isolated sandbox."),
 "LAB-1005":ErrorInfo("LAB-1005","Unsafe or unsupported lab command was blocked.","Run help in the Lab Terminal and use only commands provided for the current practical exercise."),
 "LAB-1006":ErrorInfo("LAB-1006","Lab environment reset failed.","Exit the current lab and start a fresh session."),
 "LAB-1007":ErrorInfo("LAB-1007","Lab resource or command-rate limit was exceeded.","Wait briefly, then continue with one lab command at a time."),
 "LAB-1008":ErrorInfo("LAB-1008","Sandbox path violation was blocked.","Use only paths and resources exposed inside the Lab Sandbox."),
 "SYS-001":ErrorInfo("SYS-001","Internal Cloud OS error.","Check the audit/server log and run cloud-os doctor.")
}

def payload(code:str,detail:str|None=None):
    info=ERRORS.get(code,ERRORS["SYS-001"])
    error={"code":info.code,"message":info.message,"suggestion":info.suggestion}
    if detail: error["detail"]=str(detail)[:500]
    return {"error":error}
