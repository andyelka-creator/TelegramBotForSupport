import asyncio
import json
import re
import shlex
from dataclasses import dataclass


@dataclass(frozen=True)
class MtgRotationTarget:
    name: str
    ssh_target: str
    config_path: str
    service_name: str


@dataclass(frozen=True)
class MtgRotationResult:
    target_name: str
    ssh_target: str
    ok: bool
    tg_url: str = ""
    tme_url: str = ""
    error: str = ""


_SAFE_SSH_TARGET_RE = re.compile(r"^[a-zA-Z0-9_.@:-]+$")
_SAFE_PATH_RE = re.compile(r"^/[a-zA-Z0-9_./-]+$")
_SAFE_SERVICE_RE = re.compile(r"^[a-zA-Z0-9_.@-]+$")
_SAFE_DOMAIN_RE = re.compile(r"^[a-zA-Z0-9.-]+$")


def parse_mtg_rotation_targets(raw: str) -> list[MtgRotationTarget]:
    """
    Format:
    NAME|SSH_TARGET|CONFIG_PATH|SERVICE_NAME;NAME2|SSH_TARGET2|CONFIG_PATH2|SERVICE_NAME2
    """
    targets: list[MtgRotationTarget] = []
    if not raw.strip():
        return targets

    for chunk in raw.split(";"):
        part = chunk.strip()
        if not part:
            continue
        fields = [x.strip() for x in part.split("|")]
        if len(fields) != 4:
            raise ValueError(
                "Invalid MTG_ROTATION_TARGETS format. "
                "Expected NAME|SSH_TARGET|CONFIG_PATH|SERVICE_NAME separated by ';'"
            )
        target = MtgRotationTarget(
            name=fields[0],
            ssh_target=fields[1],
            config_path=fields[2],
            service_name=fields[3],
        )
        _validate_target(target)
        targets.append(target)
    return targets


def _validate_target(target: MtgRotationTarget) -> None:
    if not target.name:
        raise ValueError("MTG target name cannot be empty")
    if not _SAFE_SSH_TARGET_RE.fullmatch(target.ssh_target):
        raise ValueError(f"Unsafe ssh target: {target.ssh_target}")
    if not _SAFE_PATH_RE.fullmatch(target.config_path):
        raise ValueError(f"Unsafe config path: {target.config_path}")
    if not _SAFE_SERVICE_RE.fullmatch(target.service_name):
        raise ValueError(f"Unsafe service name: {target.service_name}")


async def rotate_on_targets(
    targets: list[MtgRotationTarget], front_domain: str, timeout_sec: int = 45, ssh_key_path: str = ""
) -> list[MtgRotationResult]:
    if not _SAFE_DOMAIN_RE.fullmatch(front_domain):
        raise ValueError(f"Unsafe fronting domain: {front_domain}")

    results: list[MtgRotationResult] = []
    for target in targets:
        results.append(
            await _rotate_one(
                target,
                front_domain=front_domain,
                timeout_sec=timeout_sec,
                ssh_key_path=ssh_key_path,
            )
        )
    return results


async def _rotate_one(
    target: MtgRotationTarget, front_domain: str, timeout_sec: int, ssh_key_path: str = ""
) -> MtgRotationResult:
    remote_script = (
        "set -euo pipefail; "
        f"SECRET=$(/usr/local/bin/mtg generate-secret --hex {shlex.quote(front_domain)}); "
        f'sed -i "s/^secret = .*/secret = \\"$SECRET\\"/" {shlex.quote(target.config_path)}; '
        f"systemctl restart {shlex.quote(target.service_name)}; "
        f"/usr/local/bin/mtg access {shlex.quote(target.config_path)}"
    )
    cmd = [
        "ssh",
        "-o",
        "BatchMode=yes",
        "-o",
        "ConnectTimeout=10",
        "-o",
        "StrictHostKeyChecking=accept-new",
    ]
    if ssh_key_path:
        cmd.extend(["-i", ssh_key_path])
    cmd.extend([target.ssh_target, remote_script])
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout_b, stderr_b = await asyncio.wait_for(proc.communicate(), timeout=timeout_sec)
    except asyncio.TimeoutError:
        proc.kill()
        await proc.communicate()
        return MtgRotationResult(
            target_name=target.name,
            ssh_target=target.ssh_target,
            ok=False,
            error=f"Timeout after {timeout_sec}s",
        )

    stdout = stdout_b.decode("utf-8", errors="replace").strip()
    stderr = stderr_b.decode("utf-8", errors="replace").strip()

    if proc.returncode != 0:
        err = stderr or stdout or f"SSH command failed with code {proc.returncode}"
        return MtgRotationResult(
            target_name=target.name,
            ssh_target=target.ssh_target,
            ok=False,
            error=err,
        )

    try:
        payload = json.loads(stdout)
        ipv4 = payload.get("ipv4", {})
        return MtgRotationResult(
            target_name=target.name,
            ssh_target=target.ssh_target,
            ok=True,
            tg_url=str(ipv4.get("tg_url", "")),
            tme_url=str(ipv4.get("tme_url", "")),
        )
    except json.JSONDecodeError:
        return MtgRotationResult(
            target_name=target.name,
            ssh_target=target.ssh_target,
            ok=False,
            error=f"Cannot parse mtg access output as JSON: {stdout[:500]}",
        )
