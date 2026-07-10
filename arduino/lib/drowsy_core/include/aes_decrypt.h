#pragma once

#include <cstdint>
#include <cstddef>

#define AES_DECRYPT_MAX_DECODED_SIZE 256

// Decrypts a base64-encoded AES-256-CBC payload. Expected format
// (identical to SecurityManager.encrypt_data on the Python side): the
// first 16 decoded bytes are the IV, the rest is the ciphertext with
// PKCS7 padding.
//
// key:              pointer to 32 bytes (256 bits) of AES key.
// base64_payload:   C string, the encrypted payload received via MQTT.
// out_buffer:       output buffer for the decrypted plaintext (JSON),
//                   written as a C string (null-terminated).
// out_buffer_size:  size of out_buffer.
//
// Returns: length of the decrypted text (without padding, without the
// \0), or -1 on error (invalid base64, buffer too small, payload too
// short to contain IV+at least one block).
int aes_decrypt(
    const char* base64_payload,
    const uint8_t* key,
    char* out_buffer,
    size_t out_buffer_size
);
