# Measurement inputs and reproduction

These scripts and captures document the original experiment. They do not establish that rebuilding current main produces the measured binaries. The measured JAR hashes remain in the benchmark README.

## Measured software

| Component | Version |
| --- | --- |
| Spring Boot | 4.1.0 |
| Hibernate ORM | 7.4.1.Final |
| CoilBase | 0.1.0-preview4 |
| Avaje Jex | 3.6 |
| Java | Temurin 25.0.4.1+1 |
| PostgreSQL | 18.6 |

The Spring reference was built from upstream revision `500158f732419217507c7656904b8e6aa1bcc0d6`, recorded as a clean checkout. Both builds used Maven 3.9.9 and Temurin 25.0.4.1+1 on macOS. The Spring build skipped tests; the port's clean package build passed its tests. Spring was extracted with its tools jarmode before deployment. Public port branding, styling and routing subsequently changed. A byte-identical public rebuild has not been verified.

## Recompute the published workload summaries

Python 3, standard library only:

```sh
python3 scripts/analyze.py evidence/raw/workload-spring
python3 scripts/analyze.py evidence/raw/workload-coilbase
```

The outputs match `evidence/workload-spring.json` and `evidence/workload-coilbase.json`. Raw memory captures retain timestamps, process IDs, PostgreSQL process RSS and host available memory so the original analysis can run unchanged. Only workload-through-quiet samples enter the reported memory statistics; PostgreSQL summed RSS double-counts shared pages.

`evidence/root-readiness.json` preserves all six root observations, including the first Spring launch from the interrupted sequence. `evidence/owner-readiness.json` contains the separate database-backed follow-up. These sequences are not paired. The selected JVM flag and readiness-log extracts support the recorded heap settings, Serial GC selection and pool initialization. They are extracts, not complete logs.

## Run a new observation

Use a disposable Linux VM with one vCPU, 1 GiB RAM, no swap, the Java/PostgreSQL versions above and complete application deployments. Prepare separate databases with matching schema and data from the pinned Spring PostgreSQL fixtures. Set PostgreSQL shared buffers to 128 MiB, maximum connections to 100, work memory to 4 MiB, and use C.UTF-8 collation. Initialize the databases before measurement and disable application schema initialization.

Set `PETCLINIC_PERF_PASSWORD` in the environment to your disposable database credential. With no other application listening on port 8080, invoke:

```sh
python3 scripts/run.py spring /path/to/extracted/application.jar jdbc:postgresql://localhost/petclinic_spring new-spring-output
python3 scripts/analyze.py new-spring-output
python3 scripts/run.py coilbase /path/to/petclinic.jar jdbc:postgresql://localhost/petclinic_coil new-coilbase-output
python3 scripts/analyze.py new-coilbase-output
```

The default database user is `petclinic`; override with `--user`. The runner applies `-Xms64m -Xmx256m -Xlog:gc`, waits for root HTTP availability, performs one warmup cycle, then 20 serial cycles across eight paths and ten quiet seconds. The workload client shares the VM. The runner writes a new output directory and stops its application on completion.

For database-backed readiness, use fresh output directories and add `--startup-only --ready-path /owners/1 --ready-contains Franklin`. The original follow-up alternated Spring, CoilBase, CoilBase, Spring, Spring, CoilBase after a VM restart and fresh smoke checks. See the benchmark README for the interrupted original sequence and other limitations. This is a recipe for new observations, not a claim of identical timing or binary output.

## Publication boundary

Only selected measurement records, portable scripts and log/flag extracts are included. Host configuration dumps, credentials, command captures and complete application logs remain excluded. No measurements were rerun to prepare this package.
