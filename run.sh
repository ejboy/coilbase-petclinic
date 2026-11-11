#!/bin/sh
set -eu
cd "$(dirname "$0")"
mvn clean package
if [ -z "${PETCLINIC_DB:-}" ]; then
    mkdir -p .demo-db
    db_path="$(pwd)/.demo-db/petclinic"
    if [ ! -e "$db_path.mv.db" ]; then
        init_dir=$(mktemp -d "$(pwd)/.demo-db/init.XXXXXX")
        trap 'rm -rf "$init_dir"' EXIT HUP INT TERM
        init_url="jdbc:h2:file:$init_dir/petclinic"
        java -cp 'target/lib/*' org.h2.tools.RunScript -url "$init_url" -user '' -script src/test/resources/schema.sql
        java -cp 'target/lib/*' org.h2.tools.RunScript -url "$init_url" -user '' -script src/test/resources/data.sql
        if ! ln "$init_dir/petclinic.mv.db" "$db_path.mv.db"; then
            echo "Demo database appeared during initialization; leaving it unchanged." >&2
            exit 1
        fi
        rm -rf "$init_dir"
        trap - EXIT HUP INT TERM
    fi
    export PETCLINIC_DB="jdbc:h2:file:$db_path"
    export PETCLINIC_DB_USER= PETCLINIC_DB_PASSWORD=
    export PETCLINIC_SECURE_COOKIE="${PETCLINIC_SECURE_COOKIE:-false}"
fi
exec java -jar target/petclinic-1.0-SNAPSHOT.jar
