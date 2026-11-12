@param pvrlabs.coilbase.samples.petclinic.owner.Pet pet
@param String date
@param String description
@param java.util.Map<String, String> errors
@param java.util.ResourceBundle messages
@param String lang
@param String csrf
@template.layout(lang = lang, messages = messages, content = @`
    <h2>${messages.getString("addVisit")}</h2>
    <p>${pet.name()} — ${pet.type().name()}</p>
    <form class="petclinic-form" method="post">
        <input type="hidden" name="_csrf" value="${csrf}">
        @template.field("date", "text", date, errors, messages)
        @template.field("description", "text", description, errors, messages)
        <button class="btn btn-primary" type="submit">${messages.getString("addVisit")}</button>
    </form>
    <h3>${messages.getString("previousVisits")}</h3>
    @for(var visit : pet.visits())
        <p>${String.valueOf(visit.date())} — ${visit.description()}</p>
    @endfor
`)
