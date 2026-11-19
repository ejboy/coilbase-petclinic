# PetClinic JVM AOT experiment

This experiment asks how much Spring Boot PetClinic and its CoilBase port gain
from practical HotSpot AOT optimizations on a small VM. It supports the
[PetClinic AOT article](../../docs/aot-experiment.md).
The earlier [PetClinic benchmark](../README.md)
used different versions and measurement windows.

## Configurations and method

The five variants were Spring Boot 4.1.0 and 4.1.2 with conventional HotSpot,
Spring Boot 4.1.2 with Spring build-time AOT and a JDK AOT cache, CoilBase
0.1.0-preview5 with conventional HotSpot, and the same CoilBase build with a
JDK AOT cache. Spring's optimized result combines framework processing and a
JDK cache. CoilBase uses the JDK cache alone. Standard variants retained the
JDK's normal class-sharing defaults. Spring deployments used extracted JARs.

The local Linux VM had one x86-64 vCPU, 1 GiB allocated RAM, 959 MiB visible,
and no swap. PostgreSQL 18.6 and the application shared it. Temurin
25.0.4.1+1 ran with `-Xms64m -Xmx256m` and ergonomic Serial GC. PostgreSQL used
128 MiB shared buffers, 100 maximum connections and 4 MiB work memory. The
Spring PetClinic source revision was `500158f732419217507c7656904b8e6aa1bcc0d6`.
The existing CoilBase port was built with preview 5. The [original PetClinic
reproduction guide](../REPRODUCING.md)
provides the earlier fixture and packaging context. Public PetClinic source has
changed since the measured build and a byte-identical rebuild is not claimed.

Each configuration ran in three rotated rounds as a fresh JVM, one application
at a time, against the same PostgreSQL fixture. PostgreSQL stayed running and
filesystem and database caches were warm. The guest client timed launch to the
first fully read HTTP 200 from `/`, then to the first complete `/owners/1`
response containing `Franklin`. It made five fixed read requests and sampled
memory for 15 quiet seconds. Readiness and memory collection ran on the same
one-vCPU guest. Application RSS/PSS, aggregate PostgreSQL process PSS and host
MemAvailable were sampled at owner readiness and during quiet. Quiet values
are medians of samples within each run. MiB is 1,048,576 bytes.

## Results

Each table cell shows the median of three runs, with the observed minimum and
maximum in parentheses. Ready RSS/PSS shows the median and range of the three
readiness samples. Deployment sizes include the complete application and runtime JARs
and cache where applicable, excluding the JDK and PostgreSQL.

| Configuration | Root s | Owner s | Ready RSS / PSS MiB | Quiet RSS MiB | Quiet PSS MiB | Deployment MiB |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Spring Boot 4.1.0 | 43.46 (23.87–47.06) | 44.21 (24.60–47.92) | 286.23 (277.79–286.81) / 283.55 (275.12–284.20) | 291.82 (284.72–291.97) | 289.20 (282.05–289.30) | 62.57 |
| Spring Boot 4.1.2 | 24.07 (21.84–50.74) | 24.53 (22.29–51.31) | 286.51 (280.44–289.03) / 283.84 (277.81–286.35) | 286.54 (286.48–294.70) | 283.91 (283.81–292.02) | 63.09 |
| Spring 4.1.2, Spring AOT + JDK cache | 6.83 (6.49–17.93) | 6.98 (6.67–18.26) | 244.02 (241.66–244.84) / 241.41 (239.05–242.18) | 247.65 (247.50–258.15) | 244.98 (244.84–255.48) | 192.63 |
| CoilBase preview 5 | 1.88 (1.64–4.18) | 4.00 (3.41–7.79) | 117.29 (117.04–120.80) / 114.63 (114.37–118.17) | 130.44 (130.05–133.64) | 127.78 (127.41–130.97) | 9.32 |
| CoilBase preview 5, JDK cache | 1.08 (0.96–1.36) | 2.04 (1.89–2.85) | 109.18 (104.05–109.29) / 106.52 (101.42–106.69) | 112.84 (108.52–112.86) | 110.17 (105.87–110.24) | 49.95 |

Spring's combined AOT configuration reached the database-backed page 17.55 s
sooner at the median (71.6%) and reduced quiet RSS by 38.89 MiB (13.6%) and
PSS by 38.93 MiB (13.7%). CoilBase with a cache reached it 1.96 s sooner
(48.9%) and reduced quiet RSS by 17.61 MiB (13.5%) and PSS by 17.61 MiB
(13.8%). The Spring and CoilBase caches added 129.00 and 40.62 MiB respectively.

The Spring version-upgrade ranges overlap considerably, so the three-run
observations do not establish an upgrade effect. Optimized CoilBase reached the
owner page 4.93 s sooner and used 134.82 MiB less quiet RSS at the median than
optimized Spring. Persistence, rendering and dependency differences contribute
to that whole-application comparison. Median quiet PostgreSQL PSS across
configurations ranged from 55.96 to 56.67 MiB, and median quiet host MemAvailable
ranged from 354.86 to 536.25 MiB.

## Operational observations and limits

Spring training produced a JVM configuration, but automatic cache assembly left
the 1 GiB VM unresponsive. The cause was not established. Separate assembly
completed with PostgreSQL stopped. The first cache failed because assembly used
a relative JAR classpath; an absolute deployed path worked. A corrected
stopped-database assembly took approximately 10 s at one-second clock resolution.
CoilBase training and one-step assembly took 6.68 s. Training logs reported
skipped classes, including proxies, and Spring also reported a class verification
warning. Both optimized variants passed the shared PostgreSQL contract using
the first working absolute-path Spring cache. The final stopped-database Spring
cache passed a separate startup smoke and all 15-suite launch checks.

The initial measured suite used a Spring cache assembled while PostgreSQL was
running. After PostgreSQL was stopped and restarted for the corrected cache,
its observed PSS changed. The complete five-configuration suite was repeated
on the common post-restart environment; this record contains those final 15
runs. Every optimized launch used `-XX:AOTMode=on` and its log confirmed the
cache opened. Every Spring AOT launch also logged AOT-processed startup. Fixture
counts were checked before and after each run, and all 15 applications exited
gracefully. No OOM message was found in the final boot's kernel log.

Startup varied widely, particularly in round three, and the local development
host may have introduced contention. Three runs do not establish confidence
intervals, capacity, long-term stability or a minimum deployment size. RSS and
PSS describe the chosen process and JVM policy; they exclude the rest of the
host. Spring and CoilBase differ in rendering, queries, persistence and other
dependencies. Further workload-specific tuning could change the results.
Earlier [Native Image experiments](https://github.com/PVRLabs/experiments/tree/main/java/coilbase-framework-comparison)
used a different application, runtime, collector, database and workload. They
provide context and are not a Native Image measurement of PetClinic.

## Evidence and verification

The [15 run directories](evidence/runs/) retain readiness times and all sampled
RSS, PSS, PostgreSQL PSS and MemAvailable observations. Process IDs and private
paths were removed. Per-run `command.json` files preserve JVM flags with deployment paths redacted.
The `application-log.txt` files are selected collector,
cache-opening and Spring AOT startup excerpts; they are not full logs. Cache
paths were replaced with `[deployment]`, and Spring's startup line was shortened
to remove process and path details. The
[contract check](evidence/contract-validation.txt), [initial classpath failure](evidence/classpath-failure.txt),
[stopped-database assembly log](evidence/cache-assembly.txt), [run order](evidence/order.txt)
and [artifact identities](evidence/artifacts.json) provide supporting context.
The artifact hash refers to the application JAR; sizes include all runtime JARs.

Run the analysis against only this curated record (the excerpt filename was changed for publication):

```sh
python3 analyze.py evidence/runs > comparison.json
```

The output matches [comparison.json](evidence/comparison.json). The captured
[measurement script](measure.py) documents the launch flags, probes and sampling;
it assumes a prepared disposable PostgreSQL fixture and matching deployments.
This is a record of the measurement, not a turnkey reproduction package. The
later revised Spring training script was syntax-checked but not rerun and is
not included as a validated procedure. Full JVM logs, binaries, AOT caches,
build outputs and raw database state are not published here.
