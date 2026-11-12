@param String lastName
@param boolean error
@param java.util.ResourceBundle messages
@param String lang
@template.layout(lang = lang, messages = messages, content = @`
<h2>${messages.getString("findOwners")}</h2>
<form class="petclinic-form" action="/owners" method="get"><label class="form-label" for="lastName">${messages.getString("lastName")}</label>
<input class="form-control" id="lastName" name="lastName" value="${lastName}">
@if(error)<p role="alert">${messages.getString("notFound")}</p>@endif
<button class="btn btn-primary" type="submit">${messages.getString("findOwners")}</button></form>
<a class="d-inline-block mt-3" href="/owners/new">${messages.getString("addOwner")}</a>
`)
