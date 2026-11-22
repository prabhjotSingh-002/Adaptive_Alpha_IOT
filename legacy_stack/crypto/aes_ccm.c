#include "aes_ccm.h"
#include "lib/ccm-star.h"
#include <string.h>

static void wipe(void *ptr, size_t length) {
  volatile uint8_t *p = (volatile uint8_t *)ptr;
  while(length--) *p++ = 0;
}
static bool inputs_ok(const uint8_t *key, const uint8_t *nonce,
                      const uint8_t *aad, size_t aad_len) {
  return key && nonce && aad_len <= LAB_CCM_AAD_MAX && (aad || !aad_len);
}
bool lab_ccm_seal(const uint8_t key[16], const uint8_t nonce[13],
                  const uint8_t *aad, size_t aad_len,
                  const uint8_t *plaintext, size_t len,
                  uint8_t *out, size_t out_cap, size_t *out_len) {
  uint8_t scratch[LAB_CCM_BODY_MAX + LAB_CCM_TAG_SIZE] = {0};
  if(out_len) *out_len = 0;
  if(!out_len || !inputs_ok(key, nonce, aad, aad_len) || len > LAB_CCM_BODY_MAX ||
     (!plaintext && len) || !out || out_cap < len + LAB_CCM_TAG_SIZE) return false;
  if(len) memcpy(scratch, plaintext, len);
  CCM_STAR.set_key(key);
  CCM_STAR.aead(nonce, scratch, (uint16_t)len, aad, (uint16_t)aad_len,
                scratch + len, LAB_CCM_TAG_SIZE, 1);
  memcpy(out, scratch, len + LAB_CCM_TAG_SIZE);
  *out_len = len + LAB_CCM_TAG_SIZE;
  wipe(scratch, sizeof scratch);
  return true;
}
bool lab_ccm_open(const uint8_t key[16], const uint8_t nonce[13],
                  const uint8_t *aad, size_t aad_len,
                  const uint8_t *ciphertext_and_tag, size_t len,
                  uint8_t *out, size_t out_cap, size_t *out_len) {
  uint8_t scratch[LAB_CCM_BODY_MAX] = {0}, tag[LAB_CCM_TAG_SIZE] = {0};
  uint8_t diff = 0;
  if(out_len) *out_len = 0;
  if(!out_len || !inputs_ok(key, nonce, aad, aad_len) || !ciphertext_and_tag ||
     len < LAB_CCM_TAG_SIZE || len - LAB_CCM_TAG_SIZE > LAB_CCM_BODY_MAX ||
     !out || out_cap < len - LAB_CCM_TAG_SIZE) return false;
  size_t body_len = len - LAB_CCM_TAG_SIZE;
  if(body_len) memcpy(scratch, ciphertext_and_tag, body_len);
  CCM_STAR.set_key(key);
  CCM_STAR.aead(nonce, scratch, (uint16_t)body_len, aad, (uint16_t)aad_len,
                tag, LAB_CCM_TAG_SIZE, 0);
  for(size_t i = 0; i < LAB_CCM_TAG_SIZE; i++)
    diff |= (uint8_t)(tag[i] ^ ciphertext_and_tag[body_len + i]);
  if(!diff) {
    if(body_len) memcpy(out, scratch, body_len);
    *out_len = body_len;
  }
  wipe(scratch, sizeof scratch);
  wipe(tag, sizeof tag);
  return diff == 0;
}
