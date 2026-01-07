# Apply Database Migration - Add CASCADE DELETE
# This script applies the cascade delete migration to your PostgreSQL database

Write-Host "🔧 Applying CASCADE DELETE migration..." -ForegroundColor Cyan
Write-Host ""

# Database connection details from docker-compose
$DB_HOST = "localhost"
$DB_PORT = "5433"  # postgres_credentials port
$DB_NAME = "data"
$DB_USER = "postgres"
$DB_PASSWORD = "example"

# Migration file
$MIGRATION_FILE = "migrations\001_add_cascade_delete.sql"

Write-Host "📋 Migration Details:" -ForegroundColor Yellow
Write-Host "   Database: $DB_NAME"
Write-Host "   Host: ${DB_HOST}:${DB_PORT}"
Write-Host "   User: $DB_USER"
Write-Host "   File: $MIGRATION_FILE"
Write-Host ""

# Check if migration file exists
if (-not (Test-Path $MIGRATION_FILE)) {
    Write-Host "❌ ERROR: Migration file not found: $MIGRATION_FILE" -ForegroundColor Red
    exit 1
}

Write-Host "🔍 Checking Docker container status..." -ForegroundColor Cyan
$container = docker ps --filter "name=postgres_credentials" --format "{{.Names}}" 2>$null

if ($container) {
    Write-Host "✅ Found container: $container" -ForegroundColor Green
    Write-Host ""
    
    # Option 1: Apply via Docker exec (recommended if container is running)
    Write-Host "🚀 Applying migration via Docker..." -ForegroundColor Cyan
    
    $env:PGPASSWORD = $DB_PASSWORD
    Get-Content $MIGRATION_FILE | docker exec -i $container psql -U $DB_USER -d $DB_NAME
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "✅ Migration applied successfully!" -ForegroundColor Green
        Write-Host ""
        Write-Host "📝 Next steps:" -ForegroundColor Yellow
        Write-Host "   1. Restart your Python application to pick up the model change"
        Write-Host "   2. Test deletion: purchases with items will now auto-delete children"
        Write-Host "   3. No more manual item deletion required!"
    } else {
        Write-Host ""
        Write-Host "❌ Migration failed!" -ForegroundColor Red
        Write-Host "Check the error messages above." -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "⚠️  Docker container not found or not running" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "📋 Manual application instructions:" -ForegroundColor Cyan
    Write-Host "   1. Ensure PostgreSQL container is running:"
    Write-Host "      docker-compose -f docker-compose.debug.yml up -d postgres_credentials"
    Write-Host ""
    Write-Host "   2. Apply migration manually:"
    Write-Host "      docker exec -i <container_name> psql -U postgres -d data < $MIGRATION_FILE"
    Write-Host ""
    Write-Host "   OR use psql directly if you have it installed:"
    Write-Host "      set PGPASSWORD=$DB_PASSWORD"
    Write-Host "      psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -f $MIGRATION_FILE"
}

Write-Host ""
Write-Host "📖 For more details, see: FIX_CASCADE_DELETE.md" -ForegroundColor Cyan
