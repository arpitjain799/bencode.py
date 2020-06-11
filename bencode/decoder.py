# The contents of this file are subject to the BitTorrent Open Source License
# Version 1.1 (the License).  You may not copy or use this file, in either
# source code or executable form, except in compliance with the License.  You
# may obtain a copy of the License at http://www.bittorrent.com/license/.
#
# Software distributed under the License is distributed on an AS IS basis,
# WITHOUT WARRANTY OF ANY KIND, either express or implied.  See the License
# for the specific language governing rights and limitations under the
# License.

# Written by Petru Paler

"""bencode.py - bencode encoder + decoder."""

from bencode.compat import *
from bencode.exceptions import BencodeDecodeError

try:
    from typing import Dict, List, Tuple, Deque, Union, TextIO, BinaryIO, Any
except ImportError:
    Dict = List = Tuple = Deque = Union = TextIO = BinaryIO = Any = None

try:
    from collections import OrderedDict
except ImportError:
    OrderedDict = None

try:
    import pathlib
except ImportError:
    pathlib = None


class BencodeDecoder(object):
    def __init__(self):
        # noinspection PyDictCreation
        self.decode_func = {}
        self.decode_func[b'l'] = self.decode_list
        self.decode_func[b'i'] = self.decode_int
        self.decode_func[b'0'] = self.decode_string
        self.decode_func[b'1'] = self.decode_string
        self.decode_func[b'2'] = self.decode_string
        self.decode_func[b'3'] = self.decode_string
        self.decode_func[b'4'] = self.decode_string
        self.decode_func[b'5'] = self.decode_string
        self.decode_func[b'6'] = self.decode_string
        self.decode_func[b'7'] = self.decode_string
        self.decode_func[b'8'] = self.decode_string
        self.decode_func[b'9'] = self.decode_string
        self.decode_func[b'd'] = self.decode_dict

    def decode(self, value):
        # type: (bytes) -> Union[Tuple, List, OrderedDict, bool, int, str, bytes]
        """
        Decode bencode formatted byte string ``value``.

        :param value: Bencode formatted string
        :type value: bytes

        :return: Decoded value
        :rtype: object
        """
        try:
            value = to_binary(value)
            data, length = self.decode_func[value[0:1]](value, 0)
        except (IndexError, KeyError, TypeError, ValueError):
            raise BencodeDecodeError("not a valid bencoded string")

        if length != len(value):
            raise BencodeDecodeError("invalid bencoded value (data after valid prefix)")

        return data

    def decode_int(self, x, f):
        # type: (bytes, int) -> Tuple[int, int]
        f += 1
        newf = x.index(b'e', f)
        n = int(x[f:newf])

        if x[f:f + 1] == b'-':
            if x[f + 1:f + 2] == b'0':
                raise ValueError
        elif x[f:f + 1] == b'0' and newf != f + 1:
            raise ValueError

        return n, newf + 1

    def decode_string(self, x, f):
        # type: (bytes, int) -> Tuple[bytes, int]
        """Decode torrent bencoded 'string' in x starting at f."""
        colon = x.index(b':', f)
        n = int(x[f:colon])

        if x[f:f + 1] == b'0' and colon != f + 1:
            raise ValueError

        colon += 1
        s = x[colon:colon + n]

        return bytes(s), colon + n


    def decode_list(self, x, f):
        # type: (bytes, int) -> Tuple[List, int]
        r, f = [], f + 1

        while x[f:f + 1] != b'e':
            v, f = self.decode_func[x[f:f + 1]](x, f)
            r.append(v)

        return r, f + 1

    def decode_dict(self, x, f, force_sort=True):
        # type: (bytes, int, bool) -> Tuple[OrderedDict[str, Any], int]
        """Decode bencoded data to an OrderedDict.

        The BitTorrent standard states that:
            Keys must be strings and appear in sorted order (sorted as raw
            strings, not alphanumerics)
        - http://www.bittorrent.org/beps/bep_0003.html

        Therefore, this function will force the keys to be strings (decoded
        from utf-8), and by default the keys are (re)sorted after reading.
        Set force_sort to False to keep the order of the dictionary as
        represented in x, as many other encoders and decoders do not force this
        property.
        """

        r, f = OrderedDict(), f + 1

        while x[f:f + 1] != b'e':
            k, f = self.decode_string(x, f)
            r[k], f = self.decode_func[x[f:f + 1]](x, f)

        if force_sort:
            r = OrderedDict(sorted(r.items()))

        return r, f + 1
