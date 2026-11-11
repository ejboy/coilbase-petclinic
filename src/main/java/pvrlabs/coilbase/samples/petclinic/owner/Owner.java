package pvrlabs.coilbase.samples.petclinic.owner;

import java.util.List;

/** Owner details and the pets displayed on the owner page. */
public record Owner(int id, String firstName, String lastName, String address, String city,
        String telephone, List<Pet> pets) {
    OwnerForm form() {
        return new OwnerForm(firstName, lastName, address, city, telephone);
    }
}
