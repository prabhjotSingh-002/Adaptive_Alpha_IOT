#ifndef MUSTAFA_SPECK_H
#define MUSTAFA_SPECK_H

#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>

#define SPECK_TAG_SIZE 16u

void speck64_128_encrypt_block(const uint8_t key[16], const uint8_t in[8], uint8_t out[8]);
void speck64_128_decrypt_block(const uint8_t key[16], const uint8_t in[8], uint8_t out[8]);

bool lab_speck_seal(const uint8_t key[16], const uint8_t nonce[16],
                    const uint8_t *aad, size_t aad_len,
                    const uint8_t *plain, size_t plain_len,
                    uint8_t *out, size_t capacity, size_t *written);

bool lab_speck_open(const uint8_t key[16], const uint8_t nonce[16],
                    const uint8_t *aad, size_t aad_len,
                    const uint8_t *cipher, size_t cipher_len,
                    uint8_t *out, size_t capacity, size_t *written);

#endif /* MUSTAFA_SPECK_H */
