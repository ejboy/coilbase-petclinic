package pvrlabs.coilbase.samples.petclinic.owner;

import java.util.List;
import java.util.Optional;
import pvrlabs.coilbase.Repository;
import pvrlabs.coilbase.RepositoryContext;
import pvrlabs.coilbase.SqlStatement;

public final class OwnerRepository extends Repository {
    private static final String COLUMNS = "id,first_name,last_name,address,city,telephone";
    private static final SqlStatement GET = SqlStatement.of("SELECT " + COLUMNS + " FROM owners WHERE id=:id");
    private static final SqlStatement SEARCH = SqlStatement.of("SELECT " + COLUMNS + " FROM owners WHERE last_name LIKE :prefix ESCAPE '!' ORDER BY last_name,first_name,id LIMIT :limit OFFSET :offset");
    private static final SqlStatement COUNT = SqlStatement.of("SELECT COUNT(*) FROM owners WHERE last_name LIKE :prefix ESCAPE '!'");
    private static final SqlStatement INSERT = SqlStatement.of("INSERT INTO owners(first_name,last_name,address,city,telephone) VALUES (:first,:last,:address,:city,:phone)");
    private static final SqlStatement UPDATE = SqlStatement.of("UPDATE owners SET first_name=:first,last_name=:last,address=:address,city=:city,telephone=:phone WHERE id=:id");

    public OwnerRepository(RepositoryContext db) { super(db); }

    private static Owner map(java.sql.ResultSet row, org.jdbi.v3.core.statement.StatementContext context) throws java.sql.SQLException {
        return new Owner(row.getInt(1), row.getString(2), row.getString(3), row.getString(4), row.getString(5), row.getString(6), List.of());
    }
    private static String prefix(String value) {
        return value.replace("!", "!!").replace("%", "!%").replace("_", "!_") + "%";
    }
    Optional<Owner> find(int id) {
        return db.query(GET, query -> query.bind("id", id).map(OwnerRepository::map).findOne());
    }

    List<Owner> search(String name, int offset) {
        return db.query(SEARCH, query -> query.bind("prefix", prefix(name)).bind("limit", 5).bind("offset", offset).map(OwnerRepository::map).list());
    }
    int count(String name) {
        return db.query(COUNT, query -> query.bind("prefix", prefix(name)).mapTo(Integer.class).one());
    }
    int insert(OwnerForm form) {
        return db.update(INSERT, query -> query.bind("first", form.firstName()).bind("last", form.lastName())
                .bind("address", form.address()).bind("city", form.city()).bind("phone", form.telephone())
                .executeAndReturnGeneratedKeys("id").mapTo(Integer.class).one());
    }
    void update(int id, OwnerForm form) {
        db.update(UPDATE, query -> query.bind("id", id).bind("first", form.firstName()).bind("last", form.lastName())
                .bind("address", form.address()).bind("city", form.city()).bind("phone", form.telephone()).execute());
    }
}
