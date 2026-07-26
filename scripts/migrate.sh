#!/bin/bash

# Script to handle database migrations using Alembic for portal-email backend
# Usage: 
#   ./scripts/migrate.sh create "migration message"  - To create a new migration
#   ./scripts/migrate.sh apply                        - To apply migrations to the database
#   ./scripts/migrate.sh stamp                        - To stamp the database with the current head

set -e

# Navigate to the backend directory (where alembic.ini is located)
cd "$(dirname "$0")/.."

# Check if venv exists and activate it
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d "../venv" ]; then
    source ../venv/bin/activate
else
    echo "Warning: venv not found. Using system python/alembic."
fi

COMMAND=$1

if [ "$COMMAND" == "create" ]; then
    MESSAGE=$2
    if [ -z "$MESSAGE" ]; then
        echo "Error: Migration message is required."
        echo "Usage: ./scripts/migrate.sh create \"migration message\""
        exit 1
    fi
    echo "Generating new migration: $MESSAGE"
    alembic revision --autogenerate -m "$MESSAGE"
elif [ "$COMMAND" == "apply" ]; then
    echo "Checking database state for migrations..."
    STATUS=0
    python3 -c "
import os, sys
sys.path.insert(0, '.')
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from sqlalchemy import create_engine, inspect

db_url = os.getenv('DATABASE_URL', 'sqlite:///./email.db').replace('sqlite+aiosqlite:///', 'sqlite:///')
try:
    engine = create_engine(db_url)
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    if ('email_templates' in tables or 'smtp_configs' in tables) and 'alembic_version' not in tables:
        sys.exit(10)
except Exception:
    pass
sys.exit(0)
" 2>/dev/null || STATUS=$?

    if [ $STATUS -eq 10 ]; then
        echo "Existing database detected without Alembic tracking. Stamping database with head revision..."
        alembic stamp head
    fi

    echo "Applying migrations to the database..."
    MIGRATE_LOG=$(mktemp)
    if ! alembic upgrade heads >"$MIGRATE_LOG" 2>&1; then
        if grep -q "already exists" "$MIGRATE_LOG"; then
            echo "Pre-existing database detected. Stamping database with head revision..."
            alembic stamp head
            echo "Re-applying migrations..."
            alembic upgrade heads
        else
            cat "$MIGRATE_LOG"
            rm -f "$MIGRATE_LOG"
            exit 1
        fi
    else
        cat "$MIGRATE_LOG"
    fi
    rm -f "$MIGRATE_LOG"
elif [ "$COMMAND" == "stamp" ]; then
    echo "Stamping the database with the current head..."
    alembic stamp head
else
    echo "Invalid command: $COMMAND"
    echo "Usage:"
    echo "  ./scripts/migrate.sh create \"message\""
    echo "  ./scripts/migrate.sh apply"
    echo "  ./scripts/migrate.sh stamp"
    exit 1
fi
