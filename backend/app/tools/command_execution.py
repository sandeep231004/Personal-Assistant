"""
Command Execution Tool for running safe system commands.

SECURITY: This tool only allows safe, whitelisted commands.
"""
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Optional, Type, ClassVar, Dict
import subprocess
import logging
import platform
import os

logger = logging.getLogger(__name__)


class CommandExecutionInput(BaseModel):
    """Input schema for command execution tool."""
    command: str = Field(description="The system command to execute (must be from allowed list)")


class CommandExecutionTool(BaseTool):
    """
    Tool for executing safe system commands.

    SECURITY NOTICE:
    - Only whitelisted commands are allowed
    - No destructive operations (delete, format, etc.)
    - No privilege escalation (sudo, admin)
    - No network operations that could be harmful

    Use this when:
    - User asks to list files/directories on THIS computer
    - User wants to check disk space, hostname, OS info
    - User asks about current directory or local system configuration
    """

    name: str = "execute_command"
    description: str = (
        "Execute LOCAL system commands for file/directory operations on THIS computer. "
        "Can: list files, create directories, create/rename/copy/move files, check disk space. "
        "ONLY use for local file system operations. NOT for time, weather, or web information. "
        "Examples: 'create folder test', 'rename file.txt newfile.txt', 'list files'. "
        "Only safe, whitelisted commands are allowed."
    )
    args_schema: Type[BaseModel] = CommandExecutionInput

    # Whitelist of allowed commands (ClassVar to avoid Pydantic field error)
    ALLOWED_COMMANDS: ClassVar[Dict[str, Dict[str, str]]] = {
        # Directory & Files (read)
        "pwd": {"cmd": "cd" if platform.system() == "Windows" else "pwd", "desc": "Show current directory"},
        "ls": {"cmd": "dir" if platform.system() == "Windows" else "ls", "desc": "List files in current directory"},
        "list_files": {"cmd": "dir" if platform.system() == "Windows" else "ls -la", "desc": "List files with details"},

        # Directory & Files (write)
        "mkdir": {"cmd": "mkdir {path}", "desc": "Create a new directory (usage: mkdir foldername)"},
        "touch": {"cmd": "type nul > {path}" if platform.system() == "Windows" else "touch {path}", "desc": "Create a new empty file (usage: touch filename.txt)"},
        "create_file": {"cmd": "type nul > {path}" if platform.system() == "Windows" else "touch {path}", "desc": "Create a new empty file"},
        "rename": {"cmd": "ren {old} {new}" if platform.system() == "Windows" else "mv {old} {new}", "desc": "Rename a file or directory (usage: rename oldname newname)"},
        "copy": {"cmd": "copy {source} {dest}" if platform.system() == "Windows" else "cp {source} {dest}", "desc": "Copy a file (usage: copy source.txt destination.txt)"},
        "move": {"cmd": "move {source} {dest}" if platform.system() == "Windows" else "mv {source} {dest}", "desc": "Move a file (usage: move file.txt newfolder/)"},

        # System Info
        "whoami": {"cmd": "whoami", "desc": "Show current user"},
        "hostname": {"cmd": "hostname", "desc": "Show computer name"},
        "os_info": {"cmd": "ver" if platform.system() == "Windows" else "uname -a", "desc": "Show OS information"},
        "disk_space": {"cmd": "wmic logicaldisk get size,freespace,caption" if platform.system() == "Windows" else "df -h", "desc": "Show disk space"},

        # Network Info (safe, read-only)
        "ip_address": {"cmd": "ipconfig" if platform.system() == "Windows" else "ifconfig", "desc": "Show network configuration"},

        # Python
        "python_version": {"cmd": "python --version", "desc": "Show Python version"},
        "pip_version": {"cmd": "pip --version", "desc": "Show pip version"},
    }

    def _run(self, command: str) -> str:
        """
        Execute a whitelisted command.

        Args:
            command: Command name from allowed list

        Returns:
            Command output or error message
        """
        try:
            logger.info(f"Command execution requested: {command}")

            # Parse command (handle variations)
            command_key = command.lower().strip()

            # Map common variations
            command_map = {
                "where am i": "pwd",
                "current directory": "pwd",
                "show files": "ls",
                "list directory": "ls",
                "my username": "whoami",
                "computer name": "hostname",
                "system info": "os_info",
                "check disk space": "disk_space",
                "my ip": "ip_address",
            }

            # Check for mapped variations
            if command_key in command_map:
                command_key = command_map[command_key]

            # Check if command is allowed
            if command_key not in self.ALLOWED_COMMANDS:
                available = "\n".join([f"- {k}: {v['desc']}" for k, v in self.ALLOWED_COMMANDS.items()])
                return (
                    f"❌ Command '{command}' is not allowed for security reasons.\n\n"
                    f"Available commands:\n{available}\n\n"
                    f"Example: 'list files', 'create folder test', 'rename old.txt new.txt'"
                )

            # Get the actual command to execute
            cmd_info = self.ALLOWED_COMMANDS[command_key]
            actual_cmd = cmd_info["cmd"]

            # Parse parameters if command has placeholders
            if "{" in actual_cmd:
                # Extract parameters from original command
                # Example: "mkdir test" -> path="test"
                # Example: "rename old.txt new.txt" -> old="old.txt", new="new.txt"
                parts = command.split()
                if len(parts) < 2:
                    return f"❌ Command '{command_key}' requires parameters. {cmd_info['desc']}"

                if "{path}" in actual_cmd:
                    path = " ".join(parts[1:])
                    actual_cmd = actual_cmd.replace("{path}", path)
                elif "{old}" in actual_cmd and "{new}" in actual_cmd:
                    if len(parts) < 3:
                        return f"❌ Command '{command_key}' requires two parameters. {cmd_info['desc']}"
                    old = parts[1]
                    new = " ".join(parts[2:])
                    actual_cmd = actual_cmd.replace("{old}", old).replace("{new}", new)
                elif "{source}" in actual_cmd and "{dest}" in actual_cmd:
                    if len(parts) < 3:
                        return f"❌ Command '{command_key}' requires source and destination. {cmd_info['desc']}"
                    source = parts[1]
                    dest = " ".join(parts[2:])
                    actual_cmd = actual_cmd.replace("{source}", source).replace("{dest}", dest)

            logger.info(f"Executing whitelisted command: {actual_cmd}")

            # Execute command
            result = subprocess.run(
                actual_cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=10  # 10 second timeout
            )

            # Format output
            output = result.stdout.strip() if result.stdout else ""
            error = result.stderr.strip() if result.stderr else ""

            if result.returncode == 0:
                return f"✓ Command executed successfully:\n\n{output}" if output else "✓ Command completed (no output)"
            else:
                return f"⚠️ Command failed (exit code {result.returncode}):\n{error}" if error else "Command failed with no error message"

        except subprocess.TimeoutExpired:
            error_msg = f"Command '{command}' timed out after 10 seconds"
            logger.error(error_msg)
            return f"❌ {error_msg}"

        except Exception as e:
            error_msg = f"Error executing command: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return f"❌ {error_msg}"

    async def _arun(self, command: str) -> str:
        """Async version (falls back to sync)."""
        return self._run(command)


class SystemInfoTool(BaseTool):
    """
    Tool for getting system information without executing commands.

    Safer alternative that uses Python's built-in modules.
    """

    name: str = "get_system_info"
    description: str = (
        "Get LOCAL system information like OS, platform, Python version, or current working directory. "
        "ONLY use for queries about THIS computer's configuration. NOT for time, date, or web information. "
        "Use this for quick system queries without executing shell commands."
    )
    args_schema: Type[BaseModel] = CommandExecutionInput

    def _run(self, command: str) -> str:
        """
        Get system information.

        Args:
            command: Type of info requested

        Returns:
            System information
        """
        try:
            command = command.lower().strip()

            info = {}

            if "os" in command or "platform" in command or "system" in command:
                info["Operating System"] = platform.system()

                # Get proper Windows version (Windows 10, 11, etc.)
                if platform.system() == "Windows":
                    try:
                        # Windows 11 = build 22000+, Windows 10 = build 19041+
                        win_ver = platform.win32_ver()
                        release = win_ver[0]  # e.g., "10"
                        build = int(platform.version().split('.')[-1])

                        if release == "10" and build >= 22000:
                            info["OS Version"] = "Windows 11"
                        elif release == "10":
                            info["OS Version"] = "Windows 10"
                        else:
                            info["OS Version"] = f"Windows {release}"

                        info["Build"] = platform.version()
                    except:
                        info["OS Version"] = platform.version()
                else:
                    info["OS Version"] = platform.version()

                info["Platform"] = platform.platform()
                info["Architecture"] = platform.machine()

            if "python" in command:
                info["Python Version"] = platform.python_version()
                info["Python Compiler"] = platform.python_compiler()

            if "directory" in command or "folder" in command or "location" in command:
                info["Current Directory"] = os.getcwd()
                info["Home Directory"] = os.path.expanduser("~")

            if "user" in command:
                info["Username"] = os.getlogin() if hasattr(os, 'getlogin') else "Unknown"

            if not info:
                # Default: return all
                info = {
                    "Operating System": platform.system(),
                    "OS Version": platform.version(),
                    "Python Version": platform.python_version(),
                    "Current Directory": os.getcwd(),
                }

            # Format output
            result = ["System Information:"]
            for key, value in info.items():
                result.append(f"  {key}: {value}")

            return "\n".join(result)

        except Exception as e:
            error_msg = f"Error getting system info: {str(e)}"
            logger.error(error_msg)
            return error_msg

    async def _arun(self, command: str) -> str:
        """Async version (falls back to sync)."""
        return self._run(command)


def get_command_execution_tool() -> CommandExecutionTool:
    """Factory function to create command execution tool instance."""
    return CommandExecutionTool()


def get_system_info_tool() -> SystemInfoTool:
    """Factory function to create system info tool instance."""
    return SystemInfoTool()
