@param java.util.List<pvrlabs.coilbase.samples.petclinic.owner.Owner> owners
@param int page
@param int pages
@param String lastName
@param String encodedName
@param java.util.ResourceBundle messages
@param String lang
@template.layout(lang = lang, messages = messages, content = @`
<h2>${messages.getString("owners")}</h2>
<table><thead><tr><th>${messages.getString("name")}</th><th>${messages.getString("address")}</th><th>${messages.getString("city")}</th><th>${messages.getString("telephone")}</th></tr></thead><tbody>
@for(var owner : owners)
<tr><td><a href="/owners/${owner.id()}">${owner.firstName()} ${owner.lastName()}</a></td><td>${owner.address()}</td><td>${owner.city()}</td><td>${owner.telephone()}</td></tr>
@endfor
</tbody></table>
<p>${page} / ${pages}</p>
@for(int i = 1; i <= pages; i++)
<a href="/owners?lastName=${encodedName}&amp;page=${i}">${i}</a>
@endfor
`)
