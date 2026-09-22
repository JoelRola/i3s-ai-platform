# Restore and rollback

Create and checksum a backup before every restore. A restore is disruptive and must be approved for the target environment.

1. Stop only Open WebUI: `docker stop open-webui`.
2. Verify the archive before use: `sha256sum -c open-webui-data-<timestamp>.tar.gz.sha256` and `tar -tzf open-webui-data-<timestamp>.tar.gz >/dev/null`.
3. Preserve the current volume as a separate timestamped archive. Do not overwrite it.
4. Restore into the existing `open-webui` volume with a short-lived helper container: `docker run --rm -v open-webui:/target -v "$PWD":/backup alpine:3.20 sh -c 'rm -rf /target/* /target/.[!.]* /target/..?*; tar -C /target -xzf /backup/open-webui-data-<timestamp>.tar.gz'`.
5. Start `open-webui`, wait for `docker inspect -f '{{.State.Health.Status}}' open-webui` to be `healthy`, then check `curl -fsS http://127.0.0.1:8080/health`.

Never perform this destructive restore procedure as a production test. The source-host V1 backup path and checksum are recorded in the final freeze report.
