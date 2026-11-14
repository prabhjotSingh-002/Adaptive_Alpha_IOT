#include "ascon_aead.h"
#include "crypto_aead.h"
#include <string.h>

static void wipe(void *p, size_t n) {
  volatile uint8_t *q = p;
  while(n--) *q++ = 0;
}

bool lab_ascon_seal(const uint8_t key[16], const uint8_t nonce[16],
                    const uint8_t *aad, size_t aad_len,
                    const uint8_t *plaintext, size_t len,
                    uint8_t *out, size_t capacity, size_t *out_len) {
  uint8_t input[LAB_ASCON_BODY_MAX] = {0};
  uint8_t result[LAB_ASCON_BODY_MAX + LAB_ASCON_TAG_SIZE] = {0};
  unsigned long long produced = 0;
  bool ok = false;
  if(out_len) *out_len = 0;
  if(!key || !nonce || !out || !out_len || (aad_len && !aad) ||
     (len && !plaintext) || aad_len > LAB_ASCON_AAD_MAX ||
     len > LAB_ASCON_BODY_MAX || capacity < len + LAB_ASCON_TAG_SIZE) goto done;
  if(len) memcpy(input, plaintext, len);
  if(crypto_aead_encrypt(result, &produced, input, len, aad, aad_len,
                         NULL, nonce, key) != 0 ||
     produced != len + LAB_ASCON_TAG_SIZE) goto done;
  memcpy(out, result, (size_t)produced);
  *out_len = (size_t)produced;
  ok = true;
done:
  wipe(input, sizeof input);
  wipe(result, sizeof result);
  return ok;
}

bool lab_ascon_open(const uint8_t key[16], const uint8_t nonce[16],
                    const uint8_t *aad, size_t aad_len,
                    const uint8_t *ciphertext, size_t len,
                    uint8_t *out, size_t capacity, size_t *out_len) {
  uint8_t input[LAB_ASCON_BODY_MAX + LAB_ASCON_TAG_SIZE] = {0};
  uint8_t result[LAB_ASCON_BODY_MAX] = {0};
  unsigned long long produced = 0;
  bool ok = false;
  if(out_len) *out_len = 0;
  if(!key || !nonce || !ciphertext || !out || !out_len ||
     (aad_len && !aad) || aad_len > LAB_ASCON_AAD_MAX ||
     len < LAB_ASCON_TAG_SIZE || len > sizeof input ||
     capacity < len - LAB_ASCON_TAG_SIZE) goto done;
  memcpy(input, ciphertext, len);
  if(crypto_aead_decrypt(result, &produced, NULL, input, len, aad, aad_len,
                         nonce, key) != 0 || produced != len - LAB_ASCON_TAG_SIZE) goto done;
  if(produced) memcpy(out, result, (size_t)produced);
  *out_len = (size_t)produced;
  ok = true;
done:
  wipe(input, sizeof input);
  wipe(result, sizeof result);
  return ok;
}
