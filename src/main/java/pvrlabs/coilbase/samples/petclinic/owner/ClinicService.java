package pvrlabs.coilbase.samples.petclinic.owner;

import java.sql.SQLException;
import java.time.LocalDate;
import java.util.List;
import java.util.Optional;
import pvrlabs.coilbase.RepositoryContext;

/** Owns the transaction boundaries for writes. */
public final class ClinicService {
    private final RepositoryContext db;
    private final OwnerRepository owners;
    private final PetRepository pets;
    private final VisitRepository visits;

    public ClinicService(RepositoryContext db, OwnerRepository owners, PetRepository pets, VisitRepository visits) {
        this.db = db;
        this.owners = owners;
        this.pets = pets;
        this.visits = visits;
    }
    private Pet withVisits(Pet pet) {
        return new Pet(pet.id(), pet.ownerId(), pet.name(), pet.birthDate(), pet.type(), visits.forPet(pet.id()));
    }
    Optional<Owner> findOwner(int id) {
        return owners.find(id).map(owner -> new Owner(owner.id(), owner.firstName(), owner.lastName(),
                owner.address(), owner.city(), owner.telephone(), pets.forOwner(id).stream().map(this::withVisits).toList()));
    }
    Optional<Pet> findPet(int ownerId, int petId) { return pets.find(ownerId, petId).map(this::withVisits); }
    List<Owner> searchOwners(String name, int offset) { return owners.search(name, offset); }
    int countOwners(String name) { return owners.count(name); }
    int createOwner(OwnerForm form) { return db.transactional(() -> owners.insert(form)); }
    List<PetType> petTypes() { return pets.types(); }
    boolean hasPetNamed(int ownerId, String name, int exceptId) { return pets.duplicate(ownerId, name, exceptId); }
    void updateOwner(int id, OwnerForm form) { db.transactional(() -> owners.update(id, form)); }

    void createPet(int ownerId, String name, LocalDate date, int typeId) {
        db.transactional(() -> pets.insert(ownerId, name, date, typeId));
    }
    boolean updatePet(int ownerId, int petId, String name, LocalDate date, int typeId) {
        return db.transactional(() -> pets.update(ownerId, petId, name, date, typeId) == 1);
    }
    boolean bookVisit(int ownerId, int petId, LocalDate date, String description) {
        return db.transactional(() -> visits.insert(ownerId, petId, date, description) == 1);
    }
    static boolean duplicatePetConstraint(Throwable error) {
        for (Throwable cause = error; cause != null; cause = cause.getCause()) {
            if (cause instanceof SQLException sql && "23505".equals(sql.getSQLState())
                    && sql.getMessage() != null && sql.getMessage().toLowerCase(java.util.Locale.ROOT).contains("unique_owner_pet_name")) return true;
        }
        return false;
    }
}
