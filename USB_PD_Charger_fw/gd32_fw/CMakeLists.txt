
cmake_minimum_required(VERSION 3.22)

project(gd32_fw LANGUAGES C ASM)

set(CMAKE_C_STANDARD 11)

# Путь к библиотеке GD32
set(GD32_SDK
    "${CMAKE_CURRENT_SOURCE_DIR}/external/GD32F4xx_Firmware_Library/Firmware"
)

set(FREERTOS_KERNEL
    "${CMAKE_CURRENT_SOURCE_DIR}/external/FreeRTOS-Kernel"
)

# Линкерный скрипт
set(LINKER_SCRIPT
    "${CMAKE_CURRENT_SOURCE_DIR}/gd32f470xG_flash.ld"
)

# Исходные файлы
add_executable(gd32_fw
    Core/src/main.c
    startup/startup_gd32f450_470.S

    ${GD32_SDK}/CMSIS/GD/GD32F4xx/Source/system_gd32f4xx.c
    ${GD32_SDK}/GD32F4xx_standard_peripheral/Source/gd32f4xx_misc.c

    ${FREERTOS_KERNEL}/tasks.c
    ${FREERTOS_KERNEL}/list.c
    ${FREERTOS_KERNEL}/queue.c
    ${FREERTOS_KERNEL}/portable/GCC/ARM_CM4F/port.c
    ${FREERTOS_KERNEL}/portable/MemMang/heap_4.c
)


# Пути к заголовочным файлам
target_include_directories(gd32_fw PRIVATE
    Core/inc
    ${GD32_SDK}/CMSIS
    ${GD32_SDK}/CMSIS/GD/GD32F4xx/Include
    ${GD32_SDK}/GD32F4xx_standard_peripheral/Include
    ${FREERTOS_KERNEL}/include
    ${FREERTOS_KERNEL}/portable/GCC/ARM_CM4F
)

# Модель микроконтроллера
target_compile_definitions(gd32_fw PRIVATE
    GD32F470
    HXTAL_VALUE=12000000
)

# Настройки процессора
set(MCU_FLAGS
    -mcpu=cortex-m4
    -mthumb
    -mfpu=fpv4-sp-d16
    -mfloat-abi=hard
)

target_compile_options(gd32_fw PRIVATE
    ${MCU_FLAGS}
    -ffunction-sections
    -fdata-sections
    -Wall
    -Wextra
)

target_link_options(gd32_fw PRIVATE
    ${MCU_FLAGS}
    -T${LINKER_SCRIPT}
    -Wl,--gc-sections
    --specs=nosys.specs
)

set_target_properties(gd32_fw PROPERTIES
    SUFFIX ".elf"
    LINK_DEPENDS "${LINKER_SCRIPT}"
)
