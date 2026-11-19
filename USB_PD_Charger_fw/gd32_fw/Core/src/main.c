#include "gd32f4xx.h"
#include "FreeRTOS.h"
#include "task.h"

typedef enum {
    FIRMWARE_FAULT_NONE = 0,
    FIRMWARE_FAULT_TASK_CREATE,
    FIRMWARE_FAULT_SCHEDULER_RETURNED,
    FIRMWARE_FAULT_ASSERT,
    FIRMWARE_FAULT_MALLOC,
    FIRMWARE_FAULT_STACK_OVERFLOW
} firmware_fault_t;

volatile firmware_fault_t g_firmware_fault = FIRMWARE_FAULT_NONE;
volatile uint32_t g_system_uptime_seconds = 0;

static void firmware_halt(firmware_fault_t fault)
{
    __disable_irq();
    g_firmware_fault = fault;
    for (;;) {
        __WFI();
    }
}

void firmware_assert_failed(void)
{
    firmware_halt(FIRMWARE_FAULT_ASSERT);
}

void vApplicationMallocFailedHook(void)
{
    firmware_halt(FIRMWARE_FAULT_MALLOC);
}

void vApplicationStackOverflowHook(TaskHandle_t task, char *name)
{
    (void)task;
    (void)name;
    firmware_halt(FIRMWARE_FAULT_STACK_OVERFLOW);
}

static void system_task(void *argument)
{
    (void)argument;
    TickType_t wake_time = xTaskGetTickCount();

    for (;;) {
        vTaskDelayUntil(&wake_time, pdMS_TO_TICKS(1000));
        ++g_system_uptime_seconds;
    }
}

int main(void)
{
    if (xTaskCreate(system_task, "system", configMINIMAL_STACK_SIZE,
                    NULL, tskIDLE_PRIORITY + 1U, NULL) != pdPASS) {
        firmware_halt(FIRMWARE_FAULT_TASK_CREATE);
    }

    vTaskStartScheduler();
    firmware_halt(FIRMWARE_FAULT_SCHEDULER_RETURNED);
}
