window.onload = function() {
    // Use a for-loop to do nothing where no modal is found.
    document.querySelectorAll('#alert_modal').forEach( modal => {
        var show_modal = new mdb.Modal(modal);
        show_modal.show();
    });
}
