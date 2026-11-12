@param pvrlabs.coilbase.samples.petclinic.owner.OwnerForm form
@param java.util.Map<String, String> errors
@param java.util.ResourceBundle messages
@param String lang
@param String csrf
@param String flash
@param boolean creating
@template.layout(lang = lang, messages = messages, content = @`
    <h2>${messages.getString("owner")}</h2>
    @if(!flash.isEmpty())
        <p role="alert">${flash}</p>
    @endif
    <form class="petclinic-form" method="post">
        <input type="hidden" name="_csrf" value="${csrf}">
        @template.field("firstName", "text", form.firstName(), errors, messages)
        @template.field("lastName", "text", form.lastName(), errors, messages)
        @template.field("address", "text", form.address(), errors, messages)
        @template.field("city", "text", form.city(), errors, messages)
        @template.field("telephone", "text", form.telephone(), errors, messages)
        <button class="btn btn-primary" type="submit">${messages.getString(creating ? "addOwner" : "updateOwner")}</button>
    </form>
`)
