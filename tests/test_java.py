"""Java 21 isolated ABI simulation. Not a substitute for real Minecraft/Fabric compilation."""
from __future__ import annotations
import shutil
import subprocess
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]

STUBS = {
'net/minecraft/network/chat/Component.java': '''package net.minecraft.network.chat;
public class Component { public static Component literal(String s) {return new Component();} }''',
'net/minecraft/client/gui/Font.java': 'package net.minecraft.client.gui; public class Font {}',
'net/minecraft/client/gui/GuiGraphicsExtractor.java': '''package net.minecraft.client.gui;
public class GuiGraphicsExtractor {public final GuiState guiRenderState = new GuiState();
public static class GuiState {public void up() {}}
public void fill(int x, int y, int x2, int y2, int color){}
public void text(Font f,String s,int x,int y,int color,boolean shadow) {}}''',
'net/minecraft/client/input/CharacterEvent.java': '''package net.minecraft.client.input;
public record CharacterEvent(int codepoint) {public boolean isAllowedChatCharacter(){return codepoint >= 32;}
public String codepointAsString(){return Character.toString(codepoint);}}''',
'net/minecraft/client/input/KeyEvent.java': '''package net.minecraft.client.input;
public record KeyEvent(int key,int keycode,int modifiers) {public boolean isEscape(){return key==27;}
public boolean isConfirmation(){return key==13;}}''',
'net/minecraft/client/input/MouseButtonEvent.java': 'package net.minecraft.client.input; public record MouseButtonEvent(int button,double x,double y) {}',
'net/minecraft/client/gui/screens/Screen.java': '''package net.minecraft.client.gui.screens;
import net.minecraft.network.chat.Component;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.input.MouseButtonEvent;
import net.minecraft.client.input.KeyEvent;
import net.minecraft.client.input.CharacterEvent;
public class Screen { protected int width = 900,height = 480; public Screen(Component title){}
public boolean isPauseScreen(){return false;}
public void extractRenderState(GuiGraphicsExtractor g,int x,int y,float d){}
public boolean mouseClicked(MouseButtonEvent e, boolean dbl){return false;}
public boolean mouseScrolled(double x,double y,double horizontal,double vertical){return false;}
public boolean charTyped(CharacterEvent event){return false;}
public boolean keyPressed(KeyEvent event){return false;}
public void extractBackground(GuiGraphicsExtractor g,int x,int y,float delta){}
}''',
'net/minecraft/client/Minecraft.java': '''package net.minecraft.client;
import net.minecraft.client.gui.Font;
import net.minecraft.client.gui.screens.Screen;
public class Minecraft {private static final Minecraft mc=new Minecraft();
public Font font=new Font(); public final Gui gui=new Gui();
public static Minecraft getInstance(){return mc;}
public static class Gui {public Screen screen; public void setScreen(Screen s){screen=s;}}
}''',
'net/wurstclient/Category.java': '''package net.wurstclient;
public enum Category {COMBAT("Combat"), MOVEMENT("Movement"), RENDER("Render");
private final String name; Category(String s){name=s;}
public String getName(){return name;}}''',
'net/wurstclient/hack/Hack.java': '''package net.wurstclient.hack;
import net.wurstclient.Category;
public class Hack {private final String name; private final Category category; private boolean enabled;
public Hack(String name,Category category){this.name=name;this.category=category;}
public String getName(){return name;} public Category getCategory(){return category;}
public boolean isEnabled(){return enabled;} public void doPrimaryAction(){enabled=!enabled;}}''',
'net/wurstclient/hack/HackList.java': '''package net.wurstclient.hack;
import java.util.List; import net.wurstclient.Category;
public class HackList {private final List<Hack> hacks=List.of(new Hack("Flight",Category.MOVEMENT),
new Hack("Killaura",Category.COMBAT),new Hack("Freecam",Category.RENDER),new Hack("X-Ray",Category.RENDER));
public List<Hack> getAllHax(){return hacks;}
public Hack getHackByName(String name){return hacks.stream().filter(h->h.getName().equalsIgnoreCase(name)).findFirst().orElse(null);}}''',
'net/wurstclient/WurstClient.java': '''package net.wurstclient;
import net.wurstclient.hack.HackList;
public enum WurstClient {INSTANCE; private final HackList hax=new HackList();
public HackList getHax(){return hax;}}''',
'net/wurstclient/clickgui/ClickGui.java': 'package net.wurstclient.clickgui; public class ClickGui {}',
'net/wurstclient/clickgui/screens/LegacyClickGuiScreen.java': '''package net.wurstclient.clickgui.screens;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.network.chat.Component;
import net.wurstclient.clickgui.ClickGui;
public class LegacyClickGuiScreen extends Screen {public LegacyClickGuiScreen(ClickGui gui){super(Component.literal("Legacy"));}}''',
'net/wurstclient/clickgui/screens/JavaHarness.java': '''package net.wurstclient.clickgui.screens;
import java.lang.reflect.*;
import java.util.List;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.input.CharacterEvent;
import net.minecraft.client.input.KeyEvent;
import net.minecraft.client.input.MouseButtonEvent;
import net.wurstclient.WurstClient;
import net.wurstclient.clickgui.ClickGui;
import net.wurstclient.hack.Hack;
public class JavaHarness {
static void ck(boolean test,String label){if(!test)throw new AssertionError(label); System.out.println("PASS "+label);}
static Object fld(Object x,String name)throws Exception {Field f=x.getClass().getDeclaredField(name);f.setAccessible(true);return f.get(x);}
public static void main(String[]args)throws Exception {
var screen=new ClickGuiScreen(new ClickGui());
var g=new GuiGraphicsExtractor();
screen.extractRenderState(g,100,200,0);
ck(!screen.isPauseScreen(),"screen does not pause game");
Method filtered=screen.getClass().getDeclaredMethod("filteredHacks");filtered.setAccessible(true);
ck(!((List<?>)filtered.invoke(screen)).isEmpty(),"nonempty mock list");
screen.mouseClicked(new MouseButtonEvent(0,75,81),false); // search focus
ck((boolean)fld(screen,"searchFocused"),"search field focus");
screen.charTyped(new CharacterEvent((int)'f'));
screen.charTyped(new CharacterEvent((int)'l'));
ck("fl".equals(fld(screen,"searchQuery")),"typing search");
screen.keyPressed(new KeyEvent(8,0,0));
ck("f".equals(fld(screen,"searchQuery")),"backspace");
screen.keyPressed(new KeyEvent(27,0,0));
ck(!(boolean)fld(screen,"searchFocused"),"escape exits search");
screen.mouseClicked(new MouseButtonEvent(0,122,175),false);
ck("Flight".equals(fld(screen,"selectedName")),"search result selected");
screen.mouseClicked(new MouseButtonEvent(0,710,200),false);
ck(WurstClient.INSTANCE.getHax().getHackByName("Flight").isEnabled(),"real toggle delegation");
screen.mouseClicked(new MouseButtonEvent(0,824,25),false);
ck(Minecraft.getInstance().gui.screen instanceof LegacyClickGuiScreen,"advanced GUI preserved");
var small=new ClickGuiScreen(new ClickGui());
Field width=small.getClass().getSuperclass().getDeclaredField("width"); width.setAccessible(true);width.setInt(small,450);
small.mouseClicked(new MouseButtonEvent(0,75,81),false);
small.mouseClicked(new MouseButtonEvent(0,100,173),false);
ck((boolean)fld(small,"showCompactDetails"),"compact chat details");
small.mouseClicked(new MouseButtonEvent(0,58,22),false);
ck(!(boolean)fld(small,"showCompactDetails"),"compact back navigation");
small.extractRenderState(g,200,100,0);
}
}'''
}

class JavaTest(unittest.TestCase):
    def test_compile_and_interact(self):
        if not shutil.which('javac') or not shutil.which('java'):
            self.skipTest('Java not available')
        with tempfile.TemporaryDirectory() as dirname:
            path=Path(dirname)
            for name,src in STUBS.items():
                file=path/name;file.parent.mkdir(parents=True,exist_ok=True);file.write_text(src)
            custom=path/'net/wurstclient/clickgui/screens/ClickGuiScreen.java'
            custom.write_bytes((ROOT/'src/ClickGuiScreen.java').read_bytes())
            files=[str(file) for file in path.rglob('*.java')]
            result=subprocess.run(['javac','-encoding','UTF-8','-d',str(path),*files],capture_output=True,text=True,timeout=60)
            self.assertEqual(result.returncode,0,result.stderr)
            process=subprocess.run(['java','-cp',str(path),'net.wurstclient.clickgui.screens.JavaHarness'],capture_output=True,text=True,timeout=30)
            self.assertEqual(process.returncode,0,process.stdout+'\n'+process.stderr)
            self.assertEqual(process.stdout.count('PASS '),11,process.stdout)

if __name__=='__main__': unittest.main()
