# Java AOT Cut Spring Boot Startup by 72%. I'm Still Not Using It.

## Why I tried Java AOT

Feedback on my Spring Boot and CoilBase PetClinic comparison raised the idea
of using Spring AOT or a CDS archive. That was worth testing. I wanted to know
whether an optimized Spring deployment would change the picture, whether
CoilBase would benefit too, and what it would take to maintain the result.

Java's newer AOT cache can record information during a training run and use it
to speed up later HotSpot starts. Spring also has its own build-time AOT
processing, which generates initialization code and makes bean-graph decisions
at build time. They are separate features, and Spring's optimized configuration
in this experiment used both. [Spring Boot AOT documentation](https://docs.spring.io/spring-boot/reference/packaging/aot.html) · [JDK 25 AOT cache documentation](https://docs.oracle.com/en/java/javase/25/docs/specs/man/java.html#ahead-of-time-cache)

## AOT actually worked

I compared Spring PetClinic with our CoilBase port, which uses Jex, Jdbi and
JTE. Both applications ran with PostgreSQL in the
same one-vCPU, 1 GiB Linux VM. I measured three fresh launches per configuration
with warm storage, then sampled memory during a short quiet window.

| Application | DB-backed readiness, standard → optimized | Quiet RSS, standard → optimized | Additional cache |
| --- | ---: | ---: | ---: |
| Spring Boot 4.1.2 | 24.53 → 6.98 s (71.6% shorter) | 286.54 → 247.65 MiB (13.6% less) | 129.00 MiB |
| CoilBase preview 5 | 4.00 → 2.04 s (48.9% shorter) | 130.44 → 112.84 MiB (13.5% less) | 40.62 MiB |

These are differences between the medians of three runs. Readiness means a
complete database-backed owner page. Spring used its build-time AOT processing
and a JDK cache, while CoilBase used a JDK cache with its existing wiring and
precompiled templates. These are whole-application results: persistence,
rendering and other dependencies differ. The 1 GiB budget also included the
OS and PostgreSQL.

Both benefited significantly. Spring reached the owner page 17.55 seconds
sooner at the median and used 38.89 MiB less quiet RSS. CoilBase reached it
1.96 seconds sooner and used 17.61 MiB less. I am choosing the simpler workflow
even though the optimization helps our own framework too.

Startup varied substantially on the development host. Standard Spring 4.1.2
ranged from 22.29 to 51.31 seconds to the owner page, and optimized Spring
ranged from 6.67 to 18.26 seconds. Three runs are directional evidence, not a
capacity or minimum-memory guarantee. The full five-configuration table,
individual samples and method are in the [experiment record](../benchmark/aot-experiment/README.md).

## Then came the complications

Spring's training succeeded, but cache assembly left the 1 GiB VM
unresponsive. I recovered it and assembled the cache separately. The first
cache failed validation because assembly used a relative JAR path. Using the
deployed absolute path worked. I could not establish whether the guest ran out
of memory, so I do not count that as a confirmed OOM.

Stopping and restarting PostgreSQL changed the measurement environment, so I
repeated the matched comparison. CoilBase's cache trained and assembled more
smoothly. Both optimized applications passed the shared PostgreSQL contract,
and each final optimized launch verified that its intended cache loaded.

A separate compatible build VM would have avoided competing with PostgreSQL on
the small server. That is a sensible setup, though it still leaves a training
workload, cache artifact and target compatibility check to maintain. The build
and target do not need identical physical hardware, but the application, JDK,
OS, architecture and deployment layout must be compatible. [JDK 25 AOT cache documentation](https://docs.oracle.com/en/java/javase/25/docs/specs/man/java.html#ahead-of-time-cache)

## Why not just use GraalVM?

If I am already maintaining a separate build and deployment path, Native Image
is worth considering. In an earlier five-stack experiment on a different
512 MiB VM workload with MariaDB, Spring Boot plus Spring JDBC reached
readiness in 7.425 and 8.653 seconds on HotSpot, versus 0.172 and 0.273 seconds
with Native Image. Workload RSS was 180.6 and 187.9 MiB versus 84.0 and 85.0
MiB. The HotSpot and native runs used different JDKs and collectors. Those are
not PetClinic results. [Published five-stack comparison](https://github.com/PVRLabs/experiments/tree/main/java/coilbase-framework-comparison)

Native Image has its own costs, including compilation resources, reachability
metadata and testing of dynamic behavior. The Spring native build in that study
also needed a larger build machine. A JDK AOT cache retains HotSpot and the JIT,
which is a genuine advantage. Each option deserves testing against the actual
application and its deployment constraints. [GraalVM Native Image documentation](https://www.graalvm.org/latest/reference-manual/native-image/)

## Why I still choose HotSpot

For a solo developer or small team, consistency from development to production
is a practical advantage. With conventional HotSpot, I can build and test the
application locally and in CI using essentially the same JVM, packaging and
launch process that I deploy to production. The behavior I debug and the
artifact I test stay close to what runs on the server. I also keep familiar JVM
tools, JIT compilation and a straightforward path from a JAR to a service.

AOT caching offers a real runtime improvement, including for CoilBase. It adds
training and cache-validation steps that must work alongside that normal
workflow. Native Image introduces a separately compiled runtime that needs its
own compatibility checks and testing. For services that run continuously and
restart infrequently, I value keeping those workflows aligned. Frequent scaling,
short-lived processes or strict cold-start targets could justify the extra work.

Conventional HotSpot remains our default. We will not maintain AOT as a
featured Framework Benchmarks configuration. AOT and Native Image remain useful
optional studies when a specific workload justifies the cost.

## Further reading and data

- The [curated PetClinic AOT experiment](../benchmark/aot-experiment/README.md) contains the five configurations, 15 accepted runs, selected logs and limitations. The [earlier PetClinic benchmark](../benchmark/README.md) retains its separate results and reproduction guide.
- The [five-stack Native Image comparison](https://github.com/PVRLabs/experiments/tree/main/java/coilbase-framework-comparison) provides earlier context under different runtime and workload conditions.
- [XPipe's AOT cache report](https://xpipe.io/blog/java-aot-cache) discusses distribution and compatibility pitfalls, including a JDK 24 module-option restriction fixed in JDK 25.
- [Platform Notes](https://platformnotes.dev/posts/aot-agents/) reports failed cache training with OpenTelemetry agent 2.23.0 on specific JDK 25 and 26 releases. It did not test newer agent releases.
- [Adoptium issue 1507](https://github.com/adoptium/adoptium-support/issues/1507) reports a CPU-instruction mismatch crash in JDK 25. The issue was closed after a fix in 25.0.5; I did not reproduce that issue here.
