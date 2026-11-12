@param String name
@param String type
@param String value
@param java.util.Map<String, String> errors
@param java.util.ResourceBundle messages
<div class="mb-3">
    <label class="form-label" for="${name}">${messages.getString(name)}</label>
    <input class="form-control" id="${name}" name="${name}" type="${type}" value="${value}"
           aria-invalid="${errors.containsKey(name)}"
           aria-describedby="${errors.containsKey(name) ? name + "-error" : null}">
    @if(errors.containsKey(name))
        <span id="${name}-error">${errors.get(name)}</span>
    @endif
</div>
