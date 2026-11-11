package pvrlabs.coilbase.samples.petclinic.owner;

import static org.junit.jupiter.api.Assertions.*;

import java.sql.SQLException;
import java.time.LocalDate;
import java.util.UUID;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.condition.EnabledIfEnvironmentVariable;
import org.postgresql.ds.PGSimpleDataSource;
import pvrlabs.coilbase.Dialects;
import pvrlabs.coilbase.RepositoryContext;

/** Runs the same transaction and race tests against a fresh PostgreSQL schema. */
@EnabledIfEnvironmentVariable(named = "PETCLINIC_TEST_POSTGRES_URL", matches = ".+")
class PostgresClinicTest extends ClinicServiceTest {
    private PGSimpleDataSource admin;
    private String schema;

    @Override @BeforeEach void prepare() {
        admin = new PGSimpleDataSource();
        admin.setURL(System.getenv("PETCLINIC_TEST_POSTGRES_URL"));
        admin.setUser(System.getenv("PETCLINIC_TEST_POSTGRES_USER"));
        admin.setPassword(System.getenv("PETCLINIC_TEST_POSTGRES_PASSWORD"));
        schema = "petclinic_test_" + UUID.randomUUID().toString().replace("-", "");
        try (var connection = admin.getConnection(); var sql = connection.createStatement()) {
            sql.execute("CREATE SCHEMA " + schema);
        } catch (SQLException e) { throw new IllegalStateException(e); }
        var source = new PGSimpleDataSource();
        source.setURL(System.getenv("PETCLINIC_TEST_POSTGRES_URL"));
        source.setUser(System.getenv("PETCLINIC_TEST_POSTGRES_USER"));
        source.setPassword(System.getenv("PETCLINIC_TEST_POSTGRES_PASSWORD"));
        source.setCurrentSchema(schema);
        db = RepositoryContext.create(source, Dialects.POSTGRES);
        db.executeScriptResource("/postgres/schema.sql");
        db.executeScriptResource("/postgres/data.sql");
        clinic = new ClinicService(db, new OwnerRepository(db), new PetRepository(db), new VisitRepository(db));
    }

    @AfterEach void cleanUp() throws SQLException {
        if (admin != null && schema != null) {
            try (var connection = admin.getConnection(); var sql = connection.createStatement()) {
                sql.execute("DROP SCHEMA IF EXISTS " + schema + " CASCADE");
            }
        }
    }

    @Test void foreignKeysCaseOrderingPaginationAndDates() {
        assertThrows(RuntimeException.class, () -> clinic.createPet(99999, "NoOwner", LocalDate.of(2020, 1, 1), 1));
        assertThrows(RuntimeException.class, () -> clinic.createPet(1, "NoType", LocalDate.of(2020, 1, 1), 99999));
        assertTrue(clinic.searchOwners("Frank", 0).stream().anyMatch(o -> o.lastName().equals("Franklin")));
        assertTrue(clinic.searchOwners("frank", 0).isEmpty());
        assertEquals(10, clinic.countOwners(""));
        var first = clinic.searchOwners("", 0);
        var second = clinic.searchOwners("", 5);
        assertEquals(5, first.size());
        assertEquals(5, second.size());
        assertEquals(10, java.util.stream.Stream.concat(first.stream(), second.stream()).map(Owner::id).distinct().count());
        assertEquals(java.util.List.of("Black", "Coleman", "Davis", "Davis", "Escobito", "Estaban", "Franklin", "McTavish", "Rodriquez", "Schroeder"),
                java.util.stream.Stream.concat(first.stream(), second.stream()).map(Owner::lastName).toList());
        assertTrue(clinic.searchOwners("", 10).isEmpty());
        assertEquals(LocalDate.of(2000, 9, 7), clinic.findPet(1, 1).orElseThrow().birthDate());
        assertEquals(java.util.List.of(LocalDate.of(2009, 6, 4), LocalDate.of(2011, 3, 4)),
                clinic.findPet(6, 8).orElseThrow().visits().stream().map(Visit::date).toList());
        clinic.createPet(1, "UniqueCase", LocalDate.of(2020, 2, 29), 1);
        var error = assertThrows(RuntimeException.class, () -> clinic.createPet(1, "uniquecase", LocalDate.of(2020, 2, 29), 1));
        assertTrue(ClinicService.duplicatePetConstraint(error));
    }
}
