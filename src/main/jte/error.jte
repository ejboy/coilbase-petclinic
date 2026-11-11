@param java.util.ResourceBundle messages
@param String lang
@template.layout(lang = lang, messages = messages, content = @`
<h2>${messages.getString("somethingHappened")}</h2>
<p>${messages.getString("errorMessage")}</p>
`)
