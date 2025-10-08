#!/bin/bash
# Usage: ./rename_dir.sh old_directory new_directory [--dry-run] [--verbose]
#
# This script renames a directory from old_directory to new_directory.
# Then, it recursively renames any file or directory (within new_directory)
# whose name contains the old directory name by replacing that substring
# with the new directory name.

set -euo pipefail  # Exit on error, undefined vars, pipe failures

# Color output for better readability
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default options
DRY_RUN=false
VERBOSE=false

# Parse arguments
POSITIONAL_ARGS=()
while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run|-n)
            DRY_RUN=true
            shift
            ;;
        --verbose|-v)
            VERBOSE=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 old_directory new_directory [OPTIONS]"
            echo ""
            echo "This script renames a directory and recursively updates all files/directories"
            echo "within it that contain the old directory name."
            echo ""
            echo "Options:"
            echo "  --dry-run, -n    Show what would be renamed without making changes"
            echo "  --verbose, -v    Show detailed output"
            echo "  --help, -h       Show this help message"
            exit 0
            ;;
        -*)
            echo -e "${RED}Error: Unknown option $1${NC}"
            exit 1
            ;;
        *)
            POSITIONAL_ARGS+=("$1")
            shift
            ;;
    esac
done

set -- "${POSITIONAL_ARGS[@]}"

# Validate argument count
if [ "$#" -ne 2 ]; then
    echo -e "${RED}Error: Expected exactly 2 arguments, got $#${NC}"
    echo "Usage: $0 old_directory new_directory [OPTIONS]"
    echo "Use --help for more information"
    exit 1
fi

OLD_DIR="$1"
NEW_DIR="$2"

# Remove trailing slashes for consistency
OLD_DIR="${OLD_DIR%/}"
NEW_DIR="${NEW_DIR%/}"

# Extract base names for pattern matching
OLD_BASE=$(basename "$OLD_DIR")
NEW_BASE=$(basename "$NEW_DIR")

# Validation checks
if [ ! -d "$OLD_DIR" ]; then
    echo -e "${RED}Error: Directory '$OLD_DIR' does not exist.${NC}"
    exit 1
fi

if [ -e "$NEW_DIR" ]; then
    echo -e "${RED}Error: Target '$NEW_DIR' already exists.${NC}"
    exit 1
fi

if [ -z "$NEW_BASE" ]; then
    echo -e "${RED}Error: New directory name cannot be empty.${NC}"
    exit 1
fi

if [[ "$NEW_BASE" == */* ]]; then
    echo -e "${RED}Error: New directory name cannot contain slashes.${NC}"
    exit 1
fi

# Check if old and new names are the same
if [ "$OLD_BASE" = "$NEW_BASE" ]; then
    echo -e "${YELLOW}Warning: Old and new directory names are identical. No renaming needed.${NC}"
    exit 0
fi

# Display summary
echo -e "${BLUE}=== Directory Rename Operation ===${NC}"
echo -e "Old directory: ${YELLOW}$OLD_DIR${NC}"
echo -e "New directory: ${YELLOW}$NEW_DIR${NC}"
echo -e "Pattern to replace: ${YELLOW}$OLD_BASE${NC} → ${YELLOW}$NEW_BASE${NC}"
if $DRY_RUN; then
    echo -e "${YELLOW}DRY RUN MODE: No changes will be made${NC}"
fi
echo ""

# Count items to be renamed
item_count=$(find "$OLD_DIR" -depth -name "*$OLD_BASE*" 2>/dev/null | wc -l)
echo -e "Found ${GREEN}$item_count${NC} items to rename inside the directory"
echo ""

# Confirm operation unless dry run
if ! $DRY_RUN; then
    read -p "Proceed with renaming? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}Operation cancelled.${NC}"
        exit 0
    fi
fi

# Rename the main directory
if $DRY_RUN; then
    echo -e "${BLUE}[DRY RUN]${NC} Would rename: '$OLD_DIR' → '$NEW_DIR'"
else
    mv "$OLD_DIR" "$NEW_DIR"
    echo -e "${GREEN}✓${NC} Renamed directory: '$OLD_DIR' → '$NEW_DIR'"
fi

# Change to new directory
if ! $DRY_RUN; then
    cd "$NEW_DIR" || exit 1
else
    cd "$OLD_DIR" || exit 1
fi

# Process files and directories
rename_count=0
error_count=0

# Use process substitution to avoid subshell issues with counters
while IFS= read -r path; do
    parent_dir=$(dirname "$path")
    base_name=$(basename "$path")
    
    # Replace all occurrences of OLD_BASE in the basename with NEW_BASE
    new_base_name="${base_name//$OLD_BASE/$NEW_BASE}"
    
    # Skip if no change needed
    if [ "$base_name" = "$new_base_name" ]; then
        continue
    fi
    
    new_path="$parent_dir/$new_base_name"
    
    if $VERBOSE || $DRY_RUN; then
        echo "  $path → $new_path"
    fi
    
    if ! $DRY_RUN; then
        if mv "$path" "$new_path" 2>/dev/null; then
            ((rename_count++))
        else
            echo -e "${RED}Error renaming: $path${NC}"
            ((error_count++))
        fi
    else
        ((rename_count++))
    fi
done < <(find . -depth -name "*$OLD_BASE*" 2>/dev/null)

cd - > /dev/null || exit 1

# Summary
echo ""
echo -e "${BLUE}=== Summary ===${NC}"
if $DRY_RUN; then
    echo -e "Would rename ${GREEN}$rename_count${NC} items"
else
    echo -e "Successfully renamed ${GREEN}$rename_count${NC} items"
    if [ $error_count -gt 0 ]; then
        echo -e "${RED}Encountered $error_count errors${NC}"
        exit 1
    fi
fi
echo -e "${GREEN}Operation completed successfully!${NC}"
