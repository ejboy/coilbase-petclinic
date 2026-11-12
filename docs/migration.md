# From Spring PetClinic to CoilBase

This application is a worked migration of the pinned Spring PetClinic, not a required architecture for [CoilBase](https://github.com/PVRLabs/coilbase). Spring Boot supplies dependency injection, persistence integration, template rendering and web conventions; here the application explicitly assembles those responsibilities. That makes dependencies and lifecycle visible, but leaves more wiring and decisions to the application.

`PetClinicApplication` constructs the datasource, repositories, service and controllers. The [Avaje HTTP Jex generator](https://avaje.io/http/) creates route adapters at compile time from controller annotations. Controllers decode and validate form input, call the service, and render precompiled JTE templates. Templates replace Thymeleaf in this example; CoilBase does not require JTE.

Repositories use Jdbi and explicit SQL in place of JPA/Hibernate. Relationships and loading are explicit, so migration requires decisions about queries, persistence order and transaction boundaries. `ClinicService` owns multi-step transactions and rollback; database constraints still protect concurrent writes. The same common SQL and default statement selection work with the supplied H2 and PostgreSQL schemas; CoilBase also supports dialect overrides when needed.

## Routes and forms

Spring's owner controller uses Spring MVC mappings, model binding and validation. In [OwnerController.java](../src/main/java/pvrlabs/coilbase/samples/petclinic/owner/OwnerController.java), `@Get("/owners/find")` maps the search form and `@Post("/owners/new")` handles creation. The Avaje HTTP annotation processor generates route adapters that are registered with Jex. The handler reads fields with `Requests.field`, checks CSRF through `Sessions`, calls `OwnerForm.errors`, then either renders the form or redirects to the new owner. It explicitly sets status 200 for an invalid form because generated POST routes otherwise default to 201. This exposes the request flow, but requires code for binding, validation, status and session handling that Spring MVC normally supplies.

## Persistence and transactions

Spring's JPA model maps relationships and its repository infrastructure supplies persistence operations. Here [OwnerRepository.java](../src/main/java/pvrlabs/coilbase/samples/petclinic/owner/OwnerRepository.java) defines the search SQL, binds parameters and maps each result to an `Owner`. It escapes SQL LIKE wildcards before adding the prefix wildcard. The query and pagination are visible, but mapping and relationship loading are application code. `ClinicService.findOwner` separately loads pets and visits, so query count and loading behavior must be considered when the data grows.

[ClinicService.java](../src/main/java/pvrlabs/coilbase/samples/petclinic/owner/ClinicService.java) makes each write boundary explicit with `db.transactional`, for example `db.transactional(() -> owners.insert(form))`. Repository calls within that boundary participate in the transaction; failures roll it back. The database unique constraint handles duplicate pet names under concurrent writes. Explicit boundaries make the write scope easy to find, but developers must choose and test them rather than relying on Spring's transaction annotations and persistence context.

## Application responsibilities

The application owns HikariCP and closes it at shutdown. It validates fields, decodes URL-encoded forms and resolves English or Spanish from `Accept-Language`. A bounded, process-local session holds CSRF tokens and one-use flash messages. Sessions do not survive restart or work across instances. Cookie security defaults to enabled; use the local HTTP override only for development.

The port returns 404 for absent owner or pet resources and ignores submitted IDs when selecting update targets. It supports fewer locales than Spring and does not implement Actuator, WebJar endpoints or Spring's vet cache. Flash can be consumed by a different page before the redirect target. These differences and the absence of authentication matter when adapting the sample. Database-backed readiness can occur later than an HTTP root response, because the datasource is initialized on demand.
