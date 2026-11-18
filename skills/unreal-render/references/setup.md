# First-time setup: a Windows PC for headless Unreal

Who does what: **the PC's owner** installs software, signs in, accepts licences and gets content, at the PC. Claude gives the steps and checks each result read-only (`recruit.sh probe`, `ue-remote.sh check`). Nothing here is downloaded, bought or signed into by the agent.

## 1. Recruit the PC

Use the **gpu-job** skill's recruiting guide (`references/recruit.md` there, and `scripts/recruit.sh`): it puts the PC on Tailscale and gives it an SSH key login. Then `recruit.sh probe <user>@<pc>` must report the GPU and `READY`.

Without that skill, the Windows essentials (PowerShell as Administrator, by the owner):

```powershell
Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0
Start-Service sshd; Set-Service sshd -StartupType Automatic
# your public key: a standard user puts it in C:\Users\<user>\.ssh\authorized_keys (recommended: run Unreal jobs as a
# standard, non-administrator account, so a script gone wrong cannot change the system);
# an administrator account must use this file instead, owned by Administrators and SYSTEM only:
Add-Content C:\ProgramData\ssh\administrators_authorized_keys '<the .pub line>'
icacls C:\ProgramData\ssh\administrators_authorized_keys /inheritance:r /grant "*S-1-5-32-544:F" /grant "*S-1-5-18:F"
```

The SIDs (`*S-1-5-32-544` Administrators, `*S-1-5-18` SYSTEM) work on any Windows language. The default SSH shell is `cmd`; `ue-remote.sh` always calls `powershell` itself (inline PowerShell goes as `-EncodedCommand`, so cmd never reads it), so either default works. Check: `ssh -o BatchMode=yes <pc> "echo ok"` prints `ok` with no password prompt.

**Keep it awake** while it renders (Settings → System → Power: never sleep when plugged in), or a sleeping PC drops the job.

## 2. Can it carry Unreal?

| Need | Comfortable | Notes |
|---|---|---|
| GPU | RTX 3070 / 8 GB for 1080p stills | 12 GB+ for dense scenes, Lumen at high settings, or 4K |
| Driver | a current Studio or Game Ready driver | `nvidia-smi` must answer over SSH |
| Disk | engine ~60 GB, a large sample project ~100 GB, renders tens of GB | put projects on a second drive; the launcher downloads to C: first |
| RAM | 32 GB | 64 GB for large World Partition maps |

`ue-remote.sh check` reports the GPU, free space per drive and whether Unreal is already running.

## 3. Unreal and the plugins (the owner, at the PC)

1. Install the **Epic Games Launcher** and sign in with their Epic account.
2. Launcher → Unreal Engine → Library → install **UE 5.x** (the version the project or sample needs).
3. Create or add the project. For a Fab or Marketplace sample, see [fab-content.md](fab-content.md).
4. Open the project once in the editor (first-time shader compiles can take an hour) and enable, under Edit → Plugins: **Python Editor Script Plugin**, **Editor Scripting Utilities**, **Movie Render Pipeline**. Restart the editor when asked, then close it.
5. For exposure in EV100 numbers, add to the project's `Config/DefaultEngine.ini` under `[/Script/Engine.RendererSettings]`:
   ```ini
   r.DefaultFeature.AutoExposure.ExtendDefaultLuminanceRange=True
   ```
   Without it the exposure fields are luminance and a sunlit scene comes out white.

Headless runs need no desktop session after this, but the first open, plugin prompts and the launcher do.

## 4. The work folder and ue.json

Pick a work folder on the PC with no spaces in its path, e.g. `C:/Users/<you>/ue-work`. Here:

```sh
export UR_HOST=<ssh alias or user@pc> UR_WORK=C:/Users/<you>/ue-work
<skill>/scripts/ue-remote.sh setup
```

Then put `ue.json` in the work folder (the owner can write it, or copy one over with `scp`):

```json
{
  "engine": "C:/Program Files/Epic Games/UE_5.x",
  "project": "D:/Unreal/MyProject/MyProject.uproject",
  "renders": "D:/Unreal/Renders"
}
```

`ue-remote.sh check` should now list the engine version, the project, the three plugins as enabled, the exposure setting, the GPU, the drives, and "no Unreal process running".

## 5. Optional: Cesium for Unreal (a real place under the scene)

- The owner installs **Cesium for Unreal** from Fab into the engine and enables it in the project.
- A **Cesium ion** account gives an access token. Keep it in a file on the PC **outside every repository** (e.g. `C:/Users/<you>/keys/cesium-ion.txt`) and pass that path in the build's arguments; `ue/cesium.py` reads it. The token is stored inside the saved level, so never share that project.
- **Licences and terms (checked when this was written; read the current pages before relying on them):**
  - **Cesium ion's Community (free) plan** is for personal and non-commercial use (exploratory evaluation and unfunded education are allowed). A company with more than $50K in annual gross revenue or more than $50K raised needs a paid plan (Commercial, from $149/month for an individual), as do government and funded-research projects. It includes 1,000 Google Photorealistic 3D Tiles root tiles a month. https://cesium.com/platform/cesium-ion/pricing/
  - **Google Photorealistic 3D Tiles** (through Cesium ion or your own Google Cloud key, which needs billing linked) require attribution wherever they are shown: the Google Maps logo, not obscured, and the tiles' data credits aggregated on one line (Cesium: show credits on screen). Google's policies also say not to create content based on Google Maps Content, allow promotional videos of at most 30 seconds marked "for promotional purposes only", and list offline uses among prohibited ones. **Offline frames of the tiles shown on a website may therefore not be allowed at all**: that is the user's call, after reading https://developers.google.com/maps/documentation/tile/policies. Building the scene from your own and Fab geometry avoids the question.
- Google's tiles are photographs with the daylight baked in: they suit daytime far horizons; at night they render black and a lit city has to come from your own geometry.
