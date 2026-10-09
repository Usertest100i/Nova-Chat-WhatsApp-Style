#!/usr/bin/env python3
"""Apply the Nova Chat interface to an *existing* Wurst 7 source tree.

Fail closed when upstream paths/signatures no longer match; never silently ship
an unmodified upstream client as a "Nova" release.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re
import shutil

EXPECTED_VERSION = '26.3'
SCREEN_REL = Path('src/main/java/net/wurstclient/clickgui/screens/ClickGuiScreen.java')
KEYS_REL = Path('src/main/java/net/wurstclient/keybinds/KeybindList.java')


def replace_exact(source: str, before: str, after: str) -> str:
    if source.count(before) != 1:
        raise ValueError(f'Expected exactly one source signature, found {source.count(before)}: {before[:80]!r}')
    return source.replace(before, after, 1)


def apply(upstream: Path, project: Path) -> dict:
    props = (upstream / 'gradle.properties').read_text(encoding='utf8')
    match = re.search(r'^\s*minecraft_version\s*=\s*([^\s#]+)', props, re.M)
    if not match or match.group(1) != EXPECTED_VERSION:
        raise ValueError('Wrong upstream Minecraft version; expected ' + EXPECTED_VERSION)
    license_file = upstream / 'LICENSE.txt'
    if not license_file.is_file() or 'GENERAL PUBLIC LICENSE' not in license_file.read_text(encoding='utf8'):
        raise ValueError('Missing original Wurst GPL license')

    original_path = upstream / SCREEN_REL
    original = original_path.read_text(encoding='utf8')
    if 'public final class ClickGuiScreen extends Screen' not in original:
        raise ValueError('ClickGuiScreen API changed; refusing to patch')
    legacy = replace_exact(original,
        'public final class ClickGuiScreen extends Screen',
        'public final class LegacyClickGuiScreen extends Screen')
    legacy = replace_exact(legacy, 'public ClickGuiScreen(ClickGui gui)',
        'public LegacyClickGuiScreen(ClickGui gui)')
    if not all(token in legacy for token in (
        'gui.handleMouseClick(', 'gui.render(', 'gui.handleMouseScroll(')):
        raise ValueError('Original click GUI hooks changed')

    keys_path = upstream / KEYS_REL
    keys = keys_path.read_text(encoding='utf8')
    # A distinct default F9 binding on new installs. Existing Wurst configs may override.
    keys = replace_exact(keys,
        'addKB(set, "right.control", "clickgui");',
        'addKB(set, "f9", "clickgui");')

    custom = (project / 'src/ClickGuiScreen.java').read_text(encoding='utf8')
    for token in ('LegacyClickGuiScreen', 'getAllHax()', 'mouseClicked(', 'extractRenderState(',
                  'SEARCH', 'BUBBLE', 'charTyped(', 'keyPressed('):
        if token not in custom:
            raise ValueError(f'Nova source missing {token}')
    meta_path = upstream / 'src/main/resources/fabric.mod.json'
    mod_meta = json.loads(meta_path.read_text(encoding='utf8'))
    if mod_meta.get('id') != 'wurst' or mod_meta.get('name') != 'Wurst Client':
        raise ValueError('Expected original Wurst mod metadata')
    if not (project / 'assets/icon.png').is_file():
        raise ValueError('Custom icon is missing')
    # All validation is complete before making any modifications to upstream files.
    original_path.with_name('LegacyClickGuiScreen.java').write_text(legacy, encoding='utf8')
    original_path.write_text(custom, encoding='utf8')
    keys_path.write_text(keys, encoding='utf8')
    # Keep internal mod id 'wurst' to preserve upstream mixin/config compatibility.
    mod_meta['name'] = 'Nova Chat Client (Wurst-based)'
    mod_meta['description'] = 'WhatsApp-inspired module dashboard for the Wurst 7 engine. Not affiliated with Meta.'
    mod_meta['icon'] = 'assets/novachat/icon.png'
    mod_meta['contributors'] = list(dict.fromkeys(mod_meta.get('contributors', []) + ['Nova Chat UI contributors']))
    meta_path.write_text(json.dumps(mod_meta, indent=2, ensure_ascii=False) + '\n', encoding='utf8')
    icon_path = upstream / 'src/main/resources/assets/novachat/icon.png'
    icon_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(project / 'assets/icon.png', icon_path)
    (upstream / 'NOVA-ATTRIBUTION.md').write_text('''# Nova Chat UI modifications

This project is a modified fork of Wurst 7 licensed GPL-3.0-or-later.
Upstream copyright: Wurst-Imperium and contributors.
Custom work: WhatsApp-inspired green/dark module UI, searchable module list, alternate layout, default F9 binding, and a custom mod icon. The original settings GUI remains in LegacyClickGuiScreen.
The **mod id is still `wurst`** for upstream compatibility, but the visible name is Nova Chat Client (Wurst-based). Do not install alongside Wurst; use one or the other.
Source: https://github.com/Wurst-Imperium/Wurst7
Not affiliated with or endorsed by Wurst-Imperium, WhatsApp, or Meta.
''', encoding='utf8')
    return {'minecraft': EXPECTED_VERSION, 'new_screen': str(original_path), 'old_screen': 'LegacyClickGuiScreen.java', 'default_key': 'F9', 'theme':'Nova Chat'}


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('upstream', type=Path)
    ap.add_argument('--project', type=Path, default=Path(__file__).resolve().parent.parent)
    args = ap.parse_args()
    print('NOVA APPLIED:', apply(args.upstream, args.project))
