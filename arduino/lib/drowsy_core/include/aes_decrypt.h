#pragma once

#include <cstdint>
#include <cstddef>

#define AES_DECRYPT_MAX_DECODED_SIZE 256

// Decifra un payload AES-256-CBC codificato in base64. Formato atteso
// (identico a SecurityManager.encrypt_data lato Python): i primi 16 byte
// decodificati sono l'IV, il resto e' il testo cifrato con padding PKCS7.
//
// key:              puntatore a 32 byte (256 bit) di chiave AES.
// base64_payload:   stringa C, il payload cifrato ricevuto via MQTT.
// out_buffer:       buffer di output per il testo decifrato (JSON in
//                   chiaro), scritto come stringa C (null-terminated).
// out_buffer_size:  dimensione di out_buffer.
//
// Ritorna: lunghezza del testo decifrato (senza padding, senza il \0), o -1
// in caso di errore (base64 invalido, buffer troppo piccolo, payload troppo
// corto per contenere IV+almeno un blocco).
int aes_decrypt(
    const char* base64_payload,
    const uint8_t* key,
    char* out_buffer,
    size_t out_buffer_size
);
