
function copy_to_clipboard(text) {
    try {
        var success = navigator.clipboard.writeText(text);
    } catch (error) {
        alert("Unable to copy text to your clipboard.");
    }
}
