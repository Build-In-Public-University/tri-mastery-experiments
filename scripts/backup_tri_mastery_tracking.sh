#!/usr/bin/env bash
set -euo pipefail
REMOTE=${TRI_MASTERY_BACKUP_REMOTE:-arc-vps}
REMOTE_RAW=${TRI_MASTERY_REMOTE_RAW:-/opt/tri-mastery-tracking/data/raw_visit_events.jsonl}
LOCAL_ROOT=${TRI_MASTERY_BACKUP_ROOT:-artifacts/tracking-backups}
STAMP=$(date -u +%Y%m%dT%H%M%SZ)
DEST="$LOCAL_ROOT/$STAMP"
mkdir -p "$DEST"
ssh "$REMOTE" "test -f '$REMOTE_RAW' && sha256sum '$REMOTE_RAW' && wc -l '$REMOTE_RAW'" > "$DEST/remote_receipt.txt"
rsync -az "$REMOTE:$REMOTE_RAW" "$DEST/raw_visit_events.jsonl"
LOCAL_SHA=$(sha256sum "$DEST/raw_visit_events.jsonl" | awk '{print $1}')
REMOTE_SHA=$(awk 'NR==1 {print $1}' "$DEST/remote_receipt.txt")
REMOTE_LINES=$(awk 'NR==2 {print $1}' "$DEST/remote_receipt.txt")
if [ "$LOCAL_SHA" != "$REMOTE_SHA" ]; then
  echo "backup hash mismatch: remote=$REMOTE_SHA local=$LOCAL_SHA" >&2
  exit 1
fi
python3 - <<PY
import json
from datetime import datetime, timezone
from pathlib import Path
manifest={
  'artifact':'tri_mastery_tracking_raw_backup',
  'created_at_utc':datetime.now(timezone.utc).isoformat(),
  'remote':'$REMOTE:$REMOTE_RAW',
  'local_path':'$DEST/raw_visit_events.jsonl',
  'sha256':'$LOCAL_SHA',
  'line_count':int('$REMOTE_LINES'),
  'status':'ok_hash_matched'
}
Path('$DEST/manifest.json').write_text(json.dumps(manifest, indent=2, sort_keys=True)+'\n')
latest=Path('$LOCAL_ROOT/latest.json')
latest.write_text(json.dumps(manifest, indent=2, sort_keys=True)+'\n')
print(json.dumps(manifest, sort_keys=True))
PY
