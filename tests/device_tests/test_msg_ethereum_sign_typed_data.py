# This file is part of the Trezor project.
#
# Copyright (C) 2012-2019 SatoshiLabs and contributors
#
# This library is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License version 3
# as published by the Free Software Foundation.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the License along with this library.
# If not, see <https://www.gnu.org/licenses/lgpl-3.0.html>.

import pytest

from trezorlib import ethereum
from trezorlib.tools import parse_path

MNEMONIC = " ".join(["all"] * 12)
PATH = "m/44'/60'/0'/0/0"
USE_V4 = True

EXPECTED_ADDRESS = "0x73d0385F4d8E00C5e6504C6030F47BF6212736A8"

EXPECTED_SIG_BASIC = "0x2c2d8c7c1facf5bdcd997b5435bb42f3f4170a111ce079c94b5d1e34414f76560c4600d2167568e052ab846555bd590de93bb230987766c636613262eaeb8bdc1c"
CONTENT_BASIC = """
{
    "types": {
        "EIP712Domain": [
            {
                "name": "name",
                "type": "string"
            },
            {
                "name": "version",
                "type": "string"
            },
            {
                "name": "chainId",
                "type": "uint256"
            },
            {
                "name": "verifyingContract",
                "type": "address"
            }
        ],
        "Person": [
            {
                "name": "name",
                "type": "string"
            },
            {
                "name": "wallet",
                "type": "address"
            }
        ],
        "Mail": [
            {
                "name": "from",
                "type": "Person"
            },
            {
                "name": "to",
                "type": "Person"
            },
            {
                "name": "contents",
                "type": "string"
            }
        ]
    },
    "primaryType": "Mail",
    "domain": {
        "name": "Ether Mail",
        "version": "1",
        "chainId": 1,
        "verifyingContract": "0x1e0Ae8205e9726E6F296ab8869160A6423E2337E"
    },
    "message": {
        "from": {
            "name": "Cow",
            "wallet": "0xc0004B62C5A39a728e4Af5bee0c6B4a4E54b15ad"
        },
        "to": {
            "name": "Bob",
            "wallet": "0x54B0Fa66A065748C40dCA2C7Fe125A2028CF9982"
        },
        "contents": "Hello, Bob!"
    }
}
"""

EXPECTED_SIG_LIST = "0x8acd06234a7497bf81425bcc8a6682952cd3d1aa09143222770e8bed94fe92af4ed257afb08e572ba43a2d8e269a69c5e7468839d4028d6965b2a9aad9c8c74f1c"
CONTENT_LIST = """
{
    "types": {
        "EIP712Domain": [
            {
                "name": "name",
                "type": "string"
            },
            {
                "name": "version",
                "type": "string"
            },
            {
                "name": "chainId",
                "type": "uint256"
            },
            {
                "name": "verifyingContract",
                "type": "address"
            }
        ],
        "Person": [
            {
                "name": "name",
                "type": "string"
            },
            {
                "name": "wallet",
                "type": "address"
            },
            {
                "name": "married",
                "type": "bool"
            },
            {
                "name": "kids",
                "type": "uint8"
            },
            {
                "name": "karma",
                "type": "int16"
            },
            {
                "name": "pets",
                "type": "string[]"
            }
        ],
        "Mail": [
            {
                "name": "from",
                "type": "Person"
            },
            {
                "name": "to",
                "type": "Person"
            },
            {
                "name": "messages",
                "type": "string[]"
            }
        ]
    },
    "primaryType": "Mail",
    "domain": {
        "name": "Ether Mail",
        "version": "1",
        "chainId": 1,
        "verifyingContract": "0x1e0Ae8205e9726E6F296ab8869160A6423E2337E"
    },
    "message": {
        "from": {
            "name": "Amy",
            "wallet": "0xc0004B62C5A39a728e4Af5bee0c6B4a4E54b15ad",
            "married": true,
            "kids": 2,
            "karma": 4,
            "pets": ["parrot"]
        },
        "to": {
            "name": "Bob",
            "wallet": "0x54B0Fa66A065748C40dCA2C7Fe125A2028CF9982",
            "married": false,
            "kids": 0,
            "karma": -4,
            "pets": [
                "dog",
                "cat"
            ]
        },
        "messages": [
            "Hello, Bob!",
            "How are you?",
            "Hope you're fine"
        ]
    }
}
"""


VECTORS = (
    # (CONTENT_BASIC, EXPECTED_SIG_BASIC),
    (CONTENT_LIST, EXPECTED_SIG_LIST),
)


@pytest.mark.setup_client(mnemonic=MNEMONIC)
def test_ethereum_sign_typed_data(client):
    for data_to_sign, expected_sig in VECTORS:
        with client:
            address_n = parse_path(PATH)
            ret = ethereum.sign_typed_data(client, address_n, USE_V4, data_to_sign)
            assert ret.address == EXPECTED_ADDRESS
            assert f"0x{ret.signature.hex()}" == expected_sig
