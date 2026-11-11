package pvrlabs.coilbase.samples.petclinic.owner;

import static org.junit.jupiter.api.Assertions.*;

import java.time.LocalDate;
import java.util.UUID;
import org.h2.jdbcx.JdbcDataSource;
import org.junit.jupiter.api.Test;
import pvrlabs.coilbase.Dialects;
import pvrlabs.coilbase.RepositoryContext;

class H2CollationTest {
    @Test void caseInsensitiveSearchAndPetNameConstraint() {
        var source = new JdbcDataSource();
        source.setURL("jdbc:h2:mem:" + UUID.randomUUID() + ";DB_CLOSE_DELAY=-1");
        var db = RepositoryContext.create(source, Dialects.H2);
        db.executeScriptResource("/schema.sql");
        db.executeScriptResource("/data.sql");
        var clinic = new ClinicService(db, new OwnerRepository(db), new PetRepository(db), new VisitRepository(db));
        assertTrue(clinic.searchOwners("frank", 0).stream().anyMatch(o -> o.lastName().equals("Franklin")));
        clinic.createPet(1, "UniqueCase", LocalDate.of(2020, 2, 29), 1);
        var error = assertThrows(RuntimeException.class, () -> clinic.createPet(1, "uniquecase", LocalDate.of(2020, 2, 29), 1));
        assertTrue(ClinicService.duplicatePetConstraint(error));
    }
}
