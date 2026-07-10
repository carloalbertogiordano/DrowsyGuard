#include "base64.h"
#include <cstring>

static int8_t decode_char(char c) {
    if (c >= 'A' && c <= 'Z') return c - 'A';
    if (c >= 'a' && c <= 'z') return c - 'a' + 26;
    if (c >= '0' && c <= '9') return c - '0' + 52;
    if (c == '+') return 62;
    if (c == '/') return 63;
    return -1;  // '=' (padding) o carattere non valido
}

int base64_decode(const char* input, uint8_t* out_buffer, size_t out_buffer_size) {
    size_t input_len = strlen(input);
    size_t out_len = 0;
    int val = 0;
    int bits = -8;

    for (size_t i = 0; i < input_len; i++) {
        char c = input[i];
        if (c == '=') break;

        int8_t d = decode_char(c);
        if (d == -1) continue;

        val = (val << 6) + d;
        bits += 6;

        if (bits >= 0) {
            if (out_len >= out_buffer_size) return -1;
            out_buffer[out_len++] = (uint8_t)((val >> bits) & 0xFF);
            bits -= 8;
        }
    }

    return (int)out_len;
}
