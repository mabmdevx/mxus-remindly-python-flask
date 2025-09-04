#!/bin/bash
set -euo pipefail

# Usage function
usage() {
    echo "Usage: $0 -c <config_file>"
    echo "Example: $0 -c /etc/mysql_backups/project1.conf"
    exit 1
}

# Parse arguments
while getopts ":c:" opt; do
    case $opt in
        c) CONFIG_FILE="$OPTARG" ;;
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

# Load project config
# shellcheck disable=SC1090
source "$CONFIG_FILE"

# Validate required variables
: "${DB_USER:?DB_USER not set in config}"
: "${DB_PASS:?DB_PASS not set in config}"
: "${DB_NAME:?DB_NAME not set in config}"
: "${B2_BUCKET:?B2_BUCKET not set in config}"
: "${B2_PREFIX_PARENT:?B2_PREFIX_PARENT not set in config}"
: "${B2_PREFIX_DB_NAME:?B2_PREFIX_DB_NAME not set in config}"
: "${BACKUP_DIR_PARENT:?BACKUP_DIR_PARENT not set in config}"
: "${BACKUP_DIR_DB_NAME:?BACKUP_DIR_DB_NAME not set in config}"

# Derived variables
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="$BACKUP_DIR_PARENT/$BACKUP_DIR_DB_NAME/${DB_NAME}_${TIMESTAMP}.sql"
B2_FILE="$B2_PREFIX_PARENT/$B2_PREFIX_DB_NAME/${DB_NAME}_${TIMESTAMP}.sql"
BACKUP_FILE_LATEST_COPY="$BACKUP_DIR_PARENT/$BACKUP_DIR_DB_NAME/${DB_NAME}_latest.sql"

echo "Backing up database: $DB_NAME"
echo "Local backup file: $BACKUP_FILE"
echo "B2 destination: $B2_FILE"

# Ensure directories exist
mkdir -p "$BACKUP_DIR_PARENT/$BACKUP_DIR_DB_NAME"

# Dump the MySQL database
mysqldump -u"$DB_USER" -p"$DB_PASS" "$DB_NAME" > "$BACKUP_FILE"

# Update latest copy
rm -f "$BACKUP_FILE_LATEST_COPY"
cp "$BACKUP_FILE" "$BACKUP_FILE_LATEST_COPY"

# Upload backup to Backblaze B2
b2 upload-file "$B2_BUCKET" "$BACKUP_FILE" "$B2_FILE"

# Clean up local backup file (keep only latest copy)
rm "$BACKUP_FILE"

echo "Backup completed for $DB_NAME"
