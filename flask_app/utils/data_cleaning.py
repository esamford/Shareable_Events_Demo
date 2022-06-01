

def remove_excessive_newlines(string: str) -> str:
    string = string.replace('\r\n', '\n')
    while "\n\n\n" in string:
        string = string.replace('\n\n\n', '\n\n')
    return string


