@param java.util.ResourceBundle messages
@param String lang
@template.layout(lang = lang, messages = messages, content = @`
<h2>${messages.getString("welcome")}</h2>
<img class="img-fluid" src="/resources/images/pets.png" alt="${messages.getString("petsImage")}">
`)
