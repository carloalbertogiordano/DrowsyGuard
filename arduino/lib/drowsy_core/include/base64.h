#pragma once

#include <cstddef>
#include <cstdint>

// Decodes a base64 string into raw bytes. Returns the number of bytes
// written into out_buffer, or -1 if out_buffer is too small.
// Standard utility (no project-specific logic) -- used by aes_decrypt to
// decode the MQTT payload before decrypting it.
int base64_decode(const char* input, uint8_t* out_buffer, size_t out_buffer_size);
