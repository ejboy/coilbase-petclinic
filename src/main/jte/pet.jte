@param pvrlabs.coilbase.samples.petclinic.owner.PetForm form
@param java.util.Map<String, String> errors
@param java.util.ResourceBundle messages
@param String lang
@param String csrf
@param boolean editing
@param java.util.List<pvrlabs.coilbase.samples.petclinic.owner.PetType> types
@template.layout(lang = lang, messages = messages, content = @`
    <h2>${messages.getString(editing ? "editPet" : "addPet")}</h2>
    <form class="petclinic-form" method="post">
        <input type="hidden" name="_csrf" value="${csrf}">
        @template.field("name", "text", form.name(), errors, messages)
        @template.field("birthDate", "text", form.birthDate(), errors, messages)
        @template.select("type", form.type(), types, errors, messages)
        <button class="btn btn-primary" type="submit">${messages.getString(editing ? "editPet" : "addPet")}</button>
    </form>
`)
