# This Module is refile name to correcting standard file name directed by Wit
#!/bin/bash

cd "$(dirname "$0")/../pdf_data" || { echo "ไม่พบโฟลเดอร์ pdf_data"; exit 1; }
my_dir="$(pwd)"

# ตรวจสอบว่ามีโฟลเดอร์จริงไหม
[ -d "$my_dir" ] || { echo "โฟลเดอร์ไม่พบ: $my_dir"; exit 1; }

# loop ผ่านทุกไฟล์
for file in "$my_dir"/*; do
    # ตรวจสอบว่าชื่อไฟล์มี space
    if [[ "$file" == *" "* ]]; then
        new_name="${file// /_}"
        mv "$file" "$new_name"
        echo "change_name: '$file' → '$new_name'"
    fi
done
