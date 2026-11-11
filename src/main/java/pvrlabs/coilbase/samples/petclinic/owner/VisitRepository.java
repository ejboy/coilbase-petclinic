package pvrlabs.coilbase.samples.petclinic.owner;

import java.time.LocalDate;
import java.util.List;
import pvrlabs.coilbase.Repository;
import pvrlabs.coilbase.RepositoryContext;
import pvrlabs.coilbase.SqlStatement;

public final class VisitRepository extends Repository {
    private static final SqlStatement FOR_PET = SqlStatement.of("SELECT id,visit_date,description FROM visits WHERE pet_id=:pet ORDER BY visit_date,id");
    private static final SqlStatement INSERT = SqlStatement.of("INSERT INTO visits(pet_id,visit_date,description) SELECT id,:date,:description FROM pets WHERE id=:pet AND owner_id=:owner");

    public VisitRepository(RepositoryContext db) { super(db); }

    List<Visit> forPet(int petId) {
        return db.query(FOR_PET, query -> query.bind("pet", petId).map((row, context) ->
                new Visit(row.getInt(1), row.getObject(2, LocalDate.class), row.getString(3))).list());
    }

    int insert(int ownerId, int petId, LocalDate date, String description) {
        return db.update(INSERT, query -> query.bind("owner", ownerId).bind("pet", petId)
                .bind("date", date).bind("description", description).execute());
    }
}
