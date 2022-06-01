let required_inputs_hashmap = {};
function change_enable_status_of_inputs_in_group(checkbox, group_selector) {
    if (checkbox == null) { return; }
    // update_checkbox_value(checkbox)

    var location_group = document.querySelector(group_selector);
    if (location_group != null) {
        // Add inputs to the hashmap if they don't already exist.
        if (!required_inputs_hashmap[group_selector]) {
            required_inputs_hashmap[group_selector] = location_group.querySelectorAll('*[required]');
        }

        // Enable/disable the inputs.
        required_inputs_hashmap[group_selector].forEach(input => {
            if (checkbox.checked) { input.setAttribute('required', ''); }
            else { input.removeAttribute('required'); }
        });
        location_group.querySelectorAll('.form-control').forEach(input => {
            if (checkbox.checked) { input.removeAttribute('disabled'); }
            else { input.setAttribute('disabled', ''); }
        });
    }
}
change_enable_status_of_inputs_in_group(document.querySelector('#form_show_location_inputs'), '#form_location_group')
change_enable_status_of_inputs_in_group(document.querySelector('#form_show_private_event_inputs'), '#form_event_password_group')
