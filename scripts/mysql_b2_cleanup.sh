#!/bin/bash
set -euo pipefail

# Usage
usage() {
    echo "Usage: $0 -c <config_file> [-d <days>]"
    echo "Example: $0 -c /etc/mysql_backups/project1.conf -d 30"
    exit 1
}

# Defaults
DAYS_OLD=30

# Parse arguments
while getopts ":c:d:" opt; do
    case $opt in
        c) CONFIG_FILE="$OPTARG" ;;
        d) DAYS_OLD="$OPTARG" ;;
        *) usage ;;
    esac
done

if [ -z "${CONFIG_FILE:-}" ]; then
    usage
fi

if [ ! -f "$CONFIG_FILE" ]; then
    echo "Error: Config file not found: $CONFIG_FILE"
    exit 1
fi

# Load config
# shellcheck disable=SC1090
source "$CONFIG_FILE"

# Validate required variables
: "${B2_BUCKET:?B2_BUCKET not set in config}"
: "${B2_PREFIX_PARENT:?B2_PREFIX_PARENT not set in config}"
: "${B2_PREFIX_DB_NAME:?B2_PREFIX_DB_NAME not set in config}"

# Derived variable
B2_PREFIX="$B2_PREFIX_PARENT/$B2_PREFIX_DB_NAME"

# Calculate the timestamp for deletion cutoff
THRESHOLD_DATE=$(date -d "$DAYS_OLD days ago" +"%s")
echo "Deleting files older than $DAYS_OLD days ($THRESHOLD_DATE) from B2 bucket $B2_BUCKET/$B2_PREFIX"

# List files in the bucket
FILES=$(b2 ls "b2://$B2_BUCKET/$B2_PREFIX/" | awk '{print $NF}')  # Only get file names

# Loop through each file
for FILE in $FILES; do
    FILE_URI="b2://$B2_BUCKET/$FILE"
    echo "Checking file: $FILE_URI"

    # Get file info
    FILE_INFO_JSON=$(b2 file info "$FILE_URI")
    
    # Extract modification date in seconds
    MODIFICATION_MILLIS=$(echo "$FILE_INFO_JSON" | jq -r '.fileInfo.src_last_modified_millis // .uploadTimestamp')
    MODIFICATION_DATE=$((MODIFICATION_MILLIS / 1000))
    echo "Modification date (epoch): $MODIFICATION_DATE"

    # Delete if older than threshold
    if [ "$MODIFICATION_DATE" -lt "$THRESHOLD_DATE" ]; then
        b2 rm "$FILE_URI"
        echo "Deleted file: $FILE_URI"
    fi
done

echo "Cleanup completed"
