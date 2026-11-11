package pvrlabs.coilbase.samples.petclinic.owner;

import java.util.LinkedHashMap;
import java.util.Map;
import java.util.ResourceBundle;

public record OwnerForm(String firstName, String lastName, String address, String city, String telephone) {
    public Map<String, String> errors(ResourceBundle messages) {
        var errors = new LinkedHashMap<String, String>();
        check(errors, "firstName", firstName, 30, messages);
        check(errors, "lastName", lastName, 30, messages);
        check(errors, "address", address, 255, messages);
        check(errors, "city", city, 80, messages);
        if (isNullOrBlank(telephone)) {
            errors.put("telephone", messages.getString("required"));
        } else if (!telephone.matches("[0-9]{10}")) {
            errors.put("telephone", messages.getString("telephone.invalid"));
        }
        return errors;
    }

    private static boolean isNullOrBlank(String value) {
        return value == null || value.isBlank();
    }

    private static void check(Map<String, String> errors, String name, String value,
            int maximumLength, ResourceBundle messages) {
        if (isNullOrBlank(value)) {
            errors.put(name, messages.getString("required"));
        } else if (value.length() > maximumLength) {
            errors.put(name, messages.getString("tooLong").formatted(maximumLength));
        }
    }
}
