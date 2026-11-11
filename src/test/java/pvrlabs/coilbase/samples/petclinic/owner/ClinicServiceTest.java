package pvrlabs.coilbase.samples.petclinic.owner;

import static org.junit.jupiter.api.Assertions.*;
import java.time.LocalDate;
import java.util.UUID;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.Executors;
import org.h2.jdbcx.JdbcDataSource;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import pvrlabs.coilbase.Dialects;
import pvrlabs.coilbase.RepositoryContext;

class ClinicServiceTest {
    protected RepositoryContext db;
    protected ClinicService clinic;

    @BeforeEach void prepare() {
        var source = new JdbcDataSource();
        source.setURL("jdbc:h2:mem:" + UUID.randomUUID() + ";DB_CLOSE_DELAY=-1;LOCK_TIMEOUT=10000");
        db = RepositoryContext.create(source, Dialects.H2);
        db.executeScriptResource("/schema.sql");
        db.executeScriptResource("/data.sql");
        clinic = new ClinicService(db, new OwnerRepository(db), new PetRepository(db), new VisitRepository(db));
    }

    @Test void failedTransactionRollsBackVisitAndConnectionRecovers() {
        var date = LocalDate.now().plusDays(1);
        assertThrows(IllegalStateException.class, () -> db.transactional(() -> {
            assertTrue(clinic.bookVisit(1, 1, date, "rollback marker"));
            throw new IllegalStateException("after insert");
        }));
        assertTrue(clinic.findPet(1, 1).orElseThrow().visits().stream().noneMatch(v -> v.description().equals("rollback marker")));
        assertFalse(clinic.bookVisit(2, 1, date, "wrong owner"));
        assertTrue(clinic.bookVisit(1, 1, date, "recovered"));
        assertTrue(clinic.findPet(1, 1).orElseThrow().visits().stream().anyMatch(v -> v.description().equals("recovered")));
    }

    @Test void datesPaginationAndForeignKeys() {
        assertThrows(RuntimeException.class, () -> clinic.createPet(99999, "NoOwner", LocalDate.of(2020, 1, 1), 1));
        assertThrows(RuntimeException.class, () -> clinic.createPet(1, "NoType", LocalDate.of(2020, 1, 1), 99999));
        assertEquals(10, clinic.countOwners(""));
        assertEquals(5, clinic.searchOwners("", 0).size());
        assertEquals(5, clinic.searchOwners("", 5).size());
        assertTrue(clinic.searchOwners("", 10).isEmpty());
        assertNotNull(clinic.findPet(1, 1).orElseThrow().birthDate());
        var dates = clinic.findPet(6, 8).orElseThrow().visits().stream().map(Visit::date).toList();
        assertEquals(2, dates.size());
        assertTrue(dates.get(0).isBefore(dates.get(1)));
    }

    @Test void competingDuplicateInsertsAndUpdatesAreRejectedByConstraint() throws Exception {
        var start = new CountDownLatch(1);
        try (var executor = Executors.newFixedThreadPool(2)) {
            var a = executor.submit(() -> insertAfter(start, "RacePet"));
            var b = executor.submit(() -> insertAfter(start, "RacePet"));
            start.countDown();
            assertNotEquals(a.get(), b.get());
        }
        assertEquals(1, clinic.findOwner(1).orElseThrow().pets().stream().filter(p -> p.name().equals("RacePet")).count());
        clinic.createPet(1, "OtherRacePet", LocalDate.of(2020, 1, 1), 1);
        var other = clinic.findOwner(1).orElseThrow().pets().stream().filter(p -> p.name().equals("OtherRacePet")).findFirst().orElseThrow();
        var error = assertThrows(RuntimeException.class, () -> clinic.updatePet(1, other.id(), "RacePet", LocalDate.of(2020, 1, 1), 1));
        assertTrue(ClinicService.duplicatePetConstraint(error));
        assertEquals("OtherRacePet", clinic.findPet(1, other.id()).orElseThrow().name());
        assertFalse(clinic.updatePet(2, other.id(), "WrongOwner", LocalDate.of(2020, 1, 1), 1));
    }

    private boolean insertAfter(CountDownLatch start, String name) throws InterruptedException {
        start.await();
        try {
            clinic.createPet(1, name, LocalDate.of(2020, 1, 1), 1);
            return true;
        } catch (RuntimeException error) {
            if (!ClinicService.duplicatePetConstraint(error)) throw error;
            return false;
        }
    }
}
