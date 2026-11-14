#ifndef LAB_ASCON_AEAD_H
#define LAB_ASCON_AEAD_H
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#define LAB_ASCON_KEY_SIZE 16u
#define LAB_ASCON_NONCE_SIZE 16u
#define LAB_ASCON_TAG_SIZE 16u
#define LAB_ASCON_BODY_MAX 40u
#define LAB_ASCON_AAD_MAX 32u
bool lab_ascon_seal(const uint8_t key[16], const uint8_t nonce[16],
                    const uint8_t *aad, size_t aad_len,
                    const uint8_t *plaintext, size_t len,
                    uint8_t *out, size_t capacity, size_t *out_len);
bool lab_ascon_open(const uint8_t key[16], const uint8_t nonce[16],
                    const uint8_t *aad, size_t aad_len,
                    const uint8_t *ciphertext, size_t len,
                    uint8_t *out, size_t capacity, size_t *out_len);
#endif
