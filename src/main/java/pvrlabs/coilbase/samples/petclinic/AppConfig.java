package pvrlabs.coilbase.samples.petclinic;

import com.zaxxer.hikari.HikariDataSource;
import java.util.Objects;

/** Application-owned startup settings; the datasource remains owned by CoilBase. */
record AppConfig(String databaseUrl, String databaseUsername, String databasePassword,
                 boolean secureCookie, int port) {
    AppConfig {
        if (databaseUrl == null || databaseUrl.isBlank()) {
            throw new IllegalArgumentException("PETCLINIC_DB must not be blank");
        }
        Objects.requireNonNull(databaseUsername, "databaseUsername");
        Objects.requireNonNull(databasePassword, "databasePassword");
        if (port < 0 || port > 65535) {
            throw new IllegalArgumentException("PORT must be between 0 and 65535");
        }
    }

    static AppConfig fromEnv() {
        var env = System.getenv();
        return new AppConfig(
                env.getOrDefault("PETCLINIC_DB", "jdbc:h2:mem:petclinic;DB_CLOSE_DELAY=-1"),
                env.getOrDefault("PETCLINIC_DB_USER", ""),
                env.getOrDefault("PETCLINIC_DB_PASSWORD", ""),
                Boolean.parseBoolean(env.getOrDefault("PETCLINIC_SECURE_COOKIE", "true")),
                Integer.parseInt(env.getOrDefault("PORT", "8080")));
    }

    HikariDataSource createDataSource() {
        var source = new HikariDataSource();
        source.setJdbcUrl(databaseUrl);
        source.setUsername(databaseUsername);
        source.setPassword(databasePassword);
        return source;
    }
}
