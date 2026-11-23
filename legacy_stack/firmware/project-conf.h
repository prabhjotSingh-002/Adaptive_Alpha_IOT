#ifndef PROJECT_CONF_H_
#define PROJECT_CONF_H_

#undef NETSTACK_CONF_MAC
#define NETSTACK_CONF_MAC csma_driver

#undef NETSTACK_CONF_RDC
#define NETSTACK_CONF_RDC contikimac_driver

#undef NETSTACK_CONF_RDC_CHANNEL_CHECK_RATE
#define NETSTACK_CONF_RDC_CHANNEL_CHECK_RATE 8

#undef NETSTACK_CONF_FRAMER
#define NETSTACK_CONF_FRAMER framer_802154

/* Energest & Telemetry */
#define ENERGEST_CONF_ON 1

/* Channel & Power matching Mustafa Table 3 */
#define CC2420_CONF_CHANNEL 26
#define CC2420_CONF_AUTOACK 1

/* IPv6 & RPL */
#define UIP_CONF_ROUTER 1
#define UIP_CONF_IPV6_RPL 1

/* Queue Buffers & MAC Retransmissions */
#ifdef IS_ROOT
#undef QUEUEBUF_CONF_NUM
#define QUEUEBUF_CONF_NUM 4
#else
#undef QUEUEBUF_CONF_NUM
#define QUEUEBUF_CONF_NUM 8
#endif

#undef CSMA_CONF_MAX_MAC_TRANSMISSIONS
#define CSMA_CONF_MAX_MAC_TRANSMISSIONS 5

#endif /* PROJECT_CONF_H_ */
