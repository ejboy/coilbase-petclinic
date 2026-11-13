package pvrlabs.coilbase.samples.petclinic;

import io.avaje.jex.http.Context;

/** Small request helpers shared by the two form handlers. */
public final class Requests {
    private Requests() {
    }

    /**
     * Jex 3.6's native form decoder incorrectly preserves '+'; field() deliberately uses
     * Java's form decoder instead. The 16 KiB limit is application policy, and requiring
     * an explicit content length is a simplifying restriction of this example.
     */
    public static boolean acceptFormBody(Context context) {
        String length = context.header("Content-Length");
        if (length == null || context.header("Transfer-Encoding") != null) {
            context.writeEmpty(411);
            return false;
        }
        try {
            long size = Long.parseLong(length);
            if (size < 0) { context.writeEmpty(400); return false; }
            if (size > 16_384) { context.writeEmpty(413); return false; }
        } catch (NumberFormatException exception) {
            context.writeEmpty(400);
            return false;
        }
        try {
            // Jex 3.6 preserves '+' in form values, although form encoding uses it for spaces.
            for (String pair : context.body().split("&", -1)) {
                for (String part : pair.split("=", 2)) java.net.URLDecoder.decode(part, java.nio.charset.StandardCharsets.UTF_8);
            }
        } catch (IllegalArgumentException exception) {
            context.writeEmpty(400);
            return false;
        }
        return true;
    }

    public static String field(Context context, String name, String previousValue) {
        for (String pair : context.body().split("&", -1)) {
            String[] parts = pair.split("=", 2);
            if (java.net.URLDecoder.decode(parts[0], java.nio.charset.StandardCharsets.UTF_8).equals(name)) {
                return parts.length == 1 ? "" : java.net.URLDecoder.decode(parts[1], java.nio.charset.StandardCharsets.UTF_8);
            }
        }
        return previousValue;
    }
}
