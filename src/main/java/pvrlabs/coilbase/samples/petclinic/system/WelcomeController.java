package pvrlabs.coilbase.samples.petclinic.system;

import java.util.Map;
import io.avaje.http.api.Controller;
import io.avaje.http.api.Get;
import io.avaje.jex.http.Context;
import pvrlabs.coilbase.samples.petclinic.Views;

@Controller
public final class WelcomeController {
    private final Views views;
    public WelcomeController(Views views) { this.views = views; }

    @Get("/")
    public void welcome(Context context) {
        views.render(context, "welcome.jte", views.messages(context), Map.of());
    }
    @Get("/oups")
    public void error(Context context) {
        context.status(500);
        views.render(context, "error.jte", views.messages(context), Map.of());
    }
}
