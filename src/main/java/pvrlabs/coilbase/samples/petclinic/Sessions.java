package pvrlabs.coilbase.samples.petclinic;

import com.github.benmanes.caffeine.cache.Cache;
import com.github.benmanes.caffeine.cache.Caffeine;
import io.avaje.jex.http.Context;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.SecureRandom;
import java.time.Duration;
import java.util.Base64;
import java.util.concurrent.atomic.AtomicReference;

/** Single-instance bounded, expiring sessions for CSRF and one-shot flash messages. */
public final class Sessions {
    private final SecureRandom random = new SecureRandom();
    private final Cache<String, Session> cache;
    private final boolean secureCookie;
    private final long maxAge;

    public static final class Session {
        public final String csrf;
        private final AtomicReference<String> flash = new AtomicReference<>();

        Session(String csrf) {
            this.csrf = csrf;
        }

        public void flash(String message) {
            flash.set(message);
        }

        public String takeFlash() {
            return flash.getAndSet(null);
        }
    }

    record Issued(String id, Session session) {
    }

    Sessions(boolean secureCookie, Duration lifetime, long capacity) {
        this.secureCookie = secureCookie;
        this.maxAge = lifetime.toSeconds();
        this.cache = Caffeine.newBuilder().maximumSize(capacity).expireAfterWrite(lifetime).build();
    }

    private String randomToken() {
        byte[] bytes = new byte[32];
        random.nextBytes(bytes);
        return Base64.getUrlEncoder().withoutPadding().encodeToString(bytes);
    }

    public Session existing(Context context) {
        return find(context.cookie("petclinic_session"));
    }

    Issued issue() {
        String id = randomToken();
        Session session = new Session(randomToken());
        cache.put(id, session);
        return new Issued(id, session);
    }

    Session find(String id) {
        return id == null ? null : cache.getIfPresent(id);
    }

    boolean matches(String id, String token) {
        return matches(find(id), token);
    }

    private boolean matches(Session session, String token) {
        return session != null && token != null && MessageDigest.isEqual(
                session.csrf.getBytes(StandardCharsets.UTF_8), token.getBytes(StandardCharsets.UTF_8));
    }

    public Session getOrCreate(Context context) {
        Session session = existing(context);
        if (session != null) {
            return session;
        }
        var issued = issue();
        session = issued.session();
        context.header("Set-Cookie", "petclinic_session=" + issued.id()
                + "; Path=/; HttpOnly; SameSite=Lax; Max-Age=" + maxAge
                + (secureCookie ? "; Secure" : ""));
        return session;
    }

    public Session authorizeForm(Context context) {
        if (!Requests.acceptFormBody(context)) {
            return null;
        }
        Session session = authorize(context);
        if (session == null) {
            context.writeEmpty(403);
        }
        return session;
    }

    private Session authorize(Context context) {
        Session session = existing(context);
        String token = Requests.field(context, "_csrf", null);
        return matches(session, token) ? session : null;
    }

    long maintainedSize() {
        cache.cleanUp();
        return cache.estimatedSize();
    }
}
