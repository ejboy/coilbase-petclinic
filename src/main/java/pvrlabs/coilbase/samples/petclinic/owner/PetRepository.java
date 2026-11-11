package pvrlabs.coilbase.samples.petclinic.owner;

import java.time.LocalDate;
import java.util.List;
import java.util.Optional;
import pvrlabs.coilbase.Repository;
import pvrlabs.coilbase.RepositoryContext;
import pvrlabs.coilbase.SqlStatement;

public final class PetRepository extends Repository {
    private static final String COLUMNS = "p.id,p.owner_id,p.name,p.birth_date,t.id,t.name";
    private static final SqlStatement TYPES = SqlStatement.of("SELECT id,name FROM types ORDER BY name,id");
    private static final SqlStatement GET = SqlStatement.of("SELECT " + COLUMNS + " FROM pets p JOIN types t ON t.id=p.type_id WHERE p.owner_id=:owner AND p.id=:pet");
    private static final SqlStatement FOR_OWNER = SqlStatement.of("SELECT " + COLUMNS + " FROM pets p JOIN types t ON t.id=p.type_id WHERE p.owner_id=:owner ORDER BY p.name,p.id");
    private static final SqlStatement INSERT = SqlStatement.of("INSERT INTO pets(name,birth_date,type_id,owner_id) VALUES (:name,:date,:type,:owner)");
    private static final SqlStatement UPDATE = SqlStatement.of("UPDATE pets SET name=:name,birth_date=:date,type_id=:type WHERE id=:pet AND owner_id=:owner");
    private static final SqlStatement DUPLICATE = SqlStatement.of("SELECT id FROM pets WHERE owner_id=:owner AND LOWER(name)=LOWER(:name) AND id<>:pet");

    public PetRepository(RepositoryContext db) { super(db); }

    private static Pet map(java.sql.ResultSet row, org.jdbi.v3.core.statement.StatementContext context) throws java.sql.SQLException {
        return new Pet(row.getInt(1), row.getInt(2), row.getString(3), row.getObject(4, LocalDate.class),
                new PetType(row.getInt(5), row.getString(6)), List.of());
    }
    List<PetType> types() {
        return db.query(TYPES, query -> query.map((row, context) -> new PetType(row.getInt(1), row.getString(2))).list());
    }
    Optional<Pet> find(int ownerId, int petId) {
        return db.query(GET, query -> query.bind("owner", ownerId).bind("pet", petId).map(PetRepository::map).findOne());
    }
    List<Pet> forOwner(int ownerId) {
        return db.query(FOR_OWNER, query -> query.bind("owner", ownerId).map(PetRepository::map).list());
    }
    boolean duplicate(int ownerId, String name, int exceptId) {
        return db.query(DUPLICATE, query -> query.bind("owner", ownerId).bind("name", name).bind("pet", exceptId)
                .mapTo(Integer.class).findFirst().isPresent());
    }
    void insert(int ownerId, String name, LocalDate date, int typeId) {
        db.update(INSERT, query -> query.bind("owner", ownerId).bind("name", name).bind("date", date).bind("type", typeId).execute());
    }
    int update(int ownerId, int petId, String name, LocalDate date, int typeId) {
        return db.update(UPDATE, query -> query.bind("owner", ownerId).bind("pet", petId).bind("name", name)
                .bind("date", date).bind("type", typeId).execute());
    }
}
