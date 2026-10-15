"""Create a local recovery snapshot without changing live application data."""
import hashlib
import json
from pathlib import Path
import sqlite3
import subprocess
from datetime import datetime, timezone


ROOT = Path(__file__).resolve().parents[1]


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def digest(path):
    result = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(chunk)
    return result.hexdigest()


def main():
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output = ROOT / "generated-artifacts" / "backups" / stamp
    output.mkdir(parents=True, exist_ok=False)
    output.chmod(0o700)
    bundle = output / "source.bundle"
    subprocess.run(["git", "bundle", "create", str(bundle), "--all"], cwd=ROOT, check=True)
    subprocess.run(["git", "bundle", "verify", str(bundle)], cwd=ROOT, check=True)
    manifest = {
        "created_at": stamp,
        "source_revision": git("rev-parse", "HEAD"),
        "source_branch": git("branch", "--show-current"),
        "bundle_sha256": digest(bundle),
        "databases": [],
        "limitations": [
            "Local recovery copy only; not an off-site or managed production backup.",
            "External PostgreSQL and managed secrets are not included.",
            "Git bundle contains committed history; uncommitted source is not included.",
        ],
    }
    for relative in [
        "genesis_business_os.db",
        "genesis-business-os/backend/genesis_business_os.db",
    ]:
        source = ROOT / relative
        if not source.is_file():
            continue
        target = output / (relative.replace("/", "__"))
        with sqlite3.connect(source.as_uri() + "?mode=ro", uri=True) as live:
            with sqlite3.connect(target) as backup:
                live.backup(backup)
                if backup.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                    raise RuntimeError("Snapshot integrity verification failed")
        target.chmod(0o600)
        manifest["databases"].append({
            "original_path": relative,
            "snapshot": target.name,
            "sha256": digest(target),
            "integrity_check": "ok",
        })
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    (output / "RESTORE.md").write_text(
        "# Local Genesis recovery\n\n"
        "Do not restore over the running workspace or a populated production database.\n\n"
        "1. Verify the SHA-256 hashes against manifest.json.\n"
        "2. Clone source.bundle into a new temporary recovery directory and check out "
        "the source_revision recorded in the manifest.\n"
        "3. With the recovery application stopped, copy each database snapshot to its "
        "original_path inside that recovery directory.\n"
        "4. Supply secrets again using the supported secrets manager. They are not backed up here.\n"
        "5. Verify integrity and application behavior on the isolated recovery copy before "
        "considering any restoration of the original environment.\n\n"
        "This snapshot is not a production PostgreSQL backup or an off-site disaster recovery system.\n"
    )
    print(json.dumps({"snapshot": str(output.relative_to(ROOT)), **manifest}, indent=2))


if __name__ == "__main__":
    main()
