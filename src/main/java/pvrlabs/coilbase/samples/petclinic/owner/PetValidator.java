package pvrlabs.coilbase.samples.petclinic.owner;

import java.time.LocalDate;
import java.time.format.DateTimeParseException;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.ResourceBundle;

/** Validates form fields; duplicate names are a separate persistence concern. */
public final class PetValidator {
    public record Result(Map<String, String> errors, LocalDate birthDate, PetType type) { }

    public Result validate(PetForm form, List<PetType> types, ResourceBundle messages) {
        var errors = new LinkedHashMap<String, String>();
        if (form.name().isBlank()) errors.put("name", messages.getString("required"));
        else if (form.name().length() > 30) errors.put("name", messages.getString("tooLong").formatted(30));
        LocalDate date = null;
        try {
            date = LocalDate.parse(form.birthDate());
            if (date.isAfter(LocalDate.now())) errors.put("birthDate", messages.getString("invalidDate"));
        } catch (DateTimeParseException exception) {
            errors.put("birthDate", messages.getString("invalidDate"));
        }
        var type = types.stream().filter(item -> item.name().equals(form.type())).findFirst().orElse(null);
        if (type == null) errors.put("type", messages.getString("invalidType"));
        return new Result(errors, date, type);
    }
}
