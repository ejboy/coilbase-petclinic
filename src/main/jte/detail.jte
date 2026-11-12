@param pvrlabs.coilbase.samples.petclinic.owner.Owner owner
@param java.util.ResourceBundle messages
@param String lang
@param String flash
@template.layout(lang = lang, messages = messages, content = @`
    @if(!flash.isEmpty())
        <p role="status">${flash}</p>
    @endif
    <h2>${messages.getString("owner")}</h2>
    <table class="table owner-summary">
        <tbody>
            <tr><th scope="row">${messages.getString("name")}</th><td>${owner.firstName()} ${owner.lastName()}</td></tr>
            <tr><th scope="row">${messages.getString("address")}</th><td>${owner.address()}</td></tr>
            <tr><th scope="row">${messages.getString("city")}</th><td>${owner.city()}</td></tr>
            <tr><th scope="row">${messages.getString("telephone")}</th><td>${owner.telephone()}</td></tr>
        </tbody>
    </table>
    <div class="petclinic-actions mb-4">
        <a class="btn btn-primary" href="/owners/${owner.id()}/edit">${messages.getString("updateOwner")}</a>
        <a class="btn btn-primary" href="/owners/${owner.id()}/pets/new">${messages.getString("addPet")}</a>
    </div>
    <h3>${messages.getString("pets")}</h3>
    @for(var pet : owner.pets())
        <div class="mb-4">
            <p>${pet.name()} — ${String.valueOf(pet.birthDate())} — ${pet.type().name()}</p>
            <div class="petclinic-actions my-2">
                <a href="/owners/${owner.id()}/pets/${pet.id()}/edit">${messages.getString("editPet")}</a>
                <a href="/owners/${owner.id()}/pets/${pet.id()}/visits/new">${messages.getString("addVisit")}</a>
            </div>
            @for(var visit : pet.visits())
                <p>${String.valueOf(visit.date())} — ${visit.description()}</p>
            @endfor
        </div>
    @endfor
`)
