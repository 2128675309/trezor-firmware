from trezor.crypto.curve import secp256k1
from trezor.enums import EthereumDataType
from trezor.messages import (
    EthereumSignTypedData,
    EthereumTypedDataSignature,
    EthereumTypedDataStructAck,
    EthereumTypedDataStructRequest,
)

from apps.common import paths

from . import address
from .keychain import PATTERNS_ADDRESS, with_keychain_from_path
from .layout import confirm_hash, should_we_show_domain, should_we_show_message
from .typed_data import hash_struct, keccak256, validate_field_type

if False:
    from typing import Dict
    from trezor.wire import Context


@with_keychain_from_path(*PATTERNS_ADDRESS)
async def sign_typed_data(ctx: Context, msg: EthereumSignTypedData, keychain):
    await paths.validate_path(ctx, keychain, msg.address_n)

    data_hash = await generate_typed_data_hash(
        ctx, msg.primary_type, msg.metamask_v4_compat
    )

    node = keychain.derive(msg.address_n)
    signature = secp256k1.sign(
        node.private_key(), data_hash, False, secp256k1.CANONICAL_SIG_ETHEREUM
    )

    return EthereumTypedDataSignature(
        address=address.address_from_bytes(node.ethereum_pubkeyhash()),
        signature=signature[1:] + signature[0:1],
    )


async def generate_typed_data_hash(
    ctx: Context, primary_type: str, metamask_v4_compat: bool = True
) -> bytes:
    """
    Generates typed data hash according to EIP-712 specification
    https://eips.ethereum.org/EIPS/eip-712#specification

    metamask_v4_compat - a flag that enables compatibility with MetaMask's signTypedData_v4 method
    """
    types = {}
    await collect_types(ctx, "EIP712Domain", types)
    await collect_types(ctx, primary_type, types)

    show_domain = await should_we_show_domain(ctx, types["EIP712Domain"].members)
    # Member path starting with [0] means getting domain values, [1] is for message values
    domain_separator = await hash_struct(
        ctx=ctx,
        primary_type="EIP712Domain",
        types=types,
        member_path=[0],
        show_data=show_domain,
        parent_objects=["EIP712"],
        metamask_v4_compat=metamask_v4_compat,
    )

    show_message = await should_we_show_message(
        ctx, primary_type, types[primary_type].members
    )
    message_hash = await hash_struct(
        ctx=ctx,
        primary_type=primary_type,
        types=types,
        member_path=[1],
        show_data=show_message,
        parent_objects=[primary_type],
        metamask_v4_compat=metamask_v4_compat,
    )

    await confirm_hash(ctx, primary_type, message_hash)

    return keccak256(b"\x19" + b"\x01" + domain_separator + message_hash)


async def collect_types(
    ctx: Context, type_name: str, types: Dict[str, EthereumTypedDataStructAck]
) -> None:
    """
    Recursively collects types from the client
    """
    req = EthereumTypedDataStructRequest(name=type_name)
    current_type = await ctx.call(req, EthereumTypedDataStructAck)
    types[type_name] = current_type
    for member in current_type.members:
        validate_field_type(member.type)
        if (
            member.type.data_type == EthereumDataType.STRUCT
            and member.type.struct_name not in types
        ):
            await collect_types(ctx, member.type.struct_name, types)
