# x64-debian13-kernel

x86_64 Debian 13 桌面内核编译仓库。基于 Debian 官方 `7.1.8+deb13-amd64` config 精简后用 GitHub Actions 编译，产出可直接 `dpkg -i` 的 `linux-image` / `linux-headers` deb 包。

## 仓库结构

```
.github/workflows/build-kernel.yml   # 编译 workflow (手动触发, 可选 profile)
kernel-config/
  config-7.1.8+deb13-amd64           # Debian 官方 config 原件(base)
  slim-patterns.txt                  # 桌面版精简清单
  kvm-guest-patterns.txt             # KVM guest 版精简清单(桌面精简 + guest 附加项)
  gen-slim-fragment.py               # 由 base + patterns 生成 fragment
  slim-desktop.fragment              # 桌面版 fragment(已提交)
  kvm-guest.fragment                 # KVM guest 版 fragment(已提交)
```

## 用法

1. 把本文件夹推到一个 GitHub 仓库
2. Actions → Build Kernel x64 → Run workflow:
   - **version**: 内核版本(默认 7.1.8)
   - **kernel_sign**: LOCALVERSION 后缀(可选)
   - **profile**: `desktop` = 物理桌面机 / `kvm-guest` = KVM 虚拟机 guest 内核
3. 在 Release 页下载(按 profile 分 tag: `kernel-x64-desktop` / `kernel-x64-kvm-guest`)
4. 本机安装:`sudo dpkg -i linux-image-*.deb`
   - initramfs 和 grub 由系统自带的 `/etc/kernel/postinst.d` 钩子(initramfs-tools + grub)自动处理,无需手动操作

## 精简了什么(共 ~536 项)

| 类别 | 内容 | 说明 |
|---|---|---|
| 调试信息 | DEBUG_INFO/BTF 全关 | **构建时间大头**,代价是 bpftrace 无 BTF |
| Xen | XEN 全家 | 只保留 KVM host |
| 媒体 | PCI/平台 TV 卡、DVB、模拟电视、SDR、收音机、红外遥控、CAN | 保留 USB 摄像头(UVC) |
| 声卡 | SND_SOC 全部 | 保留 HDA + USB 声卡 |
| 文件系统 | AFS/Ceph/GFS2/OCFS2/JFS/HFS/老 NTFS/MTD 系等 ~25 个 | 保留 ext4/btrfs/xfs/vfat/exfat/ntfs3/fuse/squashfs/udf/NFS/CIFS |
| 企业存储/网络 | iSCSI offload、FC HBA、InfiniBand/RDMA、Zigbee、NFC、IPMI | 桌面用不到 |
| 其他 | STAGING、IIO、触摸屏、USB Gadget、Android Binder、GMA500、KUnit | |

### kvm-guest profile 在桌面精简之上额外(共 ~725 项, headless 无桌面)

| 类别 | 内容 | 说明 |
|---|---|---|
| hypervisor host | KVM/KVM_INTEL/KVM_AMD、HyperV | 内核自己跑在 KVM 里 |
| GPU | i915/Xe/AMDGPU/Nouveau/VMware | 只留 virtio-gpu(内建) |
| 无线 | 全部 WLAN vendor + 蓝牙 | guest 无物理射频 |
| SATA | ATA/SATA/PATA/AHCI 全系 | 磁盘走 virtio(需要 SATA 模拟盘就删这几行) |
| 音频 | SOUND 整棵(含 HDA/virtio-sound) | headless 无声卡 |
| 媒体 | MEDIA_SUPPORT 整棵(摄像头/采集/DVB) | 要 USB 摄像头直通就删这行 |
| 外设 | 并口、游戏杆、FireWire、AGP、SD 读卡器(MMC)、USB 打印机 | headless 用不到 |
| 内建化 | VIRTIO_BLK/NET、SCSI+SCSI_VIRTIO、VIRTIO_GPU、virtio-rng/balloon/input 全部 =y | 不依赖 initramfs 时序 |

保留的 guest 基础能力:USB core/xHCI(U 盘直通, USB_STORAGE/UAS)、PS/2 键盘 + HID(virt-manager 图形控制台打字)、VGA/EFI framebuffer(启动 console)、8250 串口 + virtio-console(串口控制台)、virtiofs(宿主机目录共享)。

## 恢复某项功能 / 自定义设值

编辑 `slim-patterns.txt`,然后重新生成 fragment:

```sh
python3 kernel-config/gen-slim-fragment.py
```

两种语法:

| 写法 | 效果 |
|---|---|
| 纯符号名(可带 `*` 前缀通配),如 `MEDIA_PCI_SUPPORT` | 禁用该符号(base 中存在才生成禁用行) |
| 含 `=` 的设值行,如 `CONFIG_TRANSPARENT_HUGEPAGE=y` | 无条件写入 fragment;`=n` 会归一化为 `# CONFIG_X is not set` |

例:需要 Waydroid → 删 `ANDROID_BINDER_IPC*`;需要电视卡 → 删 `MEDIA_PCI_SUPPORT`;改 THP 模式 → 在文件末尾"显式设置"段改 `CONFIG_TRANSPARENT_HUGEPAGE_ALWAYS=y`(choice 组内同时只留一个 =y)。

## 注意

- **bindeb-pkg 传了 `DPKG_FLAGS=-d`**:mkdebian 要求 `debhelper-compat (= 12)`,Ubuntu noble 的 debhelper 13 只 Provides `(= 13)`,该依赖 apt 无法满足,只能跳过检查;真实依赖(build-essential/debhelper/libdw-dev 等)已在 workflow 装齐
- **Secure Boot**:模块未签名(DEBIAN 签名密钥已清空)。如果开了 Secure Boot,要么关闭,要么自己 MOK 签名
- config 版本与内核版本不必须一致,workflow 里 `olddefconfig` 会自动消化新选项;换大版本后建议重跑一次 `gen-slim-fragment.py`(换个 base 文件即可)
- GitHub 免费-runner(4 vCPU)构建约 1~2 小时(精简后);timeout 已设 300 分钟
