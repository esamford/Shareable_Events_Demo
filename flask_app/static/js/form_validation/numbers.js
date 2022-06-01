function validate_numeric_positive_or_zero(number_input_element, default_value = 0) {
    // Replace all non-numeric characters with nothing.
    var input_value = String(number_input_element.getAttribute("value")).replace(/\D/g,'');

    // Convert to a positive integer or zero.
    input_value = Math.abs(parseInt(input_value));
    if (isNaN(input_value)) {
        input_value = default_value;
    }

    number_input_element.setAttribute("value", input_value);
}
