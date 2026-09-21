# I3S branding: supported, upgrade-safe approach

The running Open WebUI environment has `WEBUI_NAME=I3S`, which supplies the application name. Open WebUI 0.11.3 should be configured through its Admin Panel branding/appearance controls and supported environment variables/static asset mounts, not by editing bundled frontend source or SQLite.

Prepare approved assets outside source control: `logo.png`, `favicon.ico`, and the company-selected wallpaper. Mount/copy only the approved logo/favicon using the build's documented static asset mechanism after confirming the exact 0.11.3 admin UI options. Set the global dark/navy default and login background there if exposed. Existing users may retain per-user appearance preferences; do not overwrite their database records.

Wallpaper is pending the user-provided local path. No wallpaper was copied or generated. Rollback is to remove the asset mount or restore the prior Admin Panel branding value, then restart only Open WebUI after a backup.
