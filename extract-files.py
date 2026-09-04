#!/usr/bin/env -S PYTHONPATH=../../../tools/extract-utils python3
#
# SPDX-FileCopyrightText: 2024 The LineageOS Project
# SPDX-License-Identifier: Apache-2.0
#

import extract_utils.tools
from extract_utils.fixups_blob import (
    BlobFixupCtx,
    File,
    blob_fixup,
    blob_fixups_user_type,
)
from extract_utils.fixups_lib import (
    lib_fixup_remove,
    lib_fixups,
    lib_fixups_user_type,
)
from extract_utils.main import (
    ExtractUtils,
    ExtractUtilsModule,
)
from extract_utils.tools import (
    llvm_objdump_path,
)
from extract_utils.utils import (
    run_cmd,
)

namespace_imports = [
    'device/xiaomi/sm8650-common',
    'hardware/qcom-caf/sm8650',
    'hardware/xiaomi',
    'vendor/qcom/opensource/commonsys-intf/display',
    'vendor/xiaomi/sm8650-common',
]

def blob_fixup_graphic_buffer_size(
    ctx: BlobFixupCtx,
    file: File,
    file_path: str,
    disassemble_symbols: [str],
    *args,
    **kwargs,
):
    for line in run_cmd(
        [
            llvm_objdump_path,
            f'--disassemble-symbols={",".join(disassemble_symbols)}',
            file_path,
        ]
    ).splitlines():
        line = line.split(maxsplit=5)
        if len(line) != 6:
            continue

        # The size of GraphicBuffer changed from 0x100 to 0xd30
        offset, _, instruction, register, value, _ = line
        if instruction == 'mov' and register[:-1] == 'w0' and value == '#0x100':
            with open(file_path, 'rb+') as f:
                f.seek(int(offset[:-1], 16))
                f.write(b'\x00\xa6\x81\x52')  # AArch64 mov w0, #0xd30

def blob_fixup_mfnr_vendor_tag(
    ctx: BlobFixupCtx,
    file: File,
    file_path: str,
    *args,
    **kwargs,
):
    offset = 0xed9d4

    original = bytes.fromhex(
        '40 FC FF D0 00 40 14 91'
    )
    patched = bytes.fromhex(
        '00 FC FF B0 00 B0 09 91'
    )

    with open(file_path, 'rb+') as f:
        f.seek(offset)
        current = f.read(len(original))

        if current == patched:
            return

        if current != original:
            raise ValueError(
                f'Unexpected camera.xiaomi.so data at 0x{offset:x}: '
                f'{current.hex(" ")}'
            )

        f.seek(offset)
        f.write(patched)

def blob_fixup_fake_sat_sr_buffer_size(
    ctx: BlobFixupCtx,
    file: File,
    file_path: str,
    *args,
    **kwargs,
):
    # Use the full-resolution FakeSat stream for super-resolution captures.
    offset = 0xdf5dc
    original = bytes.fromhex('22 00 80 52')  # mov w2, #1
    patched = bytes.fromhex('62 00 80 52')   # mov w2, #3

    with open(file_path, 'rb+') as f:
        f.seek(offset)
        current = f.read(len(original))

        if current == patched:
            return

        if current != original:
            raise ValueError(
                f'Unexpected camera.xiaomi.so data at 0x{offset:x}: '
                f'{current.hex(" ")}'
            )

        f.seek(offset)
        f.write(patched)

def blob_fixup_camera_reconfiguration_query(
    ctx: BlobFixupCtx,
    file: File,
    file_path: str,
    *args,
    **kwargs,
):
    patches = (
        (
            0x47414,
            bytes.fromhex(
                '28 00 80 52 '  # mov w8, #1
                '80 00 80 52'   # mov w0, #4
            ),
            bytes.fromhex(
                '08 00 80 52 '  # mov w8, #0
                '00 00 80 52'   # mov w0, #0
            ),
        ),
        (
            0x47460,
            bytes.fromhex(
                '80 00 80 52 '  # mov w0, #4
                '28 00 80 52'   # mov w8, #1
            ),
            bytes.fromhex(
                '00 00 80 52 '  # mov w0, #0
                '08 00 80 52'   # mov w8, #0
            ),
        ),
    )

    with open(file_path, 'rb+') as f:
        for offset, original, patched in patches:
            f.seek(offset)
            current = f.read(len(original))

            if current == patched:
                continue

            if current != original:
                raise ValueError(
                    f'Unexpected camx.device-impl.so data at 0x{offset:x}: '
                    f'{current.hex(" ")}'
                )

            f.seek(offset)
            f.write(patched)


blob_fixups: blob_fixups_user_type = {
    (
        'odm/etc/camera/enhance_motiontuning.xml',
        'odm/etc/camera/night_motiontuning.xml',
        'odm/etc/camera/motiontuning.xml'
    ): blob_fixup()
        .regex_replace('xml=version', 'xml version'),
    (
        'odm/lib64/libcamxcommonutils.so',
        'odm/lib64/libmialgoengine.so',
        'vendor/lib64/libcameraopt.so',
    ): blob_fixup()
        .add_needed('libprocessgroup_shim.so'),
    (
        'odm/lib64/libsnpe_config.so',
    ): blob_fixup()
        .add_needed('liblog.so'),

    'odm/lib64/camx.device-impl.so': blob_fixup()
        .call(blob_fixup_camera_reconfiguration_query),

    (
        'odm/lib64/hw/camera.qcom.so',
        'odm/lib64/hw/com.qti.chi.override.so',
        'odm/lib64/libchifeature2.so',
    ): blob_fixup()
        .add_needed('libprocessgroup_shim.so')
        .replace_needed(
            'android.hardware.graphics.allocator-V1-ndk.so',
            'android.hardware.graphics.allocator-V2-ndk.so'
        ),

    'odm/lib64/hw/camera.xiaomi.so': blob_fixup()
        .add_needed('libprocessgroup_shim.so')
        .replace_needed(
            'android.hardware.graphics.allocator-V1-ndk.so',
            'android.hardware.graphics.allocator-V2-ndk.so'
        )
        .call(
            blob_fixup_graphic_buffer_size,
            [
                '_ZN5mihal9GraBufferC2EjjimNSt3__112basic_stringIcNS1_11char_traitsIcEENS1_9allocatorIcEEEE',
                '_ZN5mihal9GraBufferC2EPKNS_6StreamENSt3__112basic_stringIcNS4_11char_traitsIcEENS4_9allocatorIcEEEE',
                '_ZN5mihal9GraBufferC2EjjimPK13native_handle',
                '_ZN5mihal9GraBufferC2EPKNS_6StreamEPK13native_handle',
            ],
        )
        .call(blob_fixup_mfnr_vendor_tag)
        .call(blob_fixup_fake_sat_sr_buffer_size),

    'odm/lib64/camera/components/com.mi.node.tsskinbeautifier.so': blob_fixup()
        .call(
            blob_fixup_graphic_buffer_size,
            [
                'ChiNodeEntry',
            ],
        ),
    (
        'vendor/lib64/vendor.xiaomi.hardware.camera.injection-service.so',
        'vendor/lib64/vendor.xiaomi.hardware.camera.injection-V1-ndk.so',
        'vendor/lib64/vendor.xiaomi.hardware.camera.injection-client.so',
    ): blob_fixup()
        .replace_needed(
            'android.hardware.camera.device-V1-ndk.so',
            'android.hardware.camera.device-V2-ndk.so'
        ),
    (
        'odm/lib64/libAncHumanVideoBokehV4.so',
        'odm/lib64/libTrueSight.so',
        'odm/lib64/libMiPhotoFilter.so',
        'odm/lib64/libmorpho_ubwc.so',
        'odm/lib64/libalAILDC.so',
        'odm/lib64/libalLDC.so',
    ): blob_fixup()
        .clear_symbol_version('AHardwareBuffer_allocate')
        .clear_symbol_version('AHardwareBuffer_describe')
        .clear_symbol_version('AHardwareBuffer_isSupported')
        .clear_symbol_version('AHardwareBuffer_lockPlanes')
        .clear_symbol_version('AHardwareBuffer_release')
        .clear_symbol_version('AHardwareBuffer_unlock')
        .clear_symbol_version('AHardwareBuffer_lock'),
    (
        'odm/lib64/camera/plugins/com.xiaomi.plugin.anchor.so',
        'odm/lib64/camera/plugins/com.xiaomi.plugin.mialgoaiur.so',
        'odm/lib64/camera/plugins/com.xiaomi.plugin.mialgosnsc.so',
    ): blob_fixup()
        .replace_needed(
            'libtinyxml2.so',
            'libtinyxml2-v34.so'
        ),
    'odm/lib64/com.qti.feature2.anchorsync.so': blob_fixup()
        .replace_needed(
            'android.hardware.graphics.allocator-V1-ndk.so',
            'android.hardware.graphics.allocator-V2-ndk.so'
        )
        .replace_needed(
            'libtinyxml2.so',
            'libtinyxml2-v34.so'
        ),
    (
        'odm/lib64/camera/com.qti.actuator.houji_ofilm_s5kjn1_gt9764v_tele_actuator.so',
        'odm/lib64/camera/com.qti.actuator.houji_sunny_ovx9000_ak7316_wide_actuator.so',
        'odm/lib64/camera/com.qti.actuator.houji_sunny_ovx9000_ak7316_wide_ii_actuator.so',
        'odm/lib64/camera/com.qti.actuator.houji_sunny_s5kjn1_gt9764v_tele_ii_actuator.so',
        'odm/lib64/camera/com.qti.eeprom.houji_ofilm_s5kjn1_gt24p128f_tele_eeprom.so',
        'odm/lib64/camera/com.qti.eeprom.houji_sunny_ov32b_p24c64f_front_eeprom.so',
        'odm/lib64/camera/com.qti.eeprom.houji_sunny_ovx9000_p24c128e_wide_eeprom.so',
        'odm/lib64/camera/com.qti.eeprom.houji_sunny_ovx9000_p24c128e_wide_ii_eeprom.so',
        'odm/lib64/camera/com.qti.eeprom.houji_sunny_s5kjn1_gt24p128f_ultra_eeprom.so',
        'odm/lib64/camera/com.qti.eeprom.houji_sunny_s5kjn1_p24c128f_tele_ii_eeprom.so',
        'odm/lib64/camera/com.qti.ois.houji_s5kjn1_bu24618_ois_ii.so',
        'odm/lib64/camera/com.qti.ois.houji_s5kjn1_bu24618_ois.so',
        'odm/lib64/camera/com.qti.sensor.houji_ofilm_s5kjn1_tele.so',
        'odm/lib64/camera/com.qti.sensor.houji_sunny_ov32b40_front.so',
        'odm/lib64/camera/com.qti.sensor.houji_sunny_ovx9000_wide_ii.so',
        'odm/lib64/camera/com.qti.sensor.houji_sunny_ovx9000_wide.so',
        'odm/lib64/camera/com.qti.sensor.houji_sunny_s5kjn1_tele_ii.so',
        'odm/lib64/camera/com.qti.sensor.houji_sunny_s5kjn1_ultra.so',
        'odm/lib64/camera/components/com.jigan.node.videobokeh.so',
        'odm/lib64/camera/components/com.mi.node.aiasd.so',
        'odm/lib64/camera/components/com.mi.node.rearvideo.so',
        'odm/lib64/camera/components/com.mi.node.skinbeautifier.so',
        'odm/lib64/camera/components/com.mi.node.videobokeh.so',
        'odm/lib64/camera/components/com.mi.node.videofilter.so',
        'odm/lib64/camera/components/com.mi.node.videonight.so',
        'odm/lib64/camera/components/com.qti.node.aon.so',
        'odm/lib64/camera/components/com.qti.node.depth.so',
        'odm/lib64/camera/components/com.qti.node.depthprovider.so',
        'odm/lib64/camera/components/com.qti.node.dewarp.so',
        'odm/lib64/camera/components/com.qti.node.eisv2.so',
        'odm/lib64/camera/components/com.qti.node.eisv3.so',
        'odm/lib64/camera/components/com.qti.node.evadepth.so',
        'odm/lib64/camera/components/com.qti.node.gme.so',
        'odm/lib64/camera/components/com.qti.node.gyrornn.so',
        'odm/lib64/camera/components/com.qti.node.hdr10pgen.so',
        'odm/lib64/camera/components/com.qti.node.hdr10phist.so',
        'odm/lib64/camera/components/com.qti.node.itofpreprocess.so',
        'odm/lib64/camera/components/com.qti.node.ml.so',
        'odm/lib64/camera/components/com.qti.node.mlinference.so',
        'odm/lib64/camera/components/com.qti.node.pixelstats.so',
        'odm/lib64/camera/components/com.qti.node.seg.so',
        'odm/lib64/camera/components/com.qti.node.swec.so',
        'odm/lib64/camera/components/com.qti.node.swregistration.so',
        'odm/lib64/camera/components/com.qti.node.swvrt.so',
        'odm/lib64/camera/components/com.qti.stats.cnndriver.so',
        'odm/lib64/camera/components/com.xiaomi.node.smooth_transition.so',
        'odm/lib64/camera/components/libcamxevainterface.so',
        'odm/lib64/camera/components/libdepthmapwrapper_itof.so',
        'odm/lib64/camera/components/libdepthmapwrapper_secure.so',
        'odm/lib64/camera/libchxlogicalcameratable.so',
        'odm/lib64/com.qti.camx.chiiqutils.so',
        'odm/lib64/com.qti.chiusecaseselector.so',
        'odm/lib64/com.qti.feature2.afbrckt.so',
        'odm/lib64/com.qti.feature2.demux.so',
        'odm/lib64/com.qti.feature2.derivedoffline.so',
        'odm/lib64/com.qti.feature2.fusion.so',
        'odm/lib64/com.qti.feature2.generic.so',
        'odm/lib64/com.qti.feature2.gs.sm8650.so',
        'odm/lib64/com.qti.feature2.hdr.so',
        'odm/lib64/com.qti.feature2.mcreprocrt.so',
        'odm/lib64/com.qti.feature2.memcpy.so',
        'odm/lib64/com.qti.feature2.metadataserializer.so',
        'odm/lib64/com.qti.feature2.mfsr.so',
        'odm/lib64/com.qti.feature2.ml.so',
        'odm/lib64/com.qti.feature2.mux.so',
        'odm/lib64/com.qti.feature2.offlinestatsregeneration.so',
        'odm/lib64/com.qti.feature2.qcfa.so',
        'odm/lib64/com.qti.feature2.rawhdr.so',
        'odm/lib64/com.qti.feature2.realtimeserializer.so',
        'odm/lib64/com.qti.feature2.rt.so',
        'odm/lib64/com.qti.feature2.rtmcx.so',
        'odm/lib64/com.qti.feature2.serializer.so',
        'odm/lib64/com.qti.feature2.statsregeneration.so',
        'odm/lib64/com.qti.feature2.stub.so',
        'odm/lib64/com.qti.feature2.swmf.so',
        'odm/lib64/com.qti.qseeutils.so',
        'odm/lib64/com.qualcomm.mcx.distortionmapper.so',
        'odm/lib64/com.qualcomm.mcx.linearmapper.so',
        'odm/lib64/com.qualcomm.mcx.nonlinearmapper.so',
        'odm/lib64/com.qualcomm.mcx.policy.mfl.so',
        'odm/lib64/com.qualcomm.qti.mcx.usecase.extension.so',
        'odm/lib64/hw/camera.qcom.sm8650.so',
        'odm/lib64/hw/com.qti.chi.offline.so',
        'odm/lib64/libcamerapostproc.so',
        'odm/lib64/libcamxhwnodecontext.so',
        'odm/lib64/libcamxifestriping.so',
        'odm/lib64/libcamximageformatutils.so',
        'odm/lib64/libcamxncsdatafactory.so',
        'odm/lib64/libcom.xiaomi.mawutilsold.so',
        'odm/lib64/libcommonchiutils.so',
        'odm/lib64/libfastmessage.so',
        'odm/lib64/libhme.so',
        'odm/lib64/libipebpsstriping.so',
        'odm/lib64/libipebpsstriping170.so',
        'odm/lib64/libipebpsstriping480.so',
        'odm/lib64/libisphwsetting.so',
        'odm/lib64/libjpege.so',
        'odm/lib64/libmctfengine_stub.so',
        'odm/lib64/libmfec.so',
        'odm/lib64/libmmcamera_bestats.so',
        'odm/lib64/libmmcamera_cac.so',
        'odm/lib64/libmmcamera_lscv35.so',
        'odm/lib64/libmmcamera_pdpc.so',
        'odm/lib64/libofflinefeatureintf.so',
        'odm/lib64/libopestriping.so',
        'odm/lib64/libtfestriping.so',
        'odm/lib64/libubifocus.so',
        'odm/lib64/vendor.qti.hardware.camera.aon-service-impl.so',
        'odm/lib64/vendor.qti.hardware.camera.offlinecamera-service-impl.so',
        'odm/lib64/vendor.qti.hardware.camera.postproc@1.0-service-impl.so',
        'odm/lib64/libmmcamera_mfnr.so',
        'odm/lib64/libmmcamera_mfnr_t4.so',
        'odm/lib64/libtunningmemhook.so',
    ): blob_fixup()
        .replace_needed(
            'android.hardware.graphics.allocator-V1-ndk.so',
            'android.hardware.graphics.allocator-V2-ndk.so'
    ),
}

module = ExtractUtilsModule(
    'houji',
    'xiaomi',
    blob_fixups=blob_fixups,
    namespace_imports=namespace_imports,
    check_elf=True,
    add_firmware_proprietary_file=True,
)

if __name__ == '__main__':
    utils = ExtractUtils.device_with_common(
        module, 'sm8650-common', module.vendor
    )
    utils.run()
