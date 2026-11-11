package pvrlabs.coilbase.samples.petclinic;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.time.Duration;
import java.util.ArrayList;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;

class SessionsTest {
    @Test
    void tokenIsolationExpiryAndFlashConsumption() throws Exception {
        var sessions = new Sessions(true, Duration.ofMillis(100), 2);
        var first = sessions.issue();
        var second = sessions.issue();
        assertTrue(sessions.matches(first.id(), first.session().csrf));
        assertFalse(sessions.matches(second.id(), first.session().csrf));
        first.session().flash("message");
        assertEquals("message", first.session().takeFlash());
        assertNull(first.session().takeFlash());
        Thread.sleep(150);
        assertFalse(sessions.matches(first.id(), first.session().csrf));
    }

    @Test
    void capacityEvictsSessions() {
        var sessions = new Sessions(true, Duration.ofMinutes(1), 2);
        var issued = new ArrayList<Sessions.Issued>();
        for (int i = 0; i < 20; i++) {
            issued.add(sessions.issue());
        }
        assertTrue(sessions.maintainedSize() <= 2);
        assertTrue(issued.stream().filter(item -> sessions.find(item.id()) == null).count() >= 18);
    }

    @Test
    void concurrentFlashWritesKeepOneCompleteMessage() throws Exception {
        var session = new Sessions.Session("token");
        var ready = new CountDownLatch(12);
        var start = new CountDownLatch(1);
        try (var workers = Executors.newFixedThreadPool(12)) {
            for (int i = 0; i < 12; i++) {
                String message = "message-" + i;
                workers.submit(() -> {
                    ready.countDown();
                    start.await();
                    session.flash(message);
                    return null;
                });
            }
            assertTrue(ready.await(5, TimeUnit.SECONDS));
            start.countDown();
            workers.shutdown();
            assertTrue(workers.awaitTermination(5, TimeUnit.SECONDS));
        }
        assertTrue(session.takeFlash().startsWith("message-"));
        assertNull(session.takeFlash());
    }

    @Test
    void concurrentFlashConsumptionIsAtMostOnce() throws Exception {
        var session = new Sessions.Session("token");
        session.flash("updated");
        var ready = new CountDownLatch(12);
        var start = new CountDownLatch(1);
        var received = new AtomicInteger();
        try (var workers = Executors.newFixedThreadPool(12)) {
            for (int i = 0; i < 12; i++) {
                workers.submit(() -> {
                    ready.countDown();
                    start.await();
                    if (session.takeFlash() != null) {
                        received.incrementAndGet();
                    }
                    return null;
                });
            }
            assertTrue(ready.await(5, TimeUnit.SECONDS));
            start.countDown();
            workers.shutdown();
            assertTrue(workers.awaitTermination(5, TimeUnit.SECONDS));
        }
        assertEquals(1, received.get());
        assertNull(session.takeFlash());
    }
}
