/*
 * Copyright (c) Jan Pochyla, SatoshiLabs
 *
 * Licensed under TREZOR License
 * see LICENSE file for details
 */

#include "py/runtime.h"

#if MICROPY_PY_TREZORUTILS

#include <string.h>
#include "common.h"

/// def consteq(sec: bytes, pub: bytes) -> bool:
///     '''
///     Compares the private information in `sec` with public, user-provided
///     information in `pub`.  Runs in constant time, corresponding to a length
///     of `pub`.  Can access memory behind valid length of `sec`, caller is
///     expected to avoid any invalid memory access.
///     '''
STATIC mp_obj_t mod_trezorutils_consteq(mp_obj_t sec, mp_obj_t pub) {
    mp_buffer_info_t secbuf;
    mp_get_buffer_raise(sec, &secbuf, MP_BUFFER_READ);
    mp_buffer_info_t pubbuf;
    mp_get_buffer_raise(pub, &pubbuf, MP_BUFFER_READ);

    size_t diff = secbuf.len - pubbuf.len;
    for (size_t i = 0; i < pubbuf.len; i++) {
        const uint8_t *s = (uint8_t *)secbuf.buf;
        const uint8_t *p = (uint8_t *)pubbuf.buf;
        diff |= s[i] - p[i];
    }

    if (diff == 0) {
        return mp_const_true;
    } else {
        return mp_const_false;
    }
}
STATIC MP_DEFINE_CONST_FUN_OBJ_2(mod_trezorutils_consteq_obj, mod_trezorutils_consteq);

/// def memcpy(dst: bytearray, dst_ofs: int,
///            src: bytearray, src_ofs: int,
///            n: int) -> int:
///     '''
///     Copies at most `n` bytes from `src` at offset `src_ofs` to
///     `dst` at offset `dst_ofs`.  Returns the number of actually
///     copied bytes.
///     '''
STATIC mp_obj_t mod_trezorutils_memcpy(size_t n_args, const mp_obj_t *args) {
    mp_arg_check_num(n_args, 0, 5, 5, false);

    mp_buffer_info_t dst;
    mp_get_buffer_raise(args[0], &dst, MP_BUFFER_WRITE);
    int dst_ofs = mp_obj_get_int(args[1]);
    if (dst_ofs < 0) {
        mp_raise_ValueError("Invalid dst offset (has to be >= 0)");
    }

    mp_buffer_info_t src;
    mp_get_buffer_raise(args[2], &src, MP_BUFFER_READ);
    int src_ofs = mp_obj_get_int(args[3]);
    if (src_ofs < 0) {
        mp_raise_ValueError("Invalid src offset (has to be >= 0)");
    }

    int n = mp_obj_get_int(args[4]);
    if (n < 0) {
        mp_raise_ValueError("Invalid byte count (has to be >= 0)");
    }
    size_t dst_rem = (dst_ofs < dst.len) ? dst.len - dst_ofs : 0;
    size_t src_rem = (src_ofs < src.len) ? src.len - src_ofs : 0;
    size_t ncpy = MIN(n, MIN(src_rem, dst_rem));

    memmove(((char*)dst.buf) + dst_ofs, ((const char*)src.buf) + src_ofs, ncpy);

    return mp_obj_new_int(ncpy);
}
STATIC MP_DEFINE_CONST_FUN_OBJ_VAR_BETWEEN(mod_trezorutils_memcpy_obj, 5, 5, mod_trezorutils_memcpy);

/// def halt(msg: str = None) -> None:
///     '''
///     Halts execution.
///     '''
STATIC mp_obj_t mod_trezorutils_halt(size_t n_args, const mp_obj_t *args) {
    mp_buffer_info_t msg;
    if (n_args > 0 && mp_get_buffer(args[0], &msg, MP_BUFFER_READ)) {
        ensure(0, msg.buf);
    } else {
        ensure(0, "halt");
    }
    return mp_const_none;
}
STATIC MP_DEFINE_CONST_FUN_OBJ_VAR_BETWEEN(mod_trezorutils_halt_obj, 0, 1, mod_trezorutils_halt);

STATIC const mp_rom_map_elem_t mp_module_trezorutils_globals_table[] = {
    { MP_ROM_QSTR(MP_QSTR___name__), MP_ROM_QSTR(MP_QSTR_trezorutils) },
    { MP_ROM_QSTR(MP_QSTR_consteq), MP_ROM_PTR(&mod_trezorutils_consteq_obj) },
    { MP_ROM_QSTR(MP_QSTR_memcpy), MP_ROM_PTR(&mod_trezorutils_memcpy_obj) },
    { MP_ROM_QSTR(MP_QSTR_halt), MP_ROM_PTR(&mod_trezorutils_halt_obj) },
};

STATIC MP_DEFINE_CONST_DICT(mp_module_trezorutils_globals, mp_module_trezorutils_globals_table);

const mp_obj_module_t mp_module_trezorutils = {
    .base = { &mp_type_module },
    .globals = (mp_obj_dict_t*)&mp_module_trezorutils_globals,
};

#endif // MICROPY_PY_TREZORUTILS
