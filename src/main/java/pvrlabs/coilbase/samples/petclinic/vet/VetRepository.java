package pvrlabs.coilbase.samples.petclinic.vet;

import java.util.List;
import pvrlabs.coilbase.Repository;
import pvrlabs.coilbase.RepositoryContext;
import pvrlabs.coilbase.SqlStatement;

public final class VetRepository extends Repository {
    private static final SqlStatement COUNT = SqlStatement.of("SELECT COUNT(*) FROM vets");
    private static final SqlStatement PAGE = SqlStatement.of("SELECT id,first_name,last_name FROM vets ORDER BY id LIMIT :limit OFFSET :offset");
    private static final SqlStatement ALL = SqlStatement.of("SELECT id,first_name,last_name FROM vets ORDER BY id");
    private static final SqlStatement SPECIALTIES = SqlStatement.of("SELECT s.id,s.name FROM specialties s JOIN vet_specialties vs ON vs.specialty_id=s.id WHERE vs.vet_id=:id ORDER BY s.name,s.id");

    public VetRepository(RepositoryContext db) { super(db); }

    private record VetRow(int id, String firstName, String lastName) { }
    private List<Vet> withSpecialties(List<VetRow> rows) {
        return rows.stream().map(row -> new Vet(row.id(), row.firstName(), row.lastName(),
                db.query(SPECIALTIES, query -> query.bind("id", row.id()).map((result, context) ->
                        new Specialty(result.getInt(1), result.getString(2))).list()))).toList();
    }
    private static VetRow map(java.sql.ResultSet row, org.jdbi.v3.core.statement.StatementContext context) throws java.sql.SQLException {
        return new VetRow(row.getInt(1), row.getString(2), row.getString(3));
    }
    public int count() { return db.query(COUNT, query -> query.mapTo(Integer.class).one()); }
    public List<Vet> page(int offset) {
        return withSpecialties(db.query(PAGE, query -> query.bind("limit", 5).bind("offset", offset).map(VetRepository::map).list()));
    }
    public List<Vet> all() { return withSpecialties(db.query(ALL, query -> query.map(VetRepository::map).list())); }
}
