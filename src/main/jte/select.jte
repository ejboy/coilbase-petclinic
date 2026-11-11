@param String name
@param String value
@param java.util.List<pvrlabs.coilbase.samples.petclinic.owner.PetType> types
@param java.util.Map<String, String> errors
@param java.util.ResourceBundle messages
<div>
    <label for="${name}">${messages.getString(name)}</label>
    <select id="${name}" name="${name}" aria-invalid="${errors.containsKey(name)}"
            aria-describedby="${errors.containsKey(name) ? name + "-error" : null}">
        <option value=""></option>
        @for(var type : types)
            @if(type.name().equals(value))
                <option value="${type.name()}" selected>${type.name()}</option>
            @else
                <option value="${type.name()}">${type.name()}</option>
            @endif
        @endfor
    </select>
    @if(errors.containsKey(name))
        <span id="${name}-error">${errors.get(name)}</span>
    @endif
</div>
