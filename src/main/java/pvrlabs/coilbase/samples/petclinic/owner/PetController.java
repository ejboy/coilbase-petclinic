package pvrlabs.coilbase.samples.petclinic.owner;

import java.util.Map;
import io.avaje.http.api.Controller;
import io.avaje.http.api.Get;
import io.avaje.http.api.Post;
import io.avaje.jex.http.Context;
import pvrlabs.coilbase.samples.petclinic.Requests;
import pvrlabs.coilbase.samples.petclinic.Sessions;
import pvrlabs.coilbase.samples.petclinic.Views;

@Controller
public final class PetController {
    private final ClinicService clinic;
    private final Sessions sessions;
    private final Views views;
    private final PetValidator validator = new PetValidator();

    public PetController(ClinicService clinic, Sessions sessions, Views views) {
        this.clinic = clinic;
        this.sessions = sessions;
        this.views = views;
    }
    private void showForm(Context context, PetForm form, Map<String, String> errors,
            Sessions.Session session, boolean editing) {
        views.render(context, "pet.jte", views.messages(context), Map.of(
                "form", form, "errors", errors, "csrf", session.csrf,
                "types", clinic.petTypes(), "editing", editing));
    }
    @Get("/owners/{ownerId}/pets/new")
    public void newPet(Context context) {
        Integer ownerId = Requests.ownerId(context);
        if (ownerId == null) return;
        if (clinic.findOwner(ownerId).isEmpty()) { context.writeEmpty(404); return; }
        showForm(context, new PetForm("", "", ""), Map.of(), sessions.getOrCreate(context), false);
    }
    @Post("/owners/{ownerId}/pets/new")
    public void create(Context context) { save(context, false); }

    @Get("/owners/{ownerId}/pets/{petId}/edit")
    public void edit(Context context) {
        Integer ownerId = Requests.ownerId(context);
        if (ownerId == null) return;
        Integer petId = Requests.petId(context);
        if (petId == null) return;
        var pet = clinic.findPet(ownerId, petId);
        if (pet.isEmpty()) { context.writeEmpty(404); return; }
        var found = pet.get();
        showForm(context, new PetForm(found.name(), String.valueOf(found.birthDate()), found.type().name()),
                Map.of(), sessions.getOrCreate(context), true);
    }
    @Post("/owners/{ownerId}/pets/{petId}/edit")
    public void update(Context context) { save(context, true); }

    private void save(Context context, boolean editing) {
        context.status(200); // Generated POST routes default to 201.
        Integer ownerId = Requests.ownerId(context);
        if (ownerId == null) return;
        Integer petId = editing ? Requests.petId(context) : 0;
        if (petId == null) return;
        var session = sessions.authorizeForm(context);
        if (session == null) return;
        if (editing ? clinic.findPet(ownerId, petId).isEmpty() : clinic.findOwner(ownerId).isEmpty()) {
            context.writeEmpty(404);
            return;
        }
        var form = new PetForm(Requests.field(context, "name", ""), Requests.field(context, "birthDate", ""),
                Requests.field(context, "type", ""));
        var messages = views.messages(context);
        var result = validator.validate(form, clinic.petTypes(), messages);
        var errors = result.errors();
        if (!form.name().isBlank() && clinic.hasPetNamed(ownerId, form.name(), petId)) {
            errors.put("name", messages.getString("duplicate"));
        }
        if (errors.isEmpty()) {
            try {
                if (editing) {
                    if (!clinic.updatePet(ownerId, petId, form.name(), result.birthDate(), result.type().id())) {
                        context.writeEmpty(404);
                        return;
                    }
                } else {
                    clinic.createPet(ownerId, form.name(), result.birthDate(), result.type().id());
                }
            } catch (RuntimeException exception) {
                if (!ClinicService.duplicatePetConstraint(exception)) throw exception;
                errors.put("name", messages.getString("duplicate"));
            }
        }
        if (!errors.isEmpty()) { showForm(context, form, errors, session, editing); return; }
        session.flash(editing ? "petUpdated" : "petAdded");
        context.redirect("/owners/" + ownerId);
    }
}
