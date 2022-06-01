// For displaying times.
function get_datetime_string(datetime) {
    var days = [
        "Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"
    ];
    var months = [
        "January", "February", "March", "April", "May", "June", "July",
        "August", "September", "October", "November", "December"
    ];
    var hours = [
        "12", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11",
    ];
    var minutes = [
        "00", "01", "02", "03", "04", "05", "06", "07", "08", "09",
        "10", "11", "12", "13", "14", "15", "16", "17", "18", "19",
        "20", "21", "22", "23", "24", "25", "26", "27", "28", "29",
        "30", "31", "32", "33", "34", "35", "36", "37", "38", "39",
        "40", "41", "42", "43", "44", "45", "46", "47", "48", "49",
        "50", "51", "52", "53", "54", "55", "56", "57", "58", "59",
    ];
    var am_pm = "AM";
    if (datetime.getHours() >= 12) {
        am_pm = "PM";
    }
    return days[datetime.getDay()] + ", " +
        months[datetime.getMonth()] + " " +
        datetime.getDate() + ", " +
        datetime.getFullYear() + " at " +
        hours[datetime.getHours() % 12] + ":" +
        minutes[datetime.getMinutes()] + " " +
        am_pm;
}

// For converting written text to local time from UTC.
document.querySelectorAll("span.js_convert_utc_to_local").forEach(time_span => {
    var offset = get_timezone_offset();
    var utc_datetime = new Date(time_span.innerHTML);
    utc_datetime.setMinutes(utc_datetime.getMinutes() - offset);
    var local_datetime = utc_datetime;
    time_span.innerHTML = get_datetime_string(local_datetime);
});


// For converting inputs to local time from UTC.
document.querySelectorAll('form input.js_convert_time_inputs_to_local').forEach(flag_tag => {
    if (flag_tag.value == "false") {
        var offset = get_timezone_offset();
        var utc_inputs = flag_tag.parentElement.querySelectorAll('input[type="datetime-local"]');

        utc_inputs.forEach(input => {
            var utc_datetime = new Date(input.getAttribute("value"));
            utc_datetime.setMinutes(utc_datetime.getMinutes() - offset);
            var local_time = utc_datetime;
            var new_value = local_time.getFullYear() + "-" +
                String(local_time.getMonth()+1).padStart(2, '0') + "-" +
                String(local_time.getDate()).padStart(2, '0') + "T" +
                String(local_time.getHours()).padStart(2, '0') + ":" +
                String(local_time.getMinutes()).padStart(2, '0');
            input.setAttribute("value", new_value);
        });

        // Change tag value so that page refreshes will not cause another time conversion.
        flag_tag.value = "true"
    }
});


