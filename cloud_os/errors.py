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
 "SYS-001":ErrorInfo("SYS-001","Internal Cloud OS error.","Check the audit/server log and run cloud-os doctor.")
}

def payload(code:str,detail:str|None=None):
    info=ERRORS.get(code,ERRORS["SYS-001"])
    error={"code":info.code,"message":info.message,"suggestion":info.suggestion}
    if detail: error["detail"]=str(detail)[:500]
    return {"error":error}
