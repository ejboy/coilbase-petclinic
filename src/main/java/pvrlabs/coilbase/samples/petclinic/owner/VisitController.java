package pvrlabs.coilbase.samples.petclinic.owner;

import java.time.LocalDate;
import java.time.format.DateTimeParseException;
import java.util.LinkedHashMap;
import java.util.Map;
import io.avaje.http.api.Controller;
import io.avaje.http.api.Get;
import io.avaje.http.api.Post;
import io.avaje.jex.http.Context;
import pvrlabs.coilbase.samples.petclinic.Requests;
import pvrlabs.coilbase.samples.petclinic.Sessions;
import pvrlabs.coilbase.samples.petclinic.Views;

@Controller
public final class VisitController {
    private final ClinicService clinic;
    private final Sessions sessions;
    private final Views views;

    public VisitController(ClinicService clinic, Sessions sessions, Views views) {
        this.clinic = clinic;
        this.sessions = sessions;
        this.views = views;
    }
    private void showForm(Context context, Pet pet, String date, String description,
            Map<String, String> errors, Sessions.Session session) {
        views.render(context, "visit.jte", views.messages(context), Map.of("pet", pet, "date", date,
                "description", description, "errors", errors, "csrf", session.csrf));
    }
    @Get("/owners/{ownerId}/pets/{petId}/visits/new")
    public void newVisit(Context context, int ownerId, int petId) {
        var pet = clinic.findPet(ownerId, petId);
        if (pet.isEmpty()) { context.writeEmpty(404); return; }
        showForm(context, pet.get(), LocalDate.now().plusDays(1).toString(), "", Map.of(), sessions.getOrCreate(context));
    }
    @Post("/owners/{ownerId}/pets/{petId}/visits/new")
    public void create(Context context, int ownerId, int petId) {
        context.status(200);
        var session = sessions.authorizeForm(context);
        if (session == null) return;
        var pet = clinic.findPet(ownerId, petId);
        if (pet.isEmpty()) { context.writeEmpty(404); return; }
        String dateText = Requests.field(context, "date", "");
        String description = Requests.field(context, "description", "");
        var errors = new LinkedHashMap<String, String>();
        var messages = views.messages(context);
        LocalDate date = null;
        try {
            date = LocalDate.parse(dateText);
            if (!date.isAfter(LocalDate.now())) errors.put("date", messages.getString("invalidVisitDate"));
        } catch (DateTimeParseException exception) {
            errors.put("date", messages.getString("invalidVisitDate"));
        }
        if (description.isBlank()) errors.put("description", messages.getString("required"));
        else if (description.length() > 255) errors.put("description", messages.getString("tooLong").formatted(255));
        if (!errors.isEmpty()) { showForm(context, pet.get(), dateText, description, errors, session); return; }
        if (!clinic.bookVisit(ownerId, petId, date, description)) { context.writeEmpty(404); return; }
        session.flash("visitBooked");
        context.redirect("/owners/" + ownerId);
    }
}
