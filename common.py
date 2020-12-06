def substitute_range(begin, end, input_string, input_substring):
    return input_substring.join((input_string[:begin], input_string[end:]))