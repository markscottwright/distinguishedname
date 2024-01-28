"""
Parse Distinguished names from RFC2253
"""

import string
from io import StringIO

__all__ = ['string_to_dn', 'dn_to_string']


class _Peekable:
    def __init__(self, wrapped):
        self.wrapped = wrapped
        self.last_char = None

    def next_char(self):
        if self.last_char is not None:
            t = self.last_char
            self.last_char = None
            return t
        else:
            return self.wrapped.read(1)

    def push(self, c):
        self.last_char = c


def _read_attribute(dn_reader):
    """read up to and consume ="""
    attribute = ''
    while (c := dn_reader.next_char()) != '=':
        if c == '':
            raise Exception("DN parsing error")
        attribute += c
    return attribute


def _read_quoted_string(dn_reader):
    r"""
    Read up to the end of the quotes and on to the field delimiter or end of string
    >>> _read_quoted_string(_Peekable(StringIO('hello world"')))
    'hello world'
    >>> _read_quoted_string(_Peekable(StringIO('hello world"    ')))
    'hello world'
    >>> _read_quoted_string(_Peekable(StringIO('hello \\"world\\""    ')))
    'hello "world"'
    """
    out = ''
    while (c := dn_reader.next_char()) != '':

        # end of quoted string
        if c == '"':
            while (c := dn_reader.next_char()) != '':
                if c == ' ':
                    pass
                elif c in ',;+':
                    dn_reader.push(c)
                    return out
                else:
                    raise Exception("Non-space character outside quoted value")
            break

        # escaped value
        elif c == '\\':
            next_c = dn_reader.next_char()

            # escaped special character
            if next_c in r'"+,;\<>=':
                out += next_c

            # escaped two byte hex code
            elif next_c in "0123456789abcdefABCDEF":
                hexchar2 = dn_reader.next_char()
                out += chr(int(next_c + hexchar2, 16))

        else:
            out += c

    return out


def _read_string(dn_reader):
    out = ""
    spaces = ''
    while (c := dn_reader.next_char()) != '':

        if c == '"':
            return _read_quoted_string(dn_reader)

        # an unescaped comma or plus is the end of this field
        elif c in ',;+':
            dn_reader.push(c)
            break

        # if we see spaces, remember them but don't add them to the output yet.  Leading and trailing spaces are ignored
        elif c == ' ':
            spaces += c

        else:
            # only add spaces we've seen if we're in the middle of a string
            if out != '':
                out += spaces

            spaces = ''
            if c == '\\':
                next_c = dn_reader.next_char()

                # escaped special character
                if next_c in r'"+,;\<>=':
                    out += next_c

                # escaped two byte hex code
                elif next_c in "0123456789abcdefABCDEF":
                    hexchar2 = dn_reader.next_char()
                    out += chr(int(next_c + hexchar2, 16))
            else:
                out += c

    return out


def _read_rdn(dn_reader, normalize_attributes):
    out = [_read_name_and_attribute(dn_reader, normalize_attributes)]
    while (c := dn_reader.next_char()) == '+':
        out.append(_read_name_and_attribute(dn_reader, normalize_attributes))
    dn_reader.push(c)
    return out


def _read_name_and_attribute(dn_reader, normalize_attributes):
    if normalize_attributes:
        return _read_attribute(dn_reader).upper() + "=" + _read_string(dn_reader)
    else:
        return _read_attribute(dn_reader) + "=" + _read_string(dn_reader)


def _read_dn(dn_reader, normalize_attributes):
    out = [_read_rdn(dn_reader, normalize_attributes)]
    # compare against list, not string, inclusion to support c == ''
    while (c := dn_reader.next_char()) in [',', ';']:
        out.append(_read_rdn(dn_reader, normalize_attributes))

    if c != '':
        dn_reader.push(c)

    return out


def string_to_dn(s: str, normalize_attributes=True) -> list[list[str]]:
    r"""
    Given a DN string, return a list of rdns, where an rdn is a list of "attribute=value"

    >>> string_to_dn(r'CN=James Bond,OU=Spectre+UID=1234,C=US')
    [['CN=James Bond'], ['OU=Spectre', 'UID=1234'], ['C=US']]

    >>> string_to_dn(r'CN=    James Bond\20   ')
    [['CN=James Bond ']]

    >>> string_to_dn('CN=" James Bond "')
    [['CN= James Bond ']]

    >>> string_to_dn(r'CN=" \"James Bond\" "  ;OU=MI6')
    [['CN= "James Bond" '], ['OU=MI6']]
    """
    return _read_dn(_Peekable(StringIO(s)), normalize_attributes)


def _name_and_attribute_to_string(n):
    value_position = n.index('=') + 1

    last_non_space_position = len(n) - 1
    while n[last_non_space_position] == ' ':
        last_non_space_position -= 1

    out = n[0:value_position]
    char_seen = False
    for p in range(value_position, last_non_space_position + 1):
        if n[p] == ' ' and not char_seen:
            out += r"\20";
        else:
            char_seen = True
            if n[p] in r'"+,;\<>=':
                out += "\\" + n[p]
            elif n[p] in string.printable:
                out += n[p]
            else:
                out += "\\02x" % ord(n[p])

    out += "\\20" * (len(n) - last_non_space_position - 1)
    return out


def _rdn_to_string(rdn):
    return "+".join(_name_and_attribute_to_string(n) for n in rdn)


def dn_to_string(dn: list[list[str]]) -> str:
    #  docstring is literal, so we only have to escape once
    r"""

    >>> dn_to_string([["CN= James ", "UID=123"], ["OU=MI6,Q Division"]])
    'CN=\\20James\\20+UID=123,OU=MI6\\,Q Division'
    """
    return ",".join(_rdn_to_string(rdn) for rdn in dn)
