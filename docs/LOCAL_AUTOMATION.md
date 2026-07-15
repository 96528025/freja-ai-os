# Local Daily Automation

Freja schedules one daily edition at `BRIEF_HOUR:BRIEF_MINUTE` in `TIMEZONE`. The current local configuration is 07:00 in `America/Los_Angeles`.

## Runtime behavior

- At the scheduled time, Freja generates only when the local date has no brief.
- APScheduler accepts a missed run for up to 24 hours when the process survives macOS sleep.
- On backend startup, Freja checks whether the scheduled time has passed and generates a missing edition.
- Manual generation remains available at any time.
- An in-process lock prevents scheduled and manual generation from running concurrently.
- Successful source snapshots are reused for the same local date and connector configuration.
- Failed collections are not treated as successful cache entries and can be retried.
- `POST /api/v1/briefs/generate?force_refresh=true` bypasses the daily source cache.

## macOS login service

The repository includes [`deploy/macos/com.freja.personal-ai-os.plist`](../deploy/macos/com.freja.personal-ai-os.plist). It starts the backend on login and restarts it if it exits.

It is intentionally not installed automatically during development because an existing terminal server may already own port 8000. After stopping the development backend, install it explicitly:

```bash
cp deploy/macos/com.freja.personal-ai-os.plist ~/Library/LaunchAgents/
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.freja.personal-ai-os.plist
```

Remove it with:

```bash
launchctl bootout gui/$(id -u) ~/Library/LaunchAgents/com.freja.personal-ai-os.plist
rm ~/Library/LaunchAgents/com.freja.personal-ai-os.plist
```

The Mac and authenticated Chrome/OpenCLI session must still be available for Reddit and Rednote collection. If the Mac was off, the startup catch-up runs after the next login.
