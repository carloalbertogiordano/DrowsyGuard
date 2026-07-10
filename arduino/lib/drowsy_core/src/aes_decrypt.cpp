#include "aes_decrypt.h"
#include "base64.h"
#include "aes.hpp"
#include <cstring>
#include <stdlib.h>

int aes_decrypt(
    const char* base64_payload,
    const uint8_t* key,
    char* out_buffer,
    size_t out_buffer_size
) {
    uint8_t decoded[AES_DECRYPT_MAX_DECODED_SIZE];

    int dec_len = base64_decode(base64_payload, decoded, sizeof(decoded));
    
    if (dec_len < 0) {return -1;}

    if (dec_len < (AES_BLOCKLEN * 2)) {return -1;}

    uint8_t *IV = decoded; // first 16 bytes
    uint8_t *ciphertxt = decoded + AES_BLOCKLEN; //second 16 bytes
    int ciphertxt_len = dec_len - AES_BLOCKLEN;

    AES_ctx ctx;
    AES_init_ctx_iv(&ctx, key, IV);

    AES_CBC_decrypt_buffer(&ctx, ciphertxt, ciphertxt_len); //now ciphertxt has text + PKCS7 padding

    int plaintext_len = ciphertxt_len - ciphertxt[ciphertxt_len-1];
    if (plaintext_len >= out_buffer_size){return -1;}

    strncpy(out_buffer, (const char *)ciphertxt, plaintext_len);
    memset(out_buffer+plaintext_len, '\0', out_buffer_size-plaintext_len);

    return plaintext_len;
}
