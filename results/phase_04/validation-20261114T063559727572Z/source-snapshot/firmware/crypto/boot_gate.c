#include "boot_gate.h"
volatile uint8_t lab_boot_mailbox[LAB_BOOT_MAILBOX_SIZE] = {0};
static void clear_mailbox(void) {
  for(unsigned i = 0; i < LAB_BOOT_MAILBOX_SIZE; ++i) lab_boot_mailbox[i] = 0;
}
bool lab_boot_grant_pending(void) {
  return lab_boot_mailbox[0] == 0x42 && lab_boot_mailbox[1] == 0x54 &&
         lab_boot_mailbox[2] == 0x47 && lab_boot_mailbox[3] == 0x31;
}
void lab_boot_gate_init(lab_boot_gate *gate, lab_security_context *ctx,
                        uint16_t sender, uint16_t epoch, const uint8_t key[16]) {
  lab_boot_gate_init_profile(gate, ctx, 1, sender, epoch, key);
}
void lab_boot_gate_init_profile(lab_boot_gate *gate, lab_security_context *ctx,
                                uint8_t profile, uint16_t sender, uint16_t epoch,
                                const uint8_t key[16]) {
  if(!gate || !ctx) return;
  clear_mailbox();
  gate->consumed = false;
  lab_security_init_profile(ctx, profile, sender, epoch, key);
}
bool lab_boot_gate_poll(lab_boot_gate *gate, lab_security_context *ctx) {
  if(!gate || !ctx || gate->consumed || !lab_boot_grant_pending()) return false;
  clear_mailbox();
  gate->consumed = true;
  return lab_security_activate(ctx);
}
bool lab_boot_gate_poll_set(lab_boot_gate *gate, lab_security_context *contexts,
                            size_t count, const uint8_t *metadata,
                            const uint8_t *keys) {
  if(!gate || !contexts || !count || count > LAB_PROVISION_MAX_CONTEXTS || !metadata || !keys ||
     gate->consumed || !lab_boot_grant_pending()) return false;
  clear_mailbox();
  gate->consumed = true;
  for(size_t i = 0; i < count; ++i) {
    const uint8_t *m = metadata + i * LAB_PROVISION_SLOT_SIZE;
    lab_security_context *c = &contexts[i];
    if(m[0] != 1 || m[1] != c->profile ||
       (((uint16_t)m[2] << 8) | m[3]) != c->sender ||
       (((uint16_t)m[4] << 8) | m[5]) != c->epoch ||
       m[6] != 1 || m[7] != 0 || c->active || c->next_counter != 1 ||
       c->sender < 2 || !c->epoch) {
      for(size_t j = 0; j < count; ++j) lab_security_lock(&contexts[j]);
      return false;
    }
  }
  /* Cooperative execution: publish only after every declared slot validates. */
  for(size_t i = 0; i < count; ++i) {
    for(size_t j = 0; j < 16; ++j) contexts[i].key[j] = keys[i * 16 + j];
    if(!lab_security_activate(&contexts[i])) {
      for(size_t j = 0; j < count; ++j) lab_security_lock(&contexts[j]);
      return false;
    }
  }
  return true;
}
