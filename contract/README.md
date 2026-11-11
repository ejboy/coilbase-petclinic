# Shared HTTP contract

These checks exercise representative owner, pet, visit and vet workflows against both applications, inspect committed rows and verify persistence after restart. They mutate data: use disposable fixtures only. They are separate from `mvn test` and require Python 3, Java 25 and a separately built Spring PetClinic JAR from revision `500158f732419217507c7656904b8e6aa1bcc0d6`. Verify the source revision before building; the runner cannot verify a JAR's provenance.

Build this project with `mvn clean package`, build the pinned Spring project separately, then run:

```sh
python3 contract/run.py --spring-jar /path/to/spring-petclinic-4.0.0-SNAPSHOT.jar
```

The H2 runner creates and removes separate temporary databases. For PostgreSQL, provide two distinct disposable databases, `psql`, and a user with permission to create schemas. Set `PGUSER` and `PGPASSWORD`, then run:

```sh
python3 contract/run-postgres.py --spring-jar /path/to/spring-petclinic-4.0.0-SNAPSHOT.jar \
  --spring-db postgresql://127.0.0.1:5432/petclinic_spring \
  --coil-db postgresql://127.0.0.1:5432/petclinic_coil
```

The runner creates and drops uniquely named schemas; interrupted cleanup may require manual removal. The checks cover representative behavior, not every input or production security property. The flash check documents an accepted difference in when a message is consumed.
