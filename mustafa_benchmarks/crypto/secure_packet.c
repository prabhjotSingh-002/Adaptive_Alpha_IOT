#include "secure_packet.h"
#include <limits.h>
#include <string.h>
#ifdef LAB_ENABLE_ASCON
#include "ascon_aead.h"
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
  if(!key || sender < 2 || !epoch || (profile != LAB_SECURE_PROFILE
#ifdef LAB_ENABLE_ASCON
     && profile != LAB_ASCON_PROFILE
#endif
     && profile != LAB_SPECK_PROFILE
     && profile != LAB_PRESENT_PROFILE
     )) return;
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
  if(ctx->profile == LAB_SECURE_PROFILE)
    return lab_ccm_seal(ctx->key, nonce, aad, LAB_HEADER, body, len, out, cap, written);
#ifdef LAB_ENABLE_ASCON
  if(ctx->profile == LAB_ASCON_PROFILE)
    return lab_ascon_seal(ctx->key, nonce, aad, LAB_HEADER, body, len, out, cap, written);
#endif
  if(ctx->profile == LAB_SPECK_PROFILE)
    return lab_speck_seal(ctx->key, nonce, aad, LAB_HEADER, body, len, out, cap, written);
  if(ctx->profile == LAB_PRESENT_PROFILE)
    return lab_present_seal(ctx->key, nonce, aad, LAB_HEADER, body, len, out, cap, written);
  return false;
}

static bool open_body(const lab_security_context *ctx, const uint8_t nonce[16],
                      const uint8_t *aad, const uint8_t *body, size_t len,
                      uint8_t *out, size_t cap, size_t *written) {
  if(ctx->profile == LAB_SECURE_PROFILE)
    return lab_ccm_open(ctx->key, nonce, aad, LAB_HEADER, body, len, out, cap, written);
#ifdef LAB_ENABLE_ASCON
  if(ctx->profile == LAB_ASCON_PROFILE)
    return lab_ascon_open(ctx->key, nonce, aad, LAB_HEADER, body, len, out, cap, written);
#endif
  if(ctx->profile == LAB_SPECK_PROFILE)
    return lab_speck_open(ctx->key, nonce, aad, LAB_HEADER, body, len, out, cap, written);
  if(ctx->profile == LAB_PRESENT_PROFILE)
    return lab_present_open(ctx->key, nonce, aad, LAB_HEADER, body, len, out, cap, written);
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

lab_open_status lab_secure_open_status(lab_security_context *ctx, const uint8_t *packet,
                     size_t length, lab_batch *out) {
  uint8_t plain[LAB_PACKET_MAX] = {0}, nonce[16] = {0};
  size_t body_len = 0;
  lab_batch tmp;
  lab_seen candidate;
  lab_open_status status = LAB_OPEN_FORMAT;
  if(!ctx || !packet || !out) return LAB_OPEN_FORMAT;
  if(!ctx->active) return LAB_OPEN_LOCKED;
  if(
     length < LAB_HEADER + LAB_READING_BYTES + LAB_CCM_TAG_SIZE ||
     length > LAB_SECURE_PACKET_MAX || packet[0] != 1 ||
     packet[10] == 0 || packet[10] > LAB_CAPACITY ||
     length != LAB_HEADER + (size_t)packet[10] * LAB_READING_BYTES + LAB_CCM_TAG_SIZE) return LAB_OPEN_FORMAT;
  if(packet[3] != ctx->profile) return LAB_OPEN_PROFILE;
  uint16_t sender = (uint16_t)(((uint16_t)packet[1] << 8) | packet[2]);
  uint16_t epoch = (uint16_t)(((uint16_t)packet[4] << 8) | packet[5]);
  uint32_t counter = ((uint32_t)packet[6] << 24) | ((uint32_t)packet[7] << 16) |
                     ((uint32_t)packet[8] << 8) | packet[9];
  status = LAB_OPEN_CONTEXT;
  if(sender != ctx->sender || epoch != ctx->epoch ||
     !context_nonce(ctx, counter, nonce)) goto done;
  candidate = ctx->received;
  status = LAB_OPEN_REPLAY;
  if(!lab_mark_new(&candidate, counter)) goto done;
  memcpy(plain, packet, LAB_HEADER); plain[3] = 0; plain[4] = 0; plain[5] = 0;
  status = LAB_OPEN_AUTH;
  if(!open_body(ctx, nonce, packet, packet + LAB_HEADER,
                   length - LAB_HEADER, plain + LAB_HEADER,
                   sizeof plain - LAB_HEADER, &body_len)) goto done;
  status = LAB_OPEN_BODY;
  if(!lab_decode(plain, LAB_HEADER + body_len, &tmp)) goto done;
  tmp.profile = ctx->profile; tmp.epoch = epoch;
  ctx->received = candidate;
  *out = tmp; status = LAB_OPEN_OK;
done:
  wipe(plain, sizeof plain); wipe(nonce, sizeof nonce); wipe(&tmp, sizeof tmp);
  return status;
}

bool lab_secure_open(lab_security_context *ctx, const uint8_t *packet,
                     size_t length, lab_batch *out) {
  return lab_secure_open_status(ctx, packet, length, out) == LAB_OPEN_OK;
}
