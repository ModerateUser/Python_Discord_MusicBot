# ============================================
# Delete Redundant Documentation Files
# ============================================
# This script removes old documentation files that are no longer needed
# Run this from the root of your Python_Discord_MusicBot repository

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Documentation Cleanup Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# List of files to delete
$files = @(
    "BUG_FIXES_SUMMARY.md",
    "CHANGELOG.md",
    "config.example.json",
    "FEATURES_GUIDE.md",
    "GUI_FIXES_SUMMARY.md",
    "IMPLEMENTATION_SUMMARY.md",
    "NATURAL_LANGUAGE_GUIDE.md",
    "REFACTORING_SUMMARY.md",
    "SECURITY.md",
    "UPGRADE_GUIDE.md"
)

Write-Host "Files to delete:" -ForegroundColor Yellow
foreach ($file in $files) {
    Write-Host "  - $file" -ForegroundColor Gray
}
Write-Host ""

# Confirm deletion
$confirmation = Read-Host "Do you want to delete these files? (yes/no)"
if ($confirmation -ne "yes") {
    Write-Host "Operation cancelled." -ForegroundColor Red
    exit
}

Write-Host ""
Write-Host "Deleting files..." -ForegroundColor Cyan

$deletedCount = 0
$notFoundCount = 0

foreach ($file in $files) {
    if (Test-Path $file) {
        try {
            Remove-Item $file -Force
            Write-Host "[✓] Deleted: $file" -ForegroundColor Green
            $deletedCount++
        } catch {
            Write-Host "[✗] Error deleting: $file - $_" -ForegroundColor Red
        }
    } else {
        Write-Host "[!] Not found: $file" -ForegroundColor Yellow
        $notFoundCount++
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Summary:" -ForegroundColor Cyan
Write-Host "  Deleted: $deletedCount files" -ForegroundColor Green
Write-Host "  Not found: $notFoundCount files" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Ask if user wants to commit and push
if ($deletedCount -gt 0) {
    $gitCommit = Read-Host "Do you want to commit and push these changes to GitHub? (yes/no)"
    
    if ($gitCommit -eq "yes") {
        Write-Host ""
        Write-Host "Committing changes..." -ForegroundColor Cyan
        
        try {
            # Stage all deletions
            git add -A
            
            # Commit
            git commit -m "Remove redundant documentation files"
            
            # Push to main branch
            git push origin main
            
            Write-Host ""
            Write-Host "[✓] Changes committed and pushed successfully!" -ForegroundColor Green
        } catch {
            Write-Host ""
            Write-Host "[✗] Error with git operations: $_" -ForegroundColor Red
            Write-Host "You may need to commit and push manually." -ForegroundColor Yellow
        }
    } else {
        Write-Host ""
        Write-Host "Files deleted locally but not committed." -ForegroundColor Yellow
        Write-Host "To commit manually, run:" -ForegroundColor Cyan
        Write-Host "  git add -A" -ForegroundColor Gray
        Write-Host "  git commit -m 'Remove redundant documentation files'" -ForegroundColor Gray
        Write-Host "  git push origin main" -ForegroundColor Gray
    }
}

Write-Host ""
Write-Host "Done!" -ForegroundColor Green
Write-Host ""
