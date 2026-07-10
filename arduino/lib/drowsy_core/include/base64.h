#pragma once

#include <cstddef>
#include <cstdint>

// Decodifica una stringa base64 in byte grezzi. Ritorna il numero di byte
// scritti in out_buffer, o -1 se out_buffer e' troppo piccolo.
// Utility standard (nessuna logica di progetto) -- serve ad aes_decrypt per
// decodificare il payload MQTT prima di decifrarlo.
int base64_decode(const char* input, uint8_t* out_buffer, size_t out_buffer_size);
