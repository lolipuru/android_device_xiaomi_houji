#
# Copyright (C) 2023 The Android Open Source Project
#
# SPDX-License-Identifier: Apache-2.0
#

DEVICE_PATH := device/xiaomi/houji
KERNEL_PATH := $(DEVICE_PATH)-kernel
TARGET_OPT_IN_OSS_KERNEL ?= true

# Inherit from sm8650-common
include device/xiaomi/sm8650-common/BoardConfigCommon.mk

# Display
TARGET_SCREEN_DENSITY := 440

# OTA
TARGET_OTA_ASSERT_DEVICE := houji,houjiin

# Properties
TARGET_ODM_PROP += $(DEVICE_PATH)/configs/properties/odm.prop

# SEPolicy
BOARD_VENDOR_SEPOLICY_DIRS += $(DEVICE_PATH)/sepolicy/vendor

# Inherit from the proprietary version
include vendor/xiaomi/houji/BoardConfigVendor.mk
include device/xiaomi/houji-miuicamera/BoardConfig.mk
