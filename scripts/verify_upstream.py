#!/usr/bin/env python3
"""Fail rather than build the wrong Minecraft version or a partial client."""
from __future__ import annotations

import re
import sys
from pathlib import Path

REQUIRED_HACKS = (
    'FlightHack', 'KillauraHack', 'FreecamHack', 'XRayHack',
    'NukerHack', 'ClickGuiHack', 'NoFallHack', 'JesusHack',
    'AutoArmorHack', 'AntiAfkHack', 'AutoMineHack', 'MultiAuraHack',
)


def check(root: Path) -> dict:
    if not root.is_dir():
        raise ValueError('Official upstream Wurst source is missing. Clone Wurst-Imperium/Wurst7 branch 26.3.')
    props = root / 'gradle.properties'
    license_file = root / 'LICENSE.txt'
    if not props.is_file() or not license_file.is_file():
        raise ValueError('Not a full Wurst source tree (gradle.properties / LICENSE.txt missing).')
    data = props.read_text(encoding='utf-8')
    match = re.search(r'^\s*minecraft_version\s*=\s*([^#\r\n]+)', data, re.MULTILINE)
    if not match or match.group(1).strip() != '26.3':
        raise ValueError('Expected Minecraft 26.3; refusing to compile a version-mismatched client.')
    license_text = license_file.read_text(encoding='utf-8')
    if 'GNU GENERAL PUBLIC LICENSE' not in license_text:
        raise ValueError('Missing original Wurst GPL license; cannot distribute.')
    hacks_dir = root / 'src/main/java/net/wurstclient/hacks'
    if not hacks_dir.is_dir():
        raise ValueError('Original hacks folder missing.')
    missing = [name for name in REQUIRED_HACKS if not (hacks_dir / (name + '.java')).is_file()]
    if missing:
        raise ValueError('Upstream does not have expected modules: ' + ', '.join(missing))
    count = len(list(hacks_dir.glob('*Hack.java')))
    if count < 100:
        raise ValueError(f'Upstream only contains {count} hack classes; expected at least 100.')
    return {'minecraft': match.group(1).strip(), 'hacks_found': count, 'checked': len(REQUIRED_HACKS)}


if __name__ == '__main__':
    try:
        result = check(Path(sys.argv[1] if len(sys.argv) > 1 else 'upstream'))
    except (ValueError, OSError) as e:
        print('VERIFY FAILED:', e, file=sys.stderr)
        sys.exit(1)
    print('VERIFY PASS:', result)
