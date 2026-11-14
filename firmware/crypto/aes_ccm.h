#ifndef LAB_AES_CCM_H
#define LAB_AES_CCM_H
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#define LAB_CCM_KEY_SIZE 16u
#define LAB_CCM_NONCE_SIZE 13u
#define LAB_CCM_TAG_SIZE 16u
#define LAB_CCM_BODY_MAX 40u
#define LAB_CCM_AAD_MAX 32u
/* The backend has a shared key schedule. Calls must not be interleaved.
 * Output is committed only on success; input/output may alias. */
bool lab_ccm_seal(const uint8_t key[16], const uint8_t nonce[13],
                  const uint8_t *aad, size_t aad_len,
                  const uint8_t *plaintext, size_t len,
                  uint8_t *out, size_t out_cap, size_t *out_len);
bool lab_ccm_open(const uint8_t key[16], const uint8_t nonce[13],
                  const uint8_t *aad, size_t aad_len,
                  const uint8_t *ciphertext_and_tag, size_t len,
                  uint8_t *out, size_t out_cap, size_t *out_len);
#endif
