
#
# Copyright (C) 2023 The Android Open Source Project
#
# SPDX-License-Identifier: Apache-2.0
#

# Inherit from sm8650-common
$(call inherit-product, device/xiaomi/sm8650-common/common.mk)

# Get non-open-source specific aspects
$(call inherit-product, vendor/xiaomi/houji/houji-vendor.mk)

# Audio
PRODUCT_COPY_FILES += \
    $(LOCAL_PATH)/configs/audio/mixer_paths_pineapple_mtp.xml:$(TARGET_COPY_OUT_VENDOR)/etc/audio/sku_pineapple/mixer_paths_pineapple_mtp.xml \
    $(LOCAL_PATH)/configs/audio/resourcemanager_pineapple_mtp.xml:$(TARGET_COPY_OUT_VENDOR)/etc/audio/sku_pineapple/resourcemanager_pineapple_mtp.xml

# Euicc
PRODUCT_COPY_FILES += \
    $(LOCAL_PATH)/configs/permissions/privapp-permissions-euiccgoogle.xml:$(TARGET_COPY_OUT_PRODUCT)/etc/permissions/privapp-permissions-euiccgoogle.xml

PRODUCT_PACKAGES += \
    XiaomiEuicc \
    DeviceSettings

PRODUCT_BROKEN_VERIFY_USES_LIBRARIES := true

# init
PRODUCT_COPY_FILES += \
    $(LOCAL_PATH)/init/init.houji.rc:$(TARGET_COPY_OUT_VENDOR)/etc/init/init.houji.rc \

# Soong namespaces
PRODUCT_SOONG_NAMESPACES += \
    $(LOCAL_PATH)

# Overlays
PRODUCT_PACKAGES += \
    FrameworksResHouji \
    HoujiEuiccOverlay \
    SettingsOverlayHouji \
    SystemUIResHouji