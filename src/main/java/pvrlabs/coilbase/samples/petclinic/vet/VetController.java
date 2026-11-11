package pvrlabs.coilbase.samples.petclinic.vet;

import java.util.Map;
import io.avaje.http.api.Controller;
import io.avaje.http.api.Get;
import io.avaje.jex.http.Context;
import pvrlabs.coilbase.samples.petclinic.Views;

@Controller
public final class VetController {
    private final VetRepository vets;
    private final Views views;

    public VetController(VetRepository vets, Views views) {
        this.vets = vets;
        this.views = views;
    }
    @Get("/vets.html")
    public void list(Context context) {
        int page;
        try { page = Integer.parseInt(context.queryParam("page", "1")); }
        catch (NumberFormatException exception) { context.writeEmpty(400); return; }
        int pages = (vets.count() + 4) / 5;
        if (page < 1 || page > Math.max(pages, 1)) {
            context.redirect("/vets.html?page=1");
            return;
        }
        views.render(context, "vets.jte", views.messages(context), Map.of("vets", vets.page((page - 1) * 5),
                "page", page, "pages", pages));
    }
    @Get("/vets")
    public void json(Context context) {
        var result = vets.all().stream().map(vet -> Map.of("id", vet.id(), "firstName", vet.firstName(),
                "lastName", vet.lastName(), "specialties", vet.specialties().stream()
                        .map(specialty -> Map.of("id", specialty.id(), "name", specialty.name(), "new", false)).toList(),
                "nrOfSpecialties", vet.specialties().size(), "new", false)).toList();
        context.json(Map.of("vetList", result));
    }
}
