
function remove_duplicate_form_counters() {
    document.querySelectorAll('.form-helper').forEach((form_helper) => {
        // MD Bootstrap may load in multiple form counters per input. If this happens, delete the extras.
        while (form_helper.querySelectorAll('.form-counter').length > 1) {
            form_helper.querySelector('.form-counter').remove();
        }
    });
}

function remove_duplicate_form_counters_after_delay(delay) {
    // Every time the user switches to a tab containing a .form-helper > .form-counter,
    // the counter is duplicated. There needs to be a delay to allow for the new one to
    // appear before it can be deleted.
    setTimeout(remove_duplicate_form_counters, delay);
}

remove_duplicate_form_counters()
