#ifndef LAB_ENERGEST_SAMPLER_H
#define LAB_ENERGEST_SAMPLER_H
#include <stdbool.h>
bool lab_energy_is_depleted(void);
void lab_application_deplete(void);
void lab_energy_telemetry_start(void);
#endif
