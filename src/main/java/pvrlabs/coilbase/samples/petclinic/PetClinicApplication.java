package pvrlabs.coilbase.samples.petclinic;

import io.avaje.jex.Jex;
import io.avaje.http.api.InvalidPathArgumentException;
import java.time.Duration;
import javax.sql.DataSource;
import pvrlabs.coilbase.jex.CoilBaseJexApplication;
import pvrlabs.coilbase.samples.petclinic.owner.ClinicService;
import pvrlabs.coilbase.samples.petclinic.owner.OwnerController;
import pvrlabs.coilbase.samples.petclinic.owner.OwnerController$Route;
import pvrlabs.coilbase.samples.petclinic.owner.OwnerRepository;
import pvrlabs.coilbase.samples.petclinic.owner.PetController;
import pvrlabs.coilbase.samples.petclinic.owner.PetController$Route;
import pvrlabs.coilbase.samples.petclinic.owner.PetRepository;
import pvrlabs.coilbase.samples.petclinic.owner.VisitRepository;
import pvrlabs.coilbase.samples.petclinic.owner.VisitController;
import pvrlabs.coilbase.samples.petclinic.owner.VisitController$Route;

import pvrlabs.coilbase.samples.petclinic.vet.VetRepository;
import pvrlabs.coilbase.samples.petclinic.vet.VetController;
import pvrlabs.coilbase.samples.petclinic.vet.VetController$Route;
import pvrlabs.coilbase.samples.petclinic.system.WelcomeController;
import pvrlabs.coilbase.samples.petclinic.system.WelcomeController$Route;

/** Explicitly wired PetClinic application. */
public final class PetClinicApplication extends CoilBaseJexApplication {
    private final AppConfig config;

    PetClinicApplication(AppConfig config) {
        this.config = config;
        enableStaticResources();
    }

    @Override
    protected void configureErrorHandling() {
        mapError(InvalidPathArgumentException.class, 400);
    }

    @Override
    protected DataSource createPrimaryDataSource() {
        return config.createDataSource();
    }

    @Override
    protected void registerRoutes(Jex jex) {
        var owners = new OwnerRepository(db());
        var pets = new PetRepository(db());
        var clinic = new ClinicService(db(), owners, pets, new VisitRepository(db()));
        var sessions = new Sessions(config.secureCookie(), Duration.ofMinutes(30), 10_000);
        var views = new Views();
        var ownerController = new OwnerController(clinic, sessions, views);
        var petController = new PetController(clinic, sessions, views);
        jex.routing(new OwnerController$Route(ownerController));
        jex.routing(new PetController$Route(petController));
        jex.routing(new VisitController$Route(new VisitController(clinic, sessions, views)));
        jex.routing(new VetController$Route(new VetController(new VetRepository(db()), views)));
        jex.routing(new WelcomeController$Route(new WelcomeController(views)));
    }

    public Jex.Server run() {
        return start(config.port());
    }

    public static void main(String[] args) {
        new PetClinicApplication(AppConfig.fromEnv()).run();
    }
}
