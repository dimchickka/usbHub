#ifndef FREERTOS_CONFIG_H
#define FREERTOS_CONFIG_H

#include <stdint.h>

/* SystemInit() configures the clock before main() starts. */
extern uint32_t SystemCoreClock;

#define configCPU_CLOCK_HZ                         ( SystemCoreClock )
#define configTICK_RATE_HZ                         1000U
#define configUSE_PREEMPTION                       1
#define configUSE_IDLE_HOOK                        0
#define configUSE_TICK_HOOK                        0
#define configMAX_PRIORITIES                       5
#define configMINIMAL_STACK_SIZE                   128U
#define configMAX_TASK_NAME_LEN                    16
#define configTICK_TYPE_WIDTH_IN_BITS              TICK_TYPE_WIDTH_32_BITS
#define configTOTAL_HEAP_SIZE                      ( 16U * 1024U )
#define configSUPPORT_DYNAMIC_ALLOCATION           1
#define configSUPPORT_STATIC_ALLOCATION            0
#define configUSE_TIMERS                           0
#define configUSE_MUTEXES                          1
#define configUSE_COUNTING_SEMAPHORES              1
#define configUSE_TASK_NOTIFICATIONS               1
#define configUSE_NEWLIB_REENTRANT                 0
#define configCHECK_FOR_STACK_OVERFLOW             2
#define configUSE_MALLOC_FAILED_HOOK               1

#define INCLUDE_vTaskDelay                         1
#define INCLUDE_xTaskDelayUntil                    1

/* GD32F470 implements four NVIC priority bits. ISRs using FreeRTOS APIs
 * must have a numerical priority of 5 or greater. */
#define configPRIO_BITS                            4
#define configLIBRARY_LOWEST_INTERRUPT_PRIORITY    15
#define configLIBRARY_MAX_SYSCALL_INTERRUPT_PRIORITY 5
#define configKERNEL_INTERRUPT_PRIORITY            ( configLIBRARY_LOWEST_INTERRUPT_PRIORITY << ( 8 - configPRIO_BITS ) )
#define configMAX_SYSCALL_INTERRUPT_PRIORITY       ( configLIBRARY_MAX_SYSCALL_INTERRUPT_PRIORITY << ( 8 - configPRIO_BITS ) )
#define configCHECK_HANDLER_INSTALLATION           1

/* Match the symbols in startup_gd32f450_470.S. */
#define vPortSVCHandler                            SVC_Handler
#define xPortPendSVHandler                         PendSV_Handler
#define xPortSysTickHandler                        SysTick_Handler

void firmware_assert_failed(void);
#define configASSERT(expression)                   do { if (!(expression)) { firmware_assert_failed(); } } while (0)

#endif
