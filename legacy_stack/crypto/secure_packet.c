#include "secure_packet.h"
#include <limits.h>
#include <string.h>

#ifndef LAB_ENABLE_AES
#define LAB_ENABLE_AES 0
#endif
#ifndef LAB_ENABLE_SPECK
#define LAB_ENABLE_SPECK 0
#endif
#ifndef LAB_ENABLE_PRESENT
#define LAB_ENABLE_PRESENT 0
#endif

#if LAB_ENABLE_AES
#include "aes_ccm.h"
#endif
#if LAB_ENABLE_SPECK
#include "speck.h"
#endif
#if LAB_ENABLE_PRESENT
#include "present.h"
#endif

static void wipe(void *ptr, size_t len) {
  volatile uint8_t *p = ptr;
  while(len--) *p++ = 0;
}

void lab_security_init(lab_security_context *ctx, uint16_t sender, uint16_t epoch,
                       const uint8_t key[LAB_CCM_KEY_SIZE]) {
  lab_security_init_profile(ctx, LAB_SECURE_PROFILE, sender, epoch, key);
}

void lab_security_init_profile(lab_security_context *ctx, uint8_t profile,
                               uint16_t sender, uint16_t epoch, const uint8_t key[16]) {
  if(!ctx) return;
  memset(ctx, 0, sizeof *ctx);
  if(!key || sender < 2 || !epoch) return;
  memcpy(ctx->key, key, LAB_CCM_KEY_SIZE);
  ctx->sender = sender; ctx->epoch = epoch; ctx->profile = profile; ctx->next_counter = 1;
}

bool lab_security_activate(lab_security_context *ctx) {
  if(!ctx || ctx->active || ctx->sender < 2 || !ctx->epoch || ctx->next_counter != 1) return false;
  ctx->active = true;
  return true;
}

void lab_security_lock(lab_security_context *ctx) {
  if(ctx) { ctx->active = false; ctx->next_counter = UINT32_MAX; }
}

bool lab_security_nonce(uint16_t sender, uint16_t epoch, uint32_t counter,
                        uint8_t nonce[LAB_CCM_NONCE_SIZE]) {
  if(!nonce || sender < 2 || !epoch || !counter || counter == UINT32_MAX) return false;
  nonce[0] = 0x52; nonce[1] = 0x53; nonce[2] = 0x4c;
  nonce[3] = LAB_SECURE_PROFILE; nonce[4] = 0;
  nonce[5] = (uint8_t)(sender >> 8); nonce[6] = (uint8_t)sender;
  nonce[7] = (uint8_t)(epoch >> 8); nonce[8] = (uint8_t)epoch;
  nonce[9] = (uint8_t)(counter >> 24); nonce[10] = (uint8_t)(counter >> 16);
  nonce[11] = (uint8_t)(counter >> 8); nonce[12] = (uint8_t)counter;
  return true;
}

static bool context_nonce(const lab_security_context *ctx, uint32_t counter, uint8_t nonce[16]) {
  if(!lab_security_nonce(ctx->sender, ctx->epoch, counter, nonce)) return false;
  nonce[3] = ctx->profile;
  nonce[13] = nonce[14] = nonce[15] = 0;
  return true;
}

static bool seal_body(const lab_security_context *ctx, const uint8_t nonce[16],
                      const uint8_t *aad, const uint8_t *body, size_t len,
                      uint8_t *out, size_t cap, size_t *written) {
#if LAB_ENABLE_AES
  if(ctx->profile == LAB_SECURE_PROFILE)
    return lab_ccm_seal(ctx->key, nonce, aad, LAB_HEADER, body, len, out, cap, written);
#endif
#if LAB_ENABLE_SPECK
  if(ctx->profile == LAB_SPECK_PROFILE)
    return lab_speck_seal(ctx->key, nonce, aad, LAB_HEADER, body, len, out, cap, written);
#endif
#if LAB_ENABLE_PRESENT
  if(ctx->profile == LAB_PRESENT_PROFILE)
    return lab_present_seal(ctx->key, nonce, aad, LAB_HEADER, body, len, out, cap, written);
#endif
  return false;
}

static bool open_body(const lab_security_context *ctx, const uint8_t nonce[16],
                      const uint8_t *aad, const uint8_t *body, size_t len,
                      uint8_t *out, size_t cap, size_t *written) {
#if LAB_ENABLE_AES
  if(ctx->profile == LAB_SECURE_PROFILE)
    return lab_ccm_open(ctx->key, nonce, aad, LAB_HEADER, body, len, out, cap, written);
#endif
#if LAB_ENABLE_SPECK
  if(ctx->profile == LAB_SPECK_PROFILE)
    return lab_speck_open(ctx->key, nonce, aad, LAB_HEADER, body, len, out, cap, written);
#endif
#if LAB_ENABLE_PRESENT
  if(ctx->profile == LAB_PRESENT_PROFILE)
    return lab_present_open(ctx->key, nonce, aad, LAB_HEADER, body, len, out, cap, written);
#endif
  return false;
}

bool lab_secure_seal(lab_security_context *ctx, const lab_batch *batch,
                     uint8_t *out, size_t capacity, size_t *out_len) {
  uint8_t plain[LAB_PACKET_MAX] = {0}, wire[LAB_SECURE_PACKET_MAX] = {0}, nonce[16] = {0};
  lab_batch tmp;
  size_t plain_len, protected_len = 0;
  bool ok = false;
  if(out_len) *out_len = 0;
  if(!ctx || !ctx->active || !batch || !out || !out_len ||
     ctx->sender != batch->sender || ctx->next_counter == UINT32_MAX) return false;
  tmp = *batch;
  tmp.profile = 0; tmp.epoch = 0; tmp.counter = ctx->next_counter;
  plain_len = lab_encode(&tmp, plain, sizeof plain);
  if(!plain_len || capacity < plain_len + LAB_CCM_TAG_SIZE ||
     !context_nonce(ctx, ctx->next_counter, nonce)) goto done;
  memcpy(wire, plain, LAB_HEADER);
  wire[3] = ctx->profile;
  wire[4] = (uint8_t)(ctx->epoch >> 8); wire[5] = (uint8_t)ctx->epoch;
  ctx->next_counter++;
  if(!seal_body(ctx, nonce, wire, plain + LAB_HEADER,
                   plain_len - LAB_HEADER, wire + LAB_HEADER,
                   sizeof wire - LAB_HEADER, &protected_len)) goto done;
  memcpy(out, wire, LAB_HEADER + protected_len);
  *out_len = LAB_HEADER + protected_len;
  ok = true;
done:
  wipe(plain, sizeof plain); wipe(wire, sizeof wire); wipe(nonce, sizeof nonce); wipe(&tmp, sizeof tmp);
  return ok;
}

lab_open_status lab_secure_open_status(lab_security_context *ctx,
                                      const uint8_t *packet, size_t length,
                                      lab_batch *out) {
  uint8_t wire[LAB_SECURE_PACKET_MAX] = {0}, plain[LAB_PACKET_MAX] = {0}, nonce[16] = {0};
  uint16_t sender, epoch;
  uint8_t profile;
  uint32_t counter;
  size_t plain_body_len = 0;
  lab_open_status st = LAB_OPEN_FORMAT;
  if(!ctx || !packet || !out) return LAB_OPEN_CONTEXT;
  if(length < LAB_HEADER + LAB_CCM_TAG_SIZE || length > sizeof wire) return LAB_OPEN_FORMAT;
  memcpy(wire, packet, length);
  sender = ((uint16_t)wire[1] << 8) | wire[2];
  profile = wire[3];
  epoch = ((uint16_t)wire[4] << 8) | wire[5];
  counter = ((uint32_t)wire[6] << 24) | ((uint32_t)wire[7] << 16) | ((uint32_t)wire[8] << 8) | wire[9];
  if(sender != ctx->sender) { st = LAB_OPEN_CONTEXT; goto done; }
  if(profile != ctx->profile) { st = LAB_OPEN_PROFILE; goto done; }
  if(!ctx->active) { st = LAB_OPEN_LOCKED; goto done; }
  if(epoch != ctx->epoch || !counter || !lab_mark_new(&ctx->received, counter)) { st = LAB_OPEN_REPLAY; goto done; }
  if(!context_nonce(ctx, counter, nonce)) { st = LAB_OPEN_FORMAT; goto done; }
  if(!open_body(ctx, nonce, wire, wire + LAB_HEADER,
                   length - LAB_HEADER, plain + LAB_HEADER,
                   sizeof plain - LAB_HEADER, &plain_body_len)) {
    st = LAB_OPEN_AUTH; goto done;
  }
  memcpy(plain, wire, LAB_HEADER);
  plain[3] = 0; plain[4] = 0; plain[5] = 0;
  if(!lab_decode(plain, LAB_HEADER + plain_body_len, out)) { st = LAB_OPEN_BODY; goto done; }
  out->sender = sender; out->epoch = epoch; out->profile = profile; out->counter = counter;
  st = LAB_OPEN_OK;
done:
  wipe(wire, sizeof wire); wipe(plain, sizeof plain); wipe(nonce, sizeof nonce);
  return st;
}

bool lab_secure_open(lab_security_context *ctx, const uint8_t *packet,
                     size_t length, lab_batch *out) {
  return lab_secure_open_status(ctx, packet, length, out) == LAB_OPEN_OK;
}
