# Alembic Migration Usage

## Quick Start

Since Alembic is installed but not in your PATH, use one of these methods:

### Method 1: Use the helper script (PowerShell)
```powershell
.\alembic.ps1 revision --autogenerate -m "Description"
.\alembic.ps1 upgrade head
.\alembic.ps1 downgrade -1
```

### Method 2: Use full path
```powershell
& "C:\Users\kyoto\AppData\Local\Programs\Python\Python313\Scripts\alembic.exe" revision --autogenerate -m "Description"
& "C:\Users\kyoto\AppData\Local\Programs\Python\Python313\Scripts\alembic.exe" upgrade head
```

### Method 3: Add to PATH (Permanent)
Add this directory to your PATH environment variable:
```
C:\Users\kyoto\AppData\Local\Programs\Python\Python313\Scripts
```

Then you can use:
```powershell
alembic revision --autogenerate -m "Description"
alembic upgrade head
```

## Common Commands

```powershell
# Create a new migration
.\alembic.ps1 revision --autogenerate -m "Initial migration"

# Apply all pending migrations
.\alembic.ps1 upgrade head

# Rollback one migration
.\alembic.ps1 downgrade -1

# Rollback all migrations
.\alembic.ps1 downgrade base

# Show current revision
.\alembic.ps1 current

# Show migration history
.\alembic.ps1 history
```

## Notes

- The initial migration has been created: `alembic/versions/b732fe79879e_initial_migration.py`
- Run `.\alembic.ps1 upgrade head` to apply it to your database
- Always review auto-generated migrations before applying them



