#!/bin/bash

# Script to bump version, update manifest, create git tag and commit

set -e  # Exit on error

# Check if version argument is provided
if [ -z "$1" ]; then
    echo "Usage: $0 <version>"
    echo "Example: $0 0.2.0"
    exit 1
fi

VERSION=$1
MANIFEST_PATH="custom_components/ultrahuman/manifest.json"

# Validate version format (basic check: should be X.Y.Z)
if ! [[ "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo "Error: Version must be in format X.Y.Z (e.g., 0.2.0)"
    exit 1
fi

# Check if manifest file exists
if [ ! -f "$MANIFEST_PATH" ]; then
    echo "Error: Manifest file not found at $MANIFEST_PATH"
    exit 1
fi

# Check if git repository is clean (optional - comment out if you want to allow uncommitted changes)
if ! git diff-index --quiet HEAD --; then
    echo "Warning: You have uncommitted changes. Consider committing them first."
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Update version in manifest.json
echo "Updating version in $MANIFEST_PATH to $VERSION..."
if command -v jq &> /dev/null; then
    # Use jq if available (more robust)
    jq ".version = \"$VERSION\"" "$MANIFEST_PATH" > "${MANIFEST_PATH}.tmp" && mv "${MANIFEST_PATH}.tmp" "$MANIFEST_PATH"
else
    # Fallback to sed if jq is not available
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "s/\"version\": \".*\"/\"version\": \"$VERSION\"/" "$MANIFEST_PATH"
    else
        # Linux
        sed -i "s/\"version\": \".*\"/\"version\": \"$VERSION\"/" "$MANIFEST_PATH"
    fi
fi

# Verify the version was updated
CURRENT_VERSION=$(grep -o '"version": "[^"]*"' "$MANIFEST_PATH" | cut -d'"' -f4)
if [ "$CURRENT_VERSION" != "$VERSION" ]; then
    echo "Error: Failed to update version in manifest.json"
    exit 1
fi

echo "Version updated successfully to $VERSION"

# Stage the manifest file
git add "$MANIFEST_PATH"

# Commit with version as message
echo "Committing changes..."
git commit -m "$VERSION"

# Create git tag
TAG="v$VERSION"
echo "Creating git tag $TAG..."
git tag "$TAG"

echo ""
echo "✓ Version bumped to $VERSION"
echo "✓ Changes committed"
echo "✓ Tag $TAG created"
echo ""
echo "Next steps:"
echo "  git push origin main"
echo "  git push origin $TAG"
echo ""
echo "Or push both at once:"
echo "  git push origin main --tags"

