var timezone_offset_input = document.querySelectorAll("form input[name='timezone_offset']").forEach(input => {
    // To convert local time to UFT time, convert local time to minutes and add the offset (also in minutes).
    var offset = get_timezone_offset();
    input.setAttribute('value', offset);
});
