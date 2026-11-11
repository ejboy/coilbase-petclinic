package pvrlabs.coilbase.samples.petclinic;

import static org.junit.jupiter.api.Assertions.*;

import org.junit.jupiter.api.Test;

class AppConfigTest {
    @Test void validatesEssentialSettings() {
        assertThrows(IllegalArgumentException.class, () -> new AppConfig(" ", "", "", true, 8080));
        assertThrows(IllegalArgumentException.class, () -> new AppConfig("jdbc:h2:mem:test", "", "", true, -1));
        assertThrows(IllegalArgumentException.class, () -> new AppConfig("jdbc:h2:mem:test", "", "", true, 65536));
        assertDoesNotThrow(() -> new AppConfig("jdbc:h2:mem:test", "", "", true, 0));
    }

    @Test void configuresDatasourceWithoutStartingOrSizingPool() {
        var config = new AppConfig("jdbc:h2:mem:test", "user", "password", false, 1234);
        try (var source = config.createDataSource()) {
            assertEquals(config.databaseUrl(), source.getJdbcUrl());
            assertEquals(config.databaseUsername(), source.getUsername());
            assertEquals(config.databasePassword(), source.getPassword());
            assertFalse(source.isRunning());
        }
    }
}
