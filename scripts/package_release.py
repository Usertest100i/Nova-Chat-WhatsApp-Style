#!/usr/bin/env python3
"""Identify the *remapped* Fabric JAR and record its precise source provenance."""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path


def choose_jar(libdir: Path) -> tuple[Path, dict]:
    candidates = []
    for path in sorted(libdir.glob('*.jar')):
        if any(x in path.name for x in ('-dev.jar', '-sources.jar', '-javadoc.jar', '-shadow.jar')):
            continue
        try:
            with zipfile.ZipFile(path) as archive:
                entries = set(archive.namelist())
                if not {'fabric.mod.json', 'net/wurstclient/WurstInitializer.class'}.issubset(entries):
                    continue
                meta = json.loads(archive.read('fabric.mod.json'))
                if meta.get('id') != 'wurst' or meta.get('name') != 'Nova Chat Client (Wurst-based)':
                    continue
                if 'net/wurstclient/clickgui/screens/LegacyClickGuiScreen.class' not in entries:
                    continue
                if 'assets/novachat/icon.png' not in entries:
                    continue
                minecraft = str(meta.get('depends', {}).get('minecraft', ''))
                if '26.3' not in minecraft:
                    continue
                candidates.append((path, meta))
        except (zipfile.BadZipFile, json.JSONDecodeError, UnicodeDecodeError):
            continue
    if len(candidates) != 1:
        raise ValueError(f'Expected exactly one installable Wurst 26.3 JAR; found {len(candidates)} in {libdir}.')
    return candidates[0]


def package(upstream: Path, output: Path) -> Path:
    jar, meta = choose_jar(upstream / 'build/libs')
    output.mkdir(parents=True, exist_ok=True)
    target = output / 'Nova-Chat-Fabric-26.3.jar'
    shutil.copy2(jar, target)
    digest = hashlib.sha256(target.read_bytes()).hexdigest()
    (output / 'SHA256SUMS.txt').write_text(f'{digest}  {target.name}\n', encoding='utf-8')
    commit = subprocess.check_output(['git', '-C', str(upstream), 'rev-parse', 'HEAD'], text=True).strip()
    (output / 'BUILD-INFO.txt').write_text(
        'Client: Nova Chat, a modified Wurst 7 GPL fork\n'
        'Minecraft: 26.3\n'
        f"Wurst version: {meta.get('version', 'unknown')}\n"
        f'Upstream commit: {commit}\n'
        f'Source URL: https://github.com/Wurst-Imperium/Wurst7/tree/{commit}\n'
        'License: GPL-3.0-or-later\n'
        'WhatsApp-inspired GUI, search and F9 bind; GPL upstream credit retained.\n'
        'Not endorsed by Wurst-Imperium.\n',
        encoding='utf-8',
    )
    sourcezip = output / 'Nova-Chat-Fabric-26.3-source.zip'
    with zipfile.ZipFile(sourcezip, 'w', zipfile.ZIP_DEFLATED) as archive:
        for file in upstream.rglob('*'):
            if file.is_file() and not any(part in {'.git', '.gradle', 'build', 'run'} for part in file.relative_to(upstream).parts):
                archive.write(file, file.relative_to(upstream).as_posix())
    with zipfile.ZipFile(sourcezip) as archive:
        if archive.testzip() is not None or 'LICENSE.txt' not in archive.namelist():
            raise ValueError('Modified source archive corrupt or missing license.')
    print('BUILD PACKAGE PASS: verified client', target.name, f'{target.stat().st_size} bytes')
    print('Commit:', commit)
    return target


if __name__ == '__main__':
    try:
        package(Path(sys.argv[1] if len(sys.argv) > 1 else 'upstream').resolve(),
                Path(sys.argv[2] if len(sys.argv) > 2 else 'dist').resolve())
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        print('PACKAGE FAILED:', error, file=sys.stderr)
        sys.exit(1)
