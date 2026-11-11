package pvrlabs.coilbase.samples.petclinic;

import gg.jte.ContentType;
import gg.jte.TemplateEngine;
import gg.jte.output.StringOutput;
import io.avaje.jex.http.Context;
import java.util.HashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.ResourceBundle;

/** Resolves the requested language and renders the application's JTE templates. */
public final class Views {
    private final TemplateEngine templates = TemplateEngine.createPrecompiled(ContentType.Html);

    public ResourceBundle messages(Context context) {
        String languageHeader = context.header("Accept-Language");
        Locale locale;
        try {
            locale = languageHeader == null
                    ? Locale.ENGLISH
                    : Locale.lookup(
                            Locale.LanguageRange.parse(languageHeader),
                            List.of(Locale.ENGLISH, Locale.forLanguageTag("es")));
        } catch (IllegalArgumentException exception) {
            locale = Locale.ENGLISH;
        }
        return ResourceBundle.getBundle(
                "messages",
                locale == null ? Locale.ENGLISH : locale,
                ResourceBundle.Control.getNoFallbackControl(ResourceBundle.Control.FORMAT_DEFAULT));
    }

    public void render(Context context, String template, ResourceBundle messages, Map<String, Object> model) {
        String language = messages.getLocale().getLanguage();
        var parameters = new HashMap<>(model);
        parameters.put("messages", messages);
        parameters.put("lang", language.isEmpty() ? "en" : language);
        var output = new StringOutput();
        templates.render(template, parameters, output);
        context.header("Cache-Control", "no-store");
        context.html(output.toString());
    }
}
