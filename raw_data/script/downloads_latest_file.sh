#!/usr/bin/env bash
set -euo pipefail

SRC="$HOME/Downloads"
DST="$(pwd)"

mkdir -p -- "$DST"

# วันที่วันนี้ (รูปแบบ YYYY-MM-DD)
today=$(date +%F)

moved=false

# ไล่เช็คไฟล์ทั้งหมดใน Downloads
for f in "$SRC"/*.pdf; do
  [[ -f "$f" ]] || continue   # ข้ามถ้าไม่ใช่ไฟล์ปกติ

  # เอา mtime ของไฟล์นี้มาเป็น YYYY-MM-DD
  fdate=$(date -r "$f" +%F)

  if [[ "$fdate" == "$today" ]]; then
    mv -- "$f" "$DST"/
    echo "ย้าย: $(basename -- "$f") -> $DST"
    moved=true
  fi
done

if [[ "$moved" == false ]]; then
  echo "ไม่พบไฟล์ที่โหลดวันนี้ใน: $SRC"
fi
