@param java.util.List<pvrlabs.coilbase.samples.petclinic.vet.Vet> vets
@param int page
@param int pages
@param java.util.ResourceBundle messages
@param String lang
@template.layout(lang = lang, messages = messages, content = @`
<h2>${messages.getString("vets")}</h2>
<table id="vets" class="table table-striped"><thead><tr><th>${messages.getString("name")}</th><th>${messages.getString("specialties")}</th></tr></thead><tbody>
@for(var vet : vets)
<tr><td>${vet.firstName()} ${vet.lastName()}</td><td>
@if(vet.specialties().isEmpty())${messages.getString("none")}@endif
@for(var specialty : vet.specialties())${specialty.name()} @endfor
</td></tr>
@endfor
</tbody></table>
@if(pages > 1)
<p>${messages.getString("pages")}: ${page} / ${pages}</p>
@for(int i = 1; i <= pages; i++)
<a href="/vets.html?page=${i}">${i}</a>
@endfor
@endif
`)
