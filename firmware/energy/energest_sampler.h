#ifndef LAB_ENERGEST_SAMPLER_H
#define LAB_ENERGEST_SAMPLER_H
#include <stdint.h>
#include <stdbool.h>
bool lab_energy_is_depleted(void);
uint64_t lab_energy_remaining_nj(void);
void lab_application_deplete(void);
void lab_energy_telemetry_start(void);
#endif
