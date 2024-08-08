#
# Copyright (C) 2023 The Android Open Source Project
#
# SPDX-License-Identifier: Apache-2.0
#

DEVICE_PATH := device/xiaomi/houji

# Inherit from sm8650-common
include device/xiaomi/sm8650-common/BoardConfigCommon.mk

# Display
TARGET_SCREEN_DENSITY := 440

# OTA
TARGET_OTA_ASSERT_DEVICE := houji

# Properties
TARGET_ODM_PROP += $(DEVICE_PATH)/configs/properties/odm.prop
