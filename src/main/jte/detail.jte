@param pvrlabs.coilbase.samples.petclinic.owner.Owner owner
@param java.util.ResourceBundle messages
@param String lang
@param String flash
@template.layout(lang = lang, messages = messages, content = @`
    @if(!flash.isEmpty())
        <p role="status">${flash}</p>
    @endif
    <h2>${messages.getString("owner")}</h2>
    <p>${owner.firstName()} ${owner.lastName()}</p>
    <p>${owner.address()}, ${owner.city()}, ${owner.telephone()}</p>
    <h3>${messages.getString("pets")}</h3>
    @for(var pet : owner.pets())
        <p>${pet.name()} — ${String.valueOf(pet.birthDate())} — ${pet.type().name()}</p>
        <a href="/owners/${owner.id()}/pets/${pet.id()}/edit">${messages.getString("editPet")}</a>
        <a href="/owners/${owner.id()}/pets/${pet.id()}/visits/new">${messages.getString("addVisit")}</a>
        @for(var visit : pet.visits())
            <p>${String.valueOf(visit.date())} — ${visit.description()}</p>
        @endfor
    @endfor
    <a href="/owners/${owner.id()}/edit">${messages.getString("updateOwner")}</a>
    <a href="/owners/${owner.id()}/pets/new">${messages.getString("addPet")}</a>
`)
