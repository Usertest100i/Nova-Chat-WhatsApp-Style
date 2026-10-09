/*
 * Nova Chat UI - an original WhatsApp-inspired interface for Wurst 7.
 * Copyright (c) 2026 Nova Chat contributors. GPL-3.0-or-later.
 * Wurst upstream: copyright Wurst-Imperium and contributors.
 * Not affiliated with WhatsApp, Meta, or Wurst-Imperium.
 */
package net.wurstclient.clickgui.screens;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Locale;

import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.Font;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.client.input.CharacterEvent;
import net.minecraft.client.input.KeyEvent;
import net.minecraft.client.input.MouseButtonEvent;
import net.minecraft.network.chat.Component;
import net.wurstclient.Category;
import net.wurstclient.WurstClient;
import net.wurstclient.clickgui.ClickGui;
import net.wurstclient.hack.Hack;

/**
 * WhatsApp-inspired conversations list for Wurst modules.
 * UI-only change: each toggle delegates to upstream Hack.doPrimaryAction().
 * Config and advanced per-module settings remain available in LegacyClickGuiScreen.
 */
public final class ClickGuiScreen extends Screen
{
    private static final int BG = 0xFF0B141A;
    private static final int RAIL = 0xFF202C33;
    private static final int LIST = 0xFF111B21;
    private static final int HEADER = 0xFF202C33;
    private static final int ROW_HOVER = 0xFF26353D;
    private static final int ROW_SELECTED = 0xFF2A3942;
    private static final int SEARCH = 0xFF202C33;
    private static final int GREEN = 0xFF00A884;
    private static final int GREEN_LIGHT = 0xFF53BDA5;
    private static final int BUBBLE = 0xFF005C4B;
    private static final int MESSAGE = 0xFF202C33;
    private static final int PRIMARY = 0xFFE9EDEF;
    private static final int SECONDARY = 0xFF8696A0;
    private static final int DIVIDER = 0xFF30434C;
    private static final int OFF = 0xFF54656F;
    private static final int ROW_HEIGHT = 51;
    private static final String[] QUICK = {"Flight", "Killaura", "Freecam", "X-Ray"};

    private final ClickGui gui;
    private int selectedCategory = -1;
    private int listOffset = 0;
    private int categoryOffset = 0;
    private String selectedName = "";
    private boolean showCompactDetails = false;
    private boolean searchFocused = false;
    private String searchQuery = "";
    private String notification = "";
    private long notificationAt = 0;

    public ClickGuiScreen(ClickGui gui)
    {
        super(Component.literal("Nova Chat"));
        this.gui = gui;
    }

    @Override
    public boolean isPauseScreen()
    {
        return false;
    }

    private int railW()
    {
        return Math.min(58, Math.max(42, width / 10));
    }

    private boolean compact()
    {
        return width < 620;
    }

    private int listW()
    {
        int remaining = Math.max(0, width - railW());
        return compact() ? remaining : Math.min(300, Math.max(174, remaining * 40 / 100));
    }

    private int listX()
    {
        return railW();
    }

    private int detailX()
    {
        return listX() + listW();
    }

    private boolean listVisible()
    {
        return !compact() || !showCompactDetails;
    }

    private boolean detailVisible()
    {
        return !compact() || showCompactDetails;
    }

    private int visibleRows()
    {
        return Math.max(1, (height - 155) / ROW_HEIGHT);
    }

    private List<Hack> filteredHacks()
    {
        ArrayList<Hack> hacks = new ArrayList<>(WurstClient.INSTANCE.getHax().getAllHax());
        if(selectedCategory >= 0 && selectedCategory < Category.values().length)
        {
            Category category = Category.values()[selectedCategory];
            hacks.removeIf(h -> h.getCategory() != category);
        }
        String query = searchQuery.trim().toLowerCase(Locale.ROOT);
        if(!query.isEmpty()) hacks.removeIf(h -> !h.getName().toLowerCase(Locale.ROOT).contains(query));
        hacks.sort(Comparator.comparing((Hack h) -> !h.isEnabled())
            .thenComparing(h -> h.getName().toLowerCase(Locale.ROOT)));
        return hacks;
    }

    private Hack selected(List<Hack> hacks)
    {
        for(Hack hack : hacks)
            if(hack.getName().equals(selectedName)) return hack;
        return hacks.isEmpty() ? null : hacks.get(0);
    }

    private static void fill(GuiGraphicsExtractor g, int x, int y, int w, int h, int color)
    {
        if(w > 0 && h > 0) g.fill(x, y, x + w, y + h, color);
    }

    private static void txt(GuiGraphicsExtractor g, Font f, String value, int x, int y, int color)
    {
        g.text(f, value, x, y, color, false);
    }

    private static boolean hit(double mx, double my, int x, int y, int w, int h)
    {
        return w > 0 && h > 0 && mx >= x && my >= y && mx < x + w && my < y + h;
    }

    private String fit(String value, int px)
    {
        int max = Math.max(1, px / 6);
        if(value.length() <= max) return value;
        return max < 4 ? value.substring(0, max) : value.substring(0, max - 3) + "...";
    }

    private void toast(String value)
    {
        notification = value;
        notificationAt = System.currentTimeMillis();
    }

    private void action(Hack hack)
    {
        if(hack == null) return;
        hack.doPrimaryAction();
        toast(hack.getName() + (hack.isEnabled() ? " enabled" : " action completed / disabled"));
    }

    private void action(String name)
    {
        action(WurstClient.INSTANCE.getHax().getHackByName(name));
    }

    private void changeCategory(int category)
    {
        if(category < -1 || category >= Category.values().length) return;
        selectedCategory = category;
        listOffset = 0;
        showCompactDetails = false;
        selectedName = "";
    }

    @Override
    public void extractRenderState(GuiGraphicsExtractor g, int mx, int my, float delta)
    {
        Font font = Minecraft.getInstance().font;
        int r = railW();
        List<Hack> all = filteredHacks();
        Hack current = selected(all);
        int active = 0;
        for(Hack hack : WurstClient.INSTANCE.getHax().getAllHax()) if(hack.isEnabled()) active++;

        g.guiRenderState.up();
        fill(g, 0, 0, width, height, BG);
        fill(g, 0, 0, r, height, RAIL);
        fill(g, 0, 0, r, 59, GREEN);
        fill(g, Math.max(5, (r - 31) / 2), 12, 31, 31, 0xFF075E52);
        txt(g, font, "NC", Math.max(8, (r - 19) / 2), 23, PRIMARY);
        txt(g, font, "CATS", 7, 75, SECONDARY);

        int shownCategories = Math.max(1, (height - 137) / 34);
        for(int i = categoryOffset; i <= Category.values().length && i < categoryOffset + shownCategories; i++)
        {
            int categoryIndex = i - 1;
            String label = categoryIndex < 0 ? "ALL" : Category.values()[categoryIndex].getName().toUpperCase(Locale.ROOT);
            int y = 89 + (i - categoryOffset) * 34;
            boolean picked = selectedCategory == categoryIndex;
            if(picked) fill(g, 0, y, 4, 30, GREEN);
            fill(g, 6, y + 2, r - 12, 26, picked ? ROW_SELECTED : RAIL);
            txt(g, font, fit(label, r - 18), 9, y + 11, picked ? GREEN_LIGHT : PRIMARY);
        }
        txt(g, font, "F9", 12, height - 20, GREEN_LIGHT);
        if(listVisible()) renderList(g, font, mx, my, all, current, active);
        if(detailVisible()) renderDetail(g, font, mx, my, current, all.size(), active);
        if(System.currentTimeMillis() - notificationAt < 2900 && !notification.isEmpty())
        {
            int w = Math.min(Math.max(125, notification.length() * 6 + 20), Math.max(125, width - r - 10));
            int x = Math.max(r + 4, (width - w) / 2);
            fill(g, x, height - 44, w, 27, HEADER);
            fill(g, x, height - 44, 3, 27, GREEN);
            txt(g, font, fit(notification, w - 20), x + 10, height - 35, PRIMARY);
        }
    }

    private void renderList(GuiGraphicsExtractor g, Font f, int mx, int my,
        List<Hack> hacks, Hack current, int active)
    {
        int x = listX();
        int w = listW();
        fill(g, x, 0, w, height, LIST);
        fill(g, x, 0, w, 59, HEADER);
        txt(g, f, "NOVA CHAT", x + 14, 14, PRIMARY);
        txt(g, f, active + " active modules", x + 14, 35, GREEN_LIGHT);
        fill(g, x + 10, 68, w - 20, 31, SEARCH);
        txt(g, f, "o", x + 19, 79, GREEN_LIGHT);
        String hint = searchQuery.isEmpty() ? "Search modules..." : searchQuery;
        txt(g, f, fit(hint + (searchFocused ? "|" : ""), w - 64), x + 37, 79,
            searchQuery.isEmpty() ? SECONDARY : PRIMARY);
        if(!searchQuery.isEmpty()) txt(g, f, "X", x + w - 26, 79, GREEN_LIGHT);
        fill(g, x + 10, 109, 61, 23, selectedCategory == -1 ? BUBBLE : SEARCH);
        txt(g, f, "All", x + 32, 117, PRIMARY);
        fill(g, x + 77, 109, 72, 23, SEARCH);
        txt(g, f, "Modules", x + 88, 117, GREEN_LIGHT);
        txt(g, f, hacks.size() + " found", x + 12, 140, SECONDARY);
        fill(g, x, 150, w, 1, DIVIDER);
        int visible = visibleRows();
        listOffset = Math.min(Math.max(0, hacks.size() - visible), Math.max(0, listOffset));
        for(int i = listOffset; i < hacks.size() && i < listOffset + visible; i++)
        {
            Hack hack = hacks.get(i);
            int y = 151 + (i - listOffset) * ROW_HEIGHT;
            boolean chosen = current != null && current.getName().equals(hack.getName());
            if(chosen) fill(g, x, y, w, ROW_HEIGHT, ROW_SELECTED);
            else if(hit(mx, my, x, y, w, ROW_HEIGHT)) fill(g, x, y, w, ROW_HEIGHT, ROW_HOVER);
            fill(g, x + 12, y + 9, 32, 32, chosen ? GREEN : 0xFF33565A);
            String letter = hack.getName().substring(0, 1).toUpperCase(Locale.ROOT);
            txt(g, f, letter, x + 24, y + 21, PRIMARY);
            txt(g, f, fit(hack.getName(), w - 94), x + 55, y + 13, PRIMARY);
            txt(g, f, hack.isEnabled() ? "Enabled  /  tap to manage" : "Available  /  tap to manage",
                x + 55, y + 32, hack.isEnabled() ? GREEN_LIGHT : SECONDARY);
            if(hack.isEnabled()) fill(g, x + w - 20, y + 20, 7, 7, GREEN);
            fill(g, x + 55, y + ROW_HEIGHT - 1, w - 67, 1, DIVIDER);
        }
        fill(g, x, height - 22, w, 22, HEADER);
        txt(g, f, fit("Scroll to browse / click a module", w - 22), x + 12, height - 15, SECONDARY);
    }

    private void renderDetail(GuiGraphicsExtractor g, Font f, int mx, int my,
        Hack current, int count, int active)
    {
        int x = compact() ? railW() : detailX();
        int w = Math.max(1, width - x);
        fill(g, x, 0, w, height, BG);
        // Subtle geometric wallpaper, deliberately drawn with cheap primitive fills.
        for(int yy = 75; yy < height - 45; yy += 58)
            for(int xx = x + 12; xx < width; xx += 70)
                fill(g, xx, yy, 10, 1, 0xFF15272B);
        fill(g, x, 0, w, 59, HEADER);
        if(compact()) txt(g, f, "<", x + 10, 26, GREEN_LIGHT);
        int avatarX = x + (compact() ? 30 : 16);
        fill(g, avatarX, 12, 35, 35, BUBBLE);
        txt(g, f, "N", avatarX + 13, 25, PRIMARY);
        txt(g, f, fit(current == null ? "Your modules" : current.getName(), w - 155), avatarX + 47, 18, PRIMARY);
        txt(g, f, "Aster Nova / Fabric", avatarX + 47, 36, SECONDARY);
        fill(g, width - 105, 16, 92, 26, ROW_SELECTED);
        txt(g, f, "SETTINGS >", width - 98, 25, GREEN_LIGHT);
        if(current == null)
        {
            txt(g, f, "No modules match this search.", x + 20, 91, SECONDARY);
            txt(g, f, "Clear search or choose another category.", x + 20, 113, SECONDARY);
            return;
        }
        int inset = Math.max(12, Math.min(30, w / 14));
        int messageW = Math.max(120, Math.min(350, w - inset * 2));
        fill(g, x + inset, 87, messageW, 68, MESSAGE);
        fill(g, x + inset, 87, 3, 68, GREEN);
        txt(g, f, "NOVA ASSISTANT", x + inset + 11, 97, GREEN_LIGHT);
        txt(g, f, fit("Module: " + current.getName(), messageW - 23), x + inset + 11, 118, PRIMARY);
        txt(g, f, fit("Category: " + current.getCategory().getName(), messageW - 23), x + inset + 11, 138, SECONDARY);

        int bubbleW = Math.min(280, Math.max(135, w - 2 * inset));
        int bubbleX = width - inset - bubbleW;
        fill(g, bubbleX, 171, bubbleW, 76, BUBBLE);
        txt(g, f, "QUICK CONTROL", bubbleX + 14, 185, 0xFFD9FDD3);
        txt(g, f, current.isEnabled() ? "Status: ACTIVE" : "Status: INACTIVE",
            bubbleX + 14, 208, PRIMARY);
        fill(g, bubbleX + 14, 226, bubbleW - 28, 17, current.isEnabled() ? GREEN : ROW_SELECTED);
        txt(g, f, current.isEnabled() ? "TAP TO DISABLE" : "TAP TO ENABLE / RUN", bubbleX + 20, 231, PRIMARY);

        int boxY = 263;
        fill(g, x + inset, boxY, messageW, 58, MESSAGE);
        txt(g, f, "Need all module settings?", x + inset + 12, boxY + 13, PRIMARY);
        txt(g, f, "Use SETTINGS > at the top-right.", x + inset + 12, boxY + 35, SECONDARY);

        int shortcutsY = Math.max(336, height - 92);
        if(shortcutsY + 63 < height)
        {
            txt(g, f, "PINNED SHORTCUTS", x + inset, shortcutsY, SECONDARY);
            int itemW = Math.max(40, (w - 2 * inset - 18) / QUICK.length - 1);
            for(int i = 0; i < QUICK.length; i++)
            {
                int bx = x + inset + i * (itemW + 6);
                Hack quickHack = WurstClient.INSTANCE.getHax().getHackByName(QUICK[i]);
                boolean on = quickHack != null && quickHack.isEnabled();
                fill(g, bx, shortcutsY + 19, itemW, 30, on ? BUBBLE : ROW_SELECTED);
                txt(g, f, fit(QUICK[i], itemW - 10), bx + 5, shortcutsY + 30, on ? GREEN_LIGHT : PRIMARY);
            }
        }
        fill(g, x, height - 30, w, 30, HEADER);
        txt(g, f, fit("" + count + " chats  /  " + active + " active  /  F9 menu",
            w - 26), x + 15, height - 20, SECONDARY);
    }

    @Override
    public boolean mouseClicked(MouseButtonEvent event, boolean doubleClick)
    {
        if(event.button() != 0) return super.mouseClicked(event, doubleClick);
        double mx = event.x();
        double my = event.y();
        int r = railW();
        if(mx < r)
        {
            int shown = Math.max(1, (height - 137) / 34);
            for(int i = categoryOffset; i <= Category.values().length && i < categoryOffset + shown; i++)
                if(hit(mx, my, 6, 89 + (i - categoryOffset) * 34, r - 12, 30))
                {
                    changeCategory(i - 1);
                    return true;
                }
            return true;
        }
        if(listVisible() && mx < detailX())
        {
            int x = listX();
            int w = listW();
            if(hit(mx, my, x + 10, 68, w - 20, 31))
            {
                if(!searchQuery.isEmpty() && mx > x + w - 36) searchQuery = "";
                searchFocused = true;
                listOffset = 0;
                return true;
            }
            searchFocused = false;
            if(hit(mx, my, x + 10, 109, 61, 23))
            {
                changeCategory(-1);
                return true;
            }
            int row = (int)(my - 151) / ROW_HEIGHT;
            if(my >= 151 && my < Math.min(height - 22, 151 + visibleRows() * ROW_HEIGHT))
            {
                List<Hack> hacks = filteredHacks();
                int position = row + listOffset;
                if(row >= 0 && position < hacks.size())
                {
                    selectedName = hacks.get(position).getName();
                    showCompactDetails = true;
                    return true;
                }
            }
            return true;
        }
        if(detailVisible())
        {
            int x = compact() ? r : detailX();
            int w = width - x;
            if(compact() && hit(mx, my, x, 0, 28, 59))
            {
                showCompactDetails = false;
                return true;
            }
            if(hit(mx, my, width - 105, 16, 92, 26))
            {
                Minecraft.getInstance().gui.setScreen(new LegacyClickGuiScreen(gui));
                return true;
            }
            List<Hack> hacks = filteredHacks();
            Hack current = selected(hacks);
            int inset = Math.max(12, Math.min(30, w / 14));
            int bubbleW = Math.min(280, Math.max(135, w - 2 * inset));
            int bubbleX = width - inset - bubbleW;
            if(hit(mx, my, bubbleX, 171, bubbleW, 76))
            {
                action(current);
                return true;
            }
            int shortcutsY = Math.max(336, height - 92);
            if(shortcutsY + 63 < height)
            {
                int itemW = Math.max(40, (w - 2 * inset - 18) / QUICK.length - 1);
                for(int i = 0; i < QUICK.length; i++)
                {
                    int bx = x + inset + i * (itemW + 6);
                    if(hit(mx, my, bx, shortcutsY + 19, itemW, 30))
                    {
                        action(QUICK[i]);
                        return true;
                    }
                }
            }
        }
        searchFocused = false;
        return super.mouseClicked(event, doubleClick);
    }

    @Override
    public boolean mouseScrolled(double x, double y, double horizontal, double vertical)
    {
        if(vertical == 0) return super.mouseScrolled(x, y, horizontal, vertical);
        if(x < railW())
        {
            int shown = Math.max(1, (height - 137) / 34);
            int max = Math.max(0, Category.values().length + 1 - shown);
            categoryOffset = Math.max(0, Math.min(max, categoryOffset + (vertical < 0 ? 1 : -1)));
            return true;
        }
        if(listVisible() && x < detailX())
        {
            int max = Math.max(0, filteredHacks().size() - visibleRows());
            listOffset = Math.max(0, Math.min(max, listOffset + (vertical < 0 ? 2 : -2)));
            return true;
        }
        return super.mouseScrolled(x, y, horizontal, vertical);
    }

    @Override
    public boolean charTyped(CharacterEvent event)
    {
        if(searchFocused && event.isAllowedChatCharacter() && searchQuery.length() < 48)
        {
            searchQuery += event.codepointAsString();
            listOffset = 0;
            selectedName = "";
            return true;
        }
        return super.charTyped(event);
    }

    @Override
    public boolean keyPressed(KeyEvent event)
    {
        if(searchFocused)
        {
            if(event.isEscape())
            {
                searchFocused = false;
                return true;
            }
            // SDL keycode 8 and legacy GLFW 259; both supported for portability.
            if(event.key() == 8 || event.key() == 259)
            {
                if(!searchQuery.isEmpty())
                {
                    searchQuery = searchQuery.substring(0, searchQuery.offsetByCodePoints(0,
                        searchQuery.codePointCount(0, searchQuery.length()) - 1));
                    listOffset = 0;
                    selectedName = "";
                }
                return true;
            }
            if(event.isConfirmation())
            {
                searchFocused = false;
                return true;
            }
        }
        return super.keyPressed(event);
    }

    @Override
    public void extractBackground(GuiGraphicsExtractor context, int mouseX, int mouseY, float deltaTicks)
    {
        // Render a solid app background; avoid a second costly blur pass.
    }
}
