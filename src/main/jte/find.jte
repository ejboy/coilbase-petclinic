@param String lastName
@param boolean error
@param java.util.ResourceBundle messages
@param String lang
@template.layout(lang = lang, messages = messages, content = @`
<h2>${messages.getString("findOwners")}</h2>
<form action="/owners" method="get"><label for="lastName">${messages.getString("lastName")}</label>
<input id="lastName" name="lastName" value="${lastName}">
@if(error)<p role="alert">${messages.getString("notFound")}</p>@endif
<button type="submit">${messages.getString("findOwners")}</button></form>
<a href="/owners/new">${messages.getString("addOwner")}</a>
`)
