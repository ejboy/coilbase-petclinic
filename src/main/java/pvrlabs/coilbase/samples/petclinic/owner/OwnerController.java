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
public final class OwnerController {
    private final ClinicService clinic;
    private final Sessions sessions;
    private final Views views;

    public OwnerController(ClinicService clinic, Sessions sessions, Views views) {
        this.clinic = clinic;
        this.sessions = sessions;
        this.views = views;
    }

    private void showForm(Context context, OwnerForm form, Map<String, String> errors,
            Sessions.Session session, String flash) {
        var messages = views.messages(context);
        views.render(context, "owner.jte", messages, Map.of(
                "form", form,
                "errors", errors,
                "csrf", session.csrf,
                "flash", flash == null ? "" : messages.getString(flash),
                "creating", context.path().equals("/owners/new")));
    }

    @Get("/owners/find")
    public void find(Context context) {
        views.render(context, "find.jte", views.messages(context), Map.of("lastName", "", "error", false));
    }

    @Get("/owners")
    public void search(Context context) {
        String name = context.queryParam("lastName", "").strip();
        int page;
        try { page = Integer.parseInt(context.queryParam("page", "1")); }
        catch (NumberFormatException exception) { context.writeEmpty(400); return; }
        if (page < 1) { context.redirect("/owners?lastName=" + java.net.URLEncoder.encode(name, java.nio.charset.StandardCharsets.UTF_8) + "&page=1"); return; }
        int count = clinic.countOwners(name);
        if (page > Math.max((count + 4) / 5, 1)) {
            context.redirect("/owners?lastName=" + java.net.URLEncoder.encode(name, java.nio.charset.StandardCharsets.UTF_8) + "&page=1");
            return;
        }
        if (count == 0) {
            views.render(context, "find.jte", views.messages(context), Map.of("lastName", name, "error", true));
            return;
        }
        if (count == 1) { context.redirect("/owners/" + clinic.searchOwners(name, 0).getFirst().id()); return; }
        long offset = ((long) page - 1) * 5;
        var owners = offset > Integer.MAX_VALUE ? java.util.List.<Owner>of() : clinic.searchOwners(name, (int) offset);
        views.render(context, "owners.jte", views.messages(context), Map.of("owners", owners, "page", page,
                "pages", (count + 4) / 5, "lastName", name,
                "encodedName", java.net.URLEncoder.encode(name, java.nio.charset.StandardCharsets.UTF_8)));
    }

    @Get("/owners/new")
    public void newOwner(Context context) {
        showForm(context, new OwnerForm("", "", "", "", ""), Map.of(), sessions.getOrCreate(context), null);
    }

    @Post("/owners/new")
    public void create(Context context) {
        context.status(200);
        var session = sessions.authorizeForm(context);
        if (session == null) return;
        var form = new OwnerForm(Requests.field(context, "firstName", ""), Requests.field(context, "lastName", ""),
                Requests.field(context, "address", ""), Requests.field(context, "city", ""), Requests.field(context, "telephone", ""));
        var errors = form.errors(views.messages(context));
        if (!errors.isEmpty()) { showForm(context, form, errors, session, null); return; }
        int id = clinic.createOwner(form);
        session.flash("ownerAdded");
        context.redirect("/owners/" + id);
    }

    @Get("/owners/{ownerId}/edit")
    public void edit(Context context) {
        Integer ownerId = Requests.ownerId(context);
        if (ownerId == null) {
            return;
        }
        var owner = clinic.findOwner(ownerId);
        if (owner.isEmpty()) {
            context.writeEmpty(404);
            return;
        }
        var session = sessions.getOrCreate(context);
        showForm(context, owner.get().form(), Map.of(), session, session.takeFlash());
    }

    @Post("/owners/{ownerId}/edit")
    public void update(Context context) {
        // Generated POST routes default to 201; form responses historically use 200.
        context.status(200);
        Integer ownerId = Requests.ownerId(context);
        if (ownerId == null) {
            return;
        }
        var session = sessions.authorizeForm(context);
        if (session == null) {
            return;
        }
        var existing = clinic.findOwner(ownerId);
        if (existing.isEmpty()) {
            context.writeEmpty(404);
            return;
        }
        var previous = existing.get().form();
        var form = new OwnerForm(
                Requests.field(context, "firstName", previous.firstName()),
                Requests.field(context, "lastName", previous.lastName()),
                Requests.field(context, "address", previous.address()),
                Requests.field(context, "city", previous.city()),
                Requests.field(context, "telephone", previous.telephone()));
        var errors = form.errors(views.messages(context));
        if (!errors.isEmpty()) {
            showForm(context, form, errors, session, null);
            return;
        }
        clinic.updateOwner(ownerId, form);
        session.flash("updated");
        context.redirect("/owners/" + ownerId);
    }

    @Get("/owners/{ownerId}")
    public void details(Context context) {
        Integer ownerId = Requests.ownerId(context);
        if (ownerId == null) {
            return;
        }
        var owner = clinic.findOwner(ownerId);
        if (owner.isEmpty()) {
            context.writeEmpty(404);
            return;
        }
        var session = sessions.existing(context);
        String flash = session == null ? null : session.takeFlash();
        var messages = views.messages(context);
        views.render(context, "detail.jte", messages, Map.of(
                "owner", owner.get(),
                "flash", flash == null ? "" : messages.getString(flash)));
    }
}
