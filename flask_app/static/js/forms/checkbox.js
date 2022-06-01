function update_checkbox_value(checkbox) {
    // Set the value of the checkbutton so that it is submitted with the form.
    if (checkbox.checked) { checkbox.setAttribute('value', 'true'); }
    else { checkbox.setAttribute('value', 'false'); }
}

document.querySelectorAll('input[type="checkbox"]').forEach(checkbox => {
    update_checkbox_value(checkbox)
});