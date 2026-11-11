package pvrlabs.coilbase.samples.petclinic.owner;

import java.time.LocalDate;
import java.util.List;

public record Pet(int id, int ownerId, String name, LocalDate birthDate, PetType type, List<Visit> visits) { }
