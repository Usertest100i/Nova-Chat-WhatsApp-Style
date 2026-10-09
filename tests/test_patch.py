from __future__ import annotations
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]

def load(path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

patch = load(ROOT / 'scripts/apply_nova.py')
verify = load(ROOT / 'scripts/verify_upstream.py')
pack = load(ROOT / 'scripts/package_release.py')

LEGACY = '''package net.wurstclient.clickgui.screens;
public final class ClickGuiScreen extends Screen {
    public ClickGuiScreen(ClickGui gui) { gui.handleMouseClick(); gui.render(); gui.handleMouseScroll(); }
}'''


def fake(root: Path):
    (root / 'src/main/java/net/wurstclient/clickgui/screens').mkdir(parents=True)
    (root / 'src/main/java/net/wurstclient/keybinds').mkdir(parents=True)
    (root / 'src/main/java/net/wurstclient/hacks').mkdir(parents=True)
    (root / 'src/main/resources').mkdir(parents=True)
    (root / 'gradle.properties').write_text('minecraft_version=26.3\n')
    (root / 'LICENSE.txt').write_text('GNU GENERAL PUBLIC LICENSE')
    (root / patch.SCREEN_REL).write_text(LEGACY)
    (root / patch.KEYS_REL).write_text('addKB(set, "right.control", "clickgui");')
    (root / 'src/main/resources/fabric.mod.json').write_text(json.dumps({'id':'wurst','name':'Wurst Client','version':'1','depends':{'minecraft':'~26.3'},'authors':['Original']}))
    for i in range(100): (root / f'src/main/java/net/wurstclient/hacks/Module{i}Hack.java').touch()
    for name in verify.REQUIRED_HACKS: (root / f'src/main/java/net/wurstclient/hacks/{name}.java').touch()


class TestTheme(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.src=(ROOT/'src/ClickGuiScreen.java').read_text()
    def test_green_palettes(self):
        for color in ('0xFF00A884', '0xFF005C4B', '0xFF111B21', '0xFF202C33'):
            self.assertIn(color, self.src)
    def test_navigation_and_chat_sections(self):
        for value in ('renderList(', 'renderDetail(', 'searchFocused', 'charTyped(', 'keyPressed(', 'visibleRows()'):
            self.assertIn(value, self.src)
    def test_working_modules_not_fake_buttons(self):
        self.assertIn('hack.doPrimaryAction()',self.src)
        self.assertIn('getAllHax()',self.src)
        self.assertIn('getHackByName(',self.src)
    def test_advanced_settings_access(self):
        self.assertIn('new LegacyClickGuiScreen(gui)',self.src)
    def test_input_limit(self):
        self.assertIn('searchQuery.length() < 48',self.src)
    def test_list_clamping(self):
        self.assertIn('hacks.size() - visible',self.src)
        self.assertIn('Math.min(max, listOffset',self.src)
    def test_compact_mode(self):
        self.assertIn('width < 620',self.src)
        self.assertIn('showCompactDetails = false;',self.src)
    def test_no_whatsapp_impersonation(self):
        self.assertNotIn('api.whatsapp.com',self.src)
        self.assertIn('Not affiliated with WhatsApp',self.src)
    def test_persistent_label_keeps_license(self):
        self.assertIn('GPL-3.0-or-later',self.src)
    def test_quick_controls(self):
        for value in ('Flight','Killaura','Freecam','X-Ray'):
            self.assertIn(value,self.src)
    def test_wurst_feature_engine(self):
        self.assertIn('WurstClient.INSTANCE.getHax()', self.src)


class TestInjection(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        fake(self.root)
    def tearDown(self):
        self.tmp.cleanup()
    def test_verification_fails_closed_if_missing_hacks(self):
        (self.root / "src/main/java/net/wurstclient/hacks/FlightHack.java").unlink()
        self.assertRaises(ValueError, verify.check, self.root)
    def test_licensing_check(self):
        (self.root/'LICENSE.txt').unlink()
        self.assertRaises(ValueError, patch.apply, self.root, ROOT)
    def test_bad_version_refused(self):
        (self.root/'gradle.properties').write_text('minecraft_version=1.21.1')
        self.assertRaises(ValueError, patch.apply, self.root, ROOT)
    def test_bad_metadata_refused(self):
        p=self.root/'src/main/resources/fabric.mod.json'
        p.write_text(json.dumps({'id':'random','name':'Wurst Client'}))
        self.assertRaises(ValueError, patch.apply, self.root, ROOT)
        self.assertEqual((self.root/patch.SCREEN_REL).read_text(), LEGACY)
        self.assertIn('right.control', (self.root/patch.KEYS_REL).read_text())
    def test_repeated_patch_refused(self):
        patch.apply(self.root,ROOT)
        self.assertRaises(ValueError,patch.apply,self.root,ROOT)
    def test_applies_complete_patch(self):
        d=patch.apply(self.root,ROOT)
        self.assertEqual(d['default_key'],'F9')
        self.assertEqual(d['theme'],'Nova Chat')
        self.assertEqual((self.root/patch.SCREEN_REL).read_text(),(ROOT/'src/ClickGuiScreen.java').read_text())
        legacy=(self.root/patch.SCREEN_REL.with_name('LegacyClickGuiScreen.java')).read_text()
        self.assertIn('class LegacyClickGuiScreen',legacy)
        self.assertIn('public LegacyClickGuiScreen(',legacy)
        self.assertIn('"f9", "clickgui"',(self.root/patch.KEYS_REL).read_text())
        self.assertTrue((self.root/'NOVA-ATTRIBUTION.md').exists())
    def test_metadata_preserves_mod_id_and_original_author(self):
        patch.apply(self.root,ROOT)
        data=json.loads((self.root/'src/main/resources/fabric.mod.json').read_text())
        self.assertEqual(data['id'],'wurst')
        self.assertEqual(data['name'],'Nova Chat Client (Wurst-based)')
        self.assertEqual(data['authors'],['Original'])
        self.assertEqual(data['depends']['minecraft'],'~26.3')
        self.assertTrue((self.root/'src/main/resources/assets/novachat/icon.png').exists())
    def test_icons_are_png(self):
        p=ROOT/'assets/icon.png'
        self.assertEqual(p.read_bytes()[:8],b'\x89PNG\r\n\x1a\n')
    def test_patch_rejects_ui_changes(self):
        (self.root/patch.SCREEN_REL).write_text('public final class ClickGuiScreen extends Screen {}')
        self.assertRaises(ValueError,patch.apply,self.root,ROOT)


class TestPackaging(unittest.TestCase):
    def test_no_prebuilt_fake_jar(self):
        self.assertFalse(list(ROOT.rglob('*.jar')))
    def test_release_verifies_mod_name(self):
        self.assertIn("meta.get('name') != 'Nova Chat Client (Wurst-based)'",(ROOT/'scripts/package_release.py').read_text())
    def test_release_verifies_original_and_new_gui(self):
        txt=(ROOT/'scripts/package_release.py').read_text()
        self.assertIn('LegacyClickGuiScreen.class',txt)
        self.assertIn('WurstInitializer.class',txt)
    def test_package_errors_if_not_built(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertRaises(ValueError,pack.choose_jar,Path(d))
    def test_ci_compiles_real_source(self):
        workflow=(ROOT/'.github/workflows/build.yml').read_text()
        for val in ('git clone --depth 1 --branch 26.3','./gradlew build','scripts/package_release.py',"java-version: '25'",'upload-artifact@v4'):
            self.assertIn(val,workflow)

if __name__=='__main__':unittest.main()
