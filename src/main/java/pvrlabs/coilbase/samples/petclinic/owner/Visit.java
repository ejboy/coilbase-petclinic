package pvrlabs.coilbase.samples.petclinic.owner;

import java.time.LocalDate;

public record Visit(int id, LocalDate date, String description) { }
