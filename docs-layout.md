# Nova Chat — Interface specification

The client uses a **WhatsApp-inspired dark messenger visual language**, without copying the WhatsApp logo, name, login, or network service.

## Visual tokens

| Area | Hex | Purpose |
| --- | --- | --- |
| Wallpaper | `#0B141A` | Conversation background |
| Rail/Header | `#202C33` | Frame and navigation |
| Chat list | `#111B21` | Modules as contacts |
| Hover | `#26353D` | Hover state |
| Selected row | `#2A3942` | Current module |
| Brand green | `#00A884` | Active accents |
| Green bubble | `#005C4B` | Action controls |
| Primary | `#E9EDEF` | Names/text |
| Secondary | `#8696A0` | Descriptions |

## Interaction

- **F9**: open/toggle the module interface (default on first install).
- **Category rail**: change category; mouse wheel scrolls categories when needed.
- **Search box**: click, type; Backspace to erase, Escape/Enter to blur. Click `X` to clear.
- **Chat rows**: select a feature; current status is always visible.
- **Green bubble**: invoke the actual upstream primary module action.
- **Pinned shortcuts**: Flight, Killaura, Freecam, X-Ray (when there's enough vertical room).
- **SETTINGS >**: opens the original Wurst advanced configuration GUI.
- **Compact mode (<620 GUI width)**: show either chats or module details; back arrow returns to chats.

All core module logic, keybind persistence, and advanced options stay with Wurst. The menu is not a real chat network; no message is transmitted to anyone.
