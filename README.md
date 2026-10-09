# Nova Chat Client — WhatsApp-inspired Minecraft Fabric interface

**A custom green-and-dark Minecraft client interface built on the open-source Wurst 7 engine.**

> This is **not WhatsApp**, isn't associated with WhatsApp/Meta, and is not an official Wurst release.
> It is a **GPL-3.0-or-later derivative** of Wurst 7 with a separately designed module menu.

## What you get

- An original **WhatsApp-inspired dark UI**: dark navigation rail, conversation-style module list, status indicators, green control bubbles, subtle wallpaper, and an original green `N` icon.
- **F9** is the default menu binding on **fresh installations**.
- Full upstream Wurst 7 module engine (Flight, Killaura, Freecam, X-Ray, etc.); Nova Chat does not invent fake replacements for the original features.
- Search the available modules by typing in the search area; filter categories with the sidebar; scroll through the list.
- Click a module in the list to open its details, then click its action bubble to enable, disable, or trigger it.
- A **SETTINGS >** button opens Wurst's original detailed settings UI, kept for compatibility with all upstream settings.
- Responsive compact navigation on narrow Minecraft GUI scales; a separate left rail provides category browsing.
- A custom mod display name and icon; internal Fabric mod id stays `wurst` because Wurst's mixins, storage, and compatibility may depend on it.

## How to build an installable `.jar` with GitHub (recommended)

1. Create a **public GitHub repository** and upload **the contents of this ZIP** into its root (not the ZIP as one file).
2. Under your repository's **Actions** tab, enable workflows if prompted, then select **Build Nova Chat Fabric Client** and choose **Run workflow**. Pushing to `main` also triggers a build.
3. The workflow tests the patch, clones the official [Wurst 7 source](https://github.com/Wurst-Imperium/Wurst7) from the `26.3` branch, applies the customized UI, uses **Java 25** to build, and refuses to package a JAR missing the Nova Chat UI and license requirements.
4. Once the workflow **succeeds**, download the **Nova-Chat-Fabric-26.3** artifact. It contains `Nova-Chat-Fabric-26.3.jar`, a SHA-256 checksum file, build provenance, and a ZIP of the corresponding GPL source.
5. Keep the corresponding source if redistributing the client. Source is additionally uploaded as the **Nova-Chat-Corresponding-Source** workflow artifact.

**A successful GitHub build is required.** This ZIP is a source/build project; it does not contain a precompiled mod JAR. The client has not been launched in Minecraft or Lunar in this environment.

## Manual local build

Prerequisites: Git, Python 3.12+, **JDK 25**, an internet connection for Gradle/Minecraft dependencies.

```sh
git clone --depth 1 --branch 26.3 https://github.com/Wurst-Imperium/Wurst7.git upstream
python scripts/verify_upstream.py upstream
python scripts/apply_nova.py upstream
cd upstream
./gradlew build --no-daemon
cd ..
python scripts/package_release.py upstream nova-dist
```

For Windows, run `upstream\gradlew.bat build` from the `upstream` directory rather than `./gradlew`.

## Install in Minecraft / Lunar

- Create or select a **Minecraft Java 26.3 + Fabric Loader** installation, with a compatible **Fabric API** version.
- Place the resulting `Nova-Chat-Fabric-26.3.jar` into the installation's `mods` folder.
- **Remove normal Wurst** if it is installed. Nova Chat and Wurst use the same internal mod id, `wurst`, and are not designed to be installed together.
- Launch the game and press **F9** to open the Nova Chat menu. Existing Wurst keybind configuration may override the default; if needed, use Wurst's `.binds add f9 ClickGUI` command.
- Lunar Client custom-mod loading and your Fabric version **must match**, and a custom Lunar profile may still reject some third-party mods. This has not been verified on a Lunar installation.

### Using your own Aternos server

This is a **client-side Fabric mod**. Aternos doesn't need this JAR installed just to connect. Your Minecraft client and the server must be protocol/version compatible. Features such as flight can be limited by the server's movement checks or `allow-flight` configuration; because it's your server, configure them using the Aternos administration panel rather than attempting to bypass checks. Some features may not work on server versions/plugins that block their behavior. **No anti-cheat-bypass guarantee.**

## What has actually been checked

Run locally:

```sh
python -m unittest discover -s tests -v
```

- **26 unit/integration tests** pass on the packaged source. They cover upstream-version and license preflight, the exact code patch, metadata and custom icon, code structure, and remapped artifact validation.
- The Java UI code has also been compiled and interacted with in a test using **stand-in classes**, covering search, typing/backspace, activating an actual module action delegate, advanced-settings navigation, and the narrow-view flow (**11 Java harness assertions**).
- This **does not** demonstrate compilation against Wurst/Minecraft APIs or in-game performance. Only a successful Java 25 Fabric/Gradle build does that; the workflow is supplied but has not been run in this environment.

## Licensing and attribution

Wurst 7 source is GPL-3.0-or-later, copyright Wurst-Imperium and contributors. The adapted menu code, logo, scripts, and documentation in this kit are also GPL-3.0-or-later. The build includes Wurst's original license, authors, and a `NOVA-ATTRIBUTION.md` explanation. No Wurst binaries are bundled here; the official upstream code is downloaded during the GitHub build. Nova Chat is not sponsored, approved, or endorsed by Wurst-Imperium, WhatsApp, or Meta.
