/*
It is important that the user has JavaScript enabled. If it isn't, then things like time zone conversion will break,
and the site will not function properly.
*/

// Enable all elements that should be enabled with JavaScript.
document.querySelectorAll('.js_enable_with_js').forEach(disabled_tag => {
    if (disabled_tag.classList.contains('disabled')) {
        disabled_tag.classList.remove('disabled');
    }
    disabled_tag.classList.remove('js_enable_with_js');
});

// Remove the "JavaScript Required" popup with JavaScript.
document.querySelector('#js_required').remove();