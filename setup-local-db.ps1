# PostgreSQL Local Setup Script for Windows
# Run as Administrator in PowerShell

$POSTGRES_USER = "sports_league_owner"
$POSTGRES_PASSWORD = "sports_league_password"
$POSTGRES_DB = "sports_league"
$POSTGRES_HOST = "localhost"
$POSTGRES_PORT = "5432"

# Path to psql executable
$PSQL_PATH = "C:\Program Files\PostgreSQL\18\bin\psql.exe"

Write-Host "Setting up PostgreSQL locally..." -ForegroundColor Green

# Step 1: Create the role (user)
Write-Host "`nStep 1: Creating PostgreSQL role '$POSTGRES_USER'..." -ForegroundColor Yellow
$createRoleSQL = @"
DO `$`$ 
BEGIN 
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = '$POSTGRES_USER') THEN 
        CREATE ROLE $POSTGRES_USER WITH LOGIN PASSWORD '$POSTGRES_PASSWORD' CREATEDB;
    END IF;
END `$`$;
"@

& $PSQL_PATH -U postgres -h $POSTGRES_HOST -p $POSTGRES_PORT -c $createRoleSQL
if ($LASTEXITCODE -eq 0) {
    Write-Host "[OK] Role created successfully" -ForegroundColor Green
} else {
    Write-Host "[ERROR] Failed to create role" -ForegroundColor Red
    exit 1
}

# Step 2: Create the database
Write-Host "`nStep 2: Creating database '$POSTGRES_DB'..." -ForegroundColor Yellow
& $PSQL_PATH -U postgres -h $POSTGRES_HOST -p $POSTGRES_PORT -c "CREATE DATABASE `"$POSTGRES_DB`" OWNER $POSTGRES_USER;"
if ($LASTEXITCODE -eq 0) {
    Write-Host "[OK] Database created successfully" -ForegroundColor Green
} else {
    Write-Host "Database may already exist (that's okay)" -ForegroundColor Cyan
}

# Step 3: Load schema
Write-Host "`nStep 3: Loading schema..." -ForegroundColor Yellow
$schemaPath = Join-Path (Get-Location) "schema.sql"
if (Test-Path $schemaPath) {
    & $PSQL_PATH -U $POSTGRES_USER -h $POSTGRES_HOST -p $POSTGRES_PORT -d $POSTGRES_DB -f $schemaPath
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] Schema loaded successfully" -ForegroundColor Green
    } else {
        Write-Host "[ERROR] Failed to load schema" -ForegroundColor Red
    }
} else {
    Write-Host "[ERROR] schema.sql not found" -ForegroundColor Red
}

Write-Host "`n[OK] Setup complete!" -ForegroundColor Green
Write-Host "Connection string: postgresql://$POSTGRES_USER`:$POSTGRES_PASSWORD@$POSTGRES_HOST`:$POSTGRES_PORT/$POSTGRES_DB" -ForegroundColor Cyan
