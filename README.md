# distinguishedname
Parse RFC 2253 Distinguished Names from strings and create strings from DNs (which
are implemented here as lists of RDNs - which are lists of strings in "TAG=VALUE" 
format).

# Examples
```python
>>> string_to_dn(r'CN=   James \"Bond\" +UID= 007, OU = 00 Division\, Special Services, O=MI5,C=UK')
[['CN=James "Bond"', 'UID=007'], ['OU=00 Division, Special Services'], ['O=MI5'], ['C=UK']]

>>> dn_to_string([['CN="Pinkie" Stevens', 'UID=1'], ['O= Name With Spaces ']])
'CN=\\"Pinkie\\" Stevens+UID=1,O=\\20Name With Spaces\\20'
```

# Rationale
I couldn't find any existing libraries for this.  In theory, [python-ldap][1] has a DN class that 
should be able to do this, but I've never been able to `pip install` it successfully.

This is essentially a single file, so you could also just drop this file into your project, ansible
module, CLI script or whatever.


[1]: https://www.python-ldap.org/en/python-ldap-3.4.3/ "python-ldap"

