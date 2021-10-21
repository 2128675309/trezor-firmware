from ubinascii import hexlify

from trezor import ui
from trezor.enums import ButtonRequestType, EthereumDataType
from trezor.messages import EthereumFieldType, EthereumStructMember
from trezor.strings import format_amount
from trezor.ui.components.tt.text import Text
from trezor.ui.layouts import (
    confirm_address,
    confirm_amount,
    confirm_blob,
    confirm_output,
    confirm_text,
)
from trezor.ui.layouts.tt.altcoin import confirm_total_ethereum

from apps.common.confirm import confirm

from . import networks, tokens
from .helpers import address_from_bytes, decode_data, get_type_name

if False:
    from typing import Awaitable, Iterable, Optional
    from trezor.wire import Context


def require_confirm_tx(
    ctx: Context,
    to_bytes: bytes,
    value: int,
    chain_id: int,
    token: tokens.TokenInfo | None = None,
) -> Awaitable[None]:
    if to_bytes:
        to_str = address_from_bytes(to_bytes, networks.by_chain_id(chain_id))
    else:
        to_str = "new contract?"
    return confirm_output(
        ctx,
        address=to_str,
        amount=format_ethereum_amount(value, token, chain_id),
        font_amount=ui.BOLD,
        color_to=ui.GREY,
        br_code=ButtonRequestType.SignTx,
    )


def require_confirm_fee(
    ctx: Context,
    spending: int,
    gas_price: int,
    gas_limit: int,
    chain_id: int,
    token: tokens.TokenInfo | None = None,
) -> Awaitable[None]:
    return confirm_total_ethereum(
        ctx,
        format_ethereum_amount(spending, token, chain_id),
        format_ethereum_amount(gas_price, None, chain_id),
        format_ethereum_amount(gas_price * gas_limit, None, chain_id),
    )


async def require_confirm_eip1559_fee(
    ctx: Context, max_priority_fee: int, max_gas_fee: int, gas_limit: int, chain_id: int
) -> None:
    await confirm_amount(
        ctx,
        title="Confirm fee",
        description="Maximum fee per gas",
        amount=format_ethereum_amount(max_gas_fee, None, chain_id),
    )
    await confirm_amount(
        ctx,
        title="Confirm fee",
        description="Priority fee per gas",
        amount=format_ethereum_amount(max_priority_fee, None, chain_id),
    )
    await confirm_amount(
        ctx,
        title="Confirm fee",
        description="Maximum fee",
        amount=format_ethereum_amount(max_gas_fee * gas_limit, None, chain_id),
    )


def require_confirm_unknown_token(
    ctx: Context, address_bytes: bytes
) -> Awaitable[None]:
    contract_address_hex = "0x" + hexlify(address_bytes).decode()
    return confirm_address(
        ctx,
        "Unknown token",
        contract_address_hex,
        description="Contract:",
        br_type="unknown_token",
        icon_color=ui.ORANGE,
        br_code=ButtonRequestType.SignTx,
    )


def require_confirm_data(ctx: Context, data: bytes, data_total: int) -> Awaitable[None]:
    return confirm_blob(
        ctx,
        "confirm_data",
        title="Confirm data",
        description=f"Size: {data_total} bytes",
        data=data,
        br_code=ButtonRequestType.SignTx,
        ask_pagination=True,
    )


async def confirm_hash(ctx: Context, primary_type: str, typed_data_hash: bytes) -> None:
    data = "0x" + hexlify(typed_data_hash).decode()
    await confirm_blob(
        ctx,
        "confirm_resulting_hash",
        title="Sign typed data?",
        description=f"Hashed {primary_type}:",
        data=data,
        hold=True,
        icon=ui.ICON_CONFIG,
        icon_color=ui.GREEN,
    )


async def should_show_domain(ctx: Context, name: bytes, version: bytes) -> bool:
    page = Text("Typed Data", ui.ICON_SEND, icon_color=ui.GREEN)

    domain_name = decode_data(name, "string")
    domain_version = decode_data(version, "string")

    page.bold(f"Name: {domain_name}")
    page.normal(f"Version: {domain_version}")
    page.br()
    page.mono("View EIP712Domain?")

    return await confirm(ctx, page, ButtonRequestType.Other)


async def should_show_struct(
    ctx: Context,
    primary_type: str,
    parent_objects: Iterable[str],
    data_members: list[EthereumStructMember],
) -> bool:
    title = f"{'.'.join(parent_objects)} - {primary_type}"
    page = Text(title, ui.ICON_SEND, icon_color=ui.GREEN)

    # We have limited screen space, so showing only a preview when having lot of fields
    MAX_FIELDS_TO_SHOW = 3
    fields_amount = len(data_members)
    if fields_amount > MAX_FIELDS_TO_SHOW:
        for field in data_members[:MAX_FIELDS_TO_SHOW]:
            page.bold(limit_str(field.name))
        page.mono(f"...and {fields_amount - MAX_FIELDS_TO_SHOW} more.")
    else:
        for field in data_members:
            page.bold(limit_str(field.name))

    page.mono("View full struct?")

    return await confirm(ctx, page, ButtonRequestType.Other)


async def should_show_array(
    ctx: Context,
    name: str,
    parent_objects: Iterable[str],
    data_type: str,
    size: int,
) -> bool:
    title = f"{'.'.join(parent_objects)} - {name}"
    page = Text(title, ui.ICON_SEND, icon_color=ui.GREEN)

    page.bold(limit_str(f"Type: {data_type}"))
    page.bold(limit_str(f"Size: {size}"))
    page.br()
    page.mono("View full array?")

    return await confirm(ctx, page, ButtonRequestType.Other)


async def confirm_typed_value(
    ctx: Context,
    name: str,
    value: bytes,
    parent_objects: Iterable[str],
    primary_type: str,
    field: EthereumFieldType,
    array_index: Optional[int] = None,
) -> None:
    type_name = get_type_name(field)
    if parent_objects:
        title = f"{'.'.join(parent_objects)} - {primary_type}"
    else:
        title = primary_type

    if array_index is not None:
        array_str = f"[{array_index}]"
    else:
        array_str = ""

    description = f"{name}{array_str} ({type_name})"
    data = decode_data(value, type_name)

    if field.data_type in (EthereumDataType.ADDRESS, EthereumDataType.BYTES):
        await confirm_blob(
            ctx,
            "show_data",
            title=title,
            data=data,
            description=description,
            br_code=ButtonRequestType.Other,
        )
    else:
        await confirm_text(
            ctx,
            "show_data",
            title=title,
            data=data,
            description=description,
            br_code=ButtonRequestType.Other,
        )


def format_ethereum_amount(
    value: int, token: tokens.TokenInfo | None, chain_id: int
) -> str:
    if token:
        suffix = token.symbol
        decimals = token.decimals
    else:
        suffix = networks.shortcut_by_chain_id(chain_id)
        decimals = 18

    # Don't want to display wei values for tokens with small decimal numbers
    if decimals > 9 and value < 10 ** (decimals - 9):
        suffix = "Wei " + suffix
        decimals = 0

    return f"{format_amount(value, decimals)} {suffix}"


def limit_str(s: str, limit: int = 16) -> str:
    if len(s) <= limit + 2:
        return s

    return s[:limit] + ".."
