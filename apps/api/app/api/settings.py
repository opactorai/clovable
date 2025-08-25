import subprocess
import asyncio
import json
import os
from typing import Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.cli.unified_manager import CLIType, CursorAgentCLI

router = APIRouter(prefix="/api/settings", tags=["settings"])

# CLI 옵션과 체크 명령어 정의
CLI_OPTIONS = [
    {
        "id": "claude",
        "name": "Claude Code", 
        "check_command": ["claude", "--version"]
    },
    {
        "id": "cursor",
        "name": "Cursor Agent",
        "check_command": ["cursor-agent", "--version"]
    },
]

class CLIStatusResponse(BaseModel):
    cli_id: str
    installed: bool
    version: str | None = None
    error: str | None = None


async def check_cli_installation(cli_id: str, command: list) -> CLIStatusResponse:
    """단일 CLI의 설치 상태를 확인합니다."""
    try:
        # subprocess를 비동기로 실행
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode == 0:
            # 성공적으로 실행된 경우
            version_output = stdout.decode().strip()
            # 버전 정보에서 실제 버전 번호 추출 (첫 번째 라인만 사용)
            version = version_output.split('\n')[0] if version_output else "installed"
            
            return CLIStatusResponse(
                cli_id=cli_id,
                installed=True,
                version=version
            )
        else:
            # 명령어 실행은 되었지만 에러 리턴 코드
            error_msg = stderr.decode().strip() if stderr else f"Command failed with code {process.returncode}"
            return CLIStatusResponse(
                cli_id=cli_id,
                installed=False,
                error=error_msg
            )
            
    except FileNotFoundError:
        # 명령어를 찾을 수 없는 경우 (설치되지 않음)
        return CLIStatusResponse(
            cli_id=cli_id,
            installed=False,
            error="Command not found"
        )
    except Exception as e:
        # 기타 예외
        return CLIStatusResponse(
            cli_id=cli_id,
            installed=False,
            error=str(e)
        )


@router.get("/cli-status")
async def get_cli_status() -> Dict[str, Any]:
    """모든 CLI의 설치 상태를 확인하고 반환합니다."""
    results = {}
    
    # 새로운 UnifiedCLIManager의 CLI 인스턴스 사용
    from app.services.cli.unified_manager import ClaudeCodeCLI, CursorAgentCLI
    cli_instances = {
        "claude": ClaudeCodeCLI(),
        "cursor": CursorAgentCLI()
    }
    
    # 모든 CLI를 병렬로 확인
    tasks = []
    for cli_id, cli_instance in cli_instances.items():
        async def check_cli(cli_id, cli_instance):
            status = await cli_instance.check_availability()
            return cli_id, status
        
        tasks.append(check_cli(cli_id, cli_instance))
    
    # 모든 태스크 실행
    cli_results = await asyncio.gather(*tasks)
    
    # 결과를 딕셔너리로 변환
    for cli_id, status in cli_results:
        results[cli_id] = {
            "installed": status.get("available", False) and status.get("configured", False),
            "version": status.get("models", ["Unknown"])[0] if status.get("models") else None,
            "error": status.get("error"),
            "checking": False
        }
    
    return results


# 글로벌 설정 관리를 위한 임시 메모리 저장소 (실제로는 데이터베이스에 저장해야 함)
GLOBAL_SETTINGS = {
    "default_cli": "claude",
    "cli_settings": {
        "claude": {
            "model": "claude-sonnet-4",
            "permission_mode": "acceptEdits"  # acceptEdits or bypassPermissions
        },
        "cursor": {"model": "gpt-5"}
    }
}

class GlobalSettingsModel(BaseModel):
    default_cli: str
    cli_settings: Dict[str, Any]


@router.get("/global")
async def get_global_settings() -> Dict[str, Any]:
    """글로벌 설정을 반환합니다."""
    return GLOBAL_SETTINGS


@router.put("/global")
async def update_global_settings(settings: GlobalSettingsModel) -> Dict[str, Any]:
    """글로벌 설정을 업데이트합니다."""
    global GLOBAL_SETTINGS
    
    GLOBAL_SETTINGS.update({
        "default_cli": settings.default_cli,
        "cli_settings": settings.cli_settings
    })
    
    return {"success": True, "settings": GLOBAL_SETTINGS}


class TestPermissionRequest(BaseModel):
    permission_mode: str = "acceptEdits"  # acceptEdits or bypassPermissions


@router.post("/test-permission-mode")
async def test_permission_mode(request: TestPermissionRequest) -> Dict[str, Any]:
    """Test if the specified permission mode works with Claude CLI."""
    
    # Check if running as root
    is_root = os.geteuid() == 0 if hasattr(os, 'geteuid') else False
    
    # Build test command based on permission mode
    if request.permission_mode == "bypassPermissions":
        if is_root:
            return {
                "success": False,
                "error": "Cannot use 'bypassPermissions' mode when running as root/sudo",
                "suggestion": "Use 'acceptEdits' mode instead for root environments",
                "is_root": is_root
            }
        # Test with bypass permissions flag
        test_command = ["claude", "--dangerously-skip-permissions", "--version"]
    else:
        # Test with normal mode (acceptEdits)
        test_command = ["claude", "--version"]
    
    try:
        # Run the test command
        process = await asyncio.create_subprocess_exec(
            *test_command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env={**os.environ, "CLAUDE_NO_INTERACTIVE": "1"}  # Prevent interactive prompts
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode == 0:
            version_output = stdout.decode().strip()
            return {
                "success": True,
                "message": f"Permission mode '{request.permission_mode}' is working correctly",
                "version": version_output.split('\n')[0] if version_output else "Claude CLI detected",
                "is_root": is_root
            }
        else:
            error_output = stderr.decode().strip()
            
            # Check for specific permission error
            if "dangerously-skip-permissions" in error_output and "root" in error_output:
                return {
                    "success": False,
                    "error": "Permission mode conflict: Cannot bypass permissions as root user",
                    "suggestion": "Switch to 'acceptEdits' mode for root environments",
                    "details": error_output,
                    "is_root": is_root
                }
            
            return {
                "success": False,
                "error": f"Claude CLI test failed with permission mode '{request.permission_mode}'",
                "details": error_output or f"Command failed with exit code {process.returncode}",
                "is_root": is_root
            }
            
    except FileNotFoundError:
        return {
            "success": False,
            "error": "Claude CLI not found",
            "suggestion": "Please install Claude Code CLI: npm install -g @anthropic-ai/claude-code",
            "is_root": is_root
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to test permission mode: {str(e)}",
            "is_root": is_root
        }