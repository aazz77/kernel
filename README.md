# KVM VPS 内核 (x86_64, 主线 7.2.5)

用同一份主线 7.2.5 源码编译 x86_64 内核,面向 KVM VPS 虚机。
CI 从 kernel.org 下载源码(与 amlogic-kernel 同源同版),本仓库只维护配置 fragment。
**全内建**:x86_64_defconfig + `kvm_guest.config` + `CONFIG_MODULES=n`,不构建任何模块;只叠加代理功能 fragment。

## 与 panther/amlogic 工程的差异

| | panther/amlogic | vps (本工程) |
|---|---|---|
| 基线配置 | arm64 defconfig + slim 裁剪 | x86_64_defconfig + kvm_guest.config |
| 架构 | arm64 (arm runner) | x86_64 (ubuntu-latest) |
| 模块 | 全内建 (MODULES=n) | 全内建 (MODULES=n) |
| 固件 | 内嵌/板级 | 不需要 (virtio 纯虚拟设备) |
| 产物 | Image + dtb | bzImage (单文件, 无模块树) |

## 文件清单

| 文件 | 说明 |
|---|---|
| `kernel-config/vps.fragment` | `CONFIG_MODULES=n` 全内建 + virtio 关键驱动显式 =y;补 tproxy/nft/iptables/cgroup/bbr/wireguard/ipsec/ipvs/flow offload/THP madvise |
| `.github/workflows/build-kernel.yml` | x86_64 构建,产 deb + tar.gz 发 Release |

## VPS 上安装

```sh
dpkg -i linux-image-7.2.5*.deb   # postinst 自动 update-grub (全内建无模块, 无需 depmod/initramfs)
reboot
```

- `kvm_guest.config` 已内建 virtio_blk/virtio_net/virtio_scsi/9p/串口,root=UUID 直接挂,**无需 initramfs**( grub 不带 initrd 也能起);若 VPS 面板强制要求 initrd,装 `initramfs-tools` 后 `update-initramfs -c -k <KVER>` 再 `update-grub`
- 控制台: `console=ttyS0,115200`(VPS 串口)或图形控制台 tty0
- 重启前先确认面板引导是 grub 直读 /boot(绝大多数 KVM VPS 是);LVM/LUKS 根分区才需要 initramfs

## 风险提示

- **换内核前确认 VPS 商家的引导方式**:少数商家用自家 boot 分区/内核白名单(如部分 OpenVZ 不适用,KVM 可以);装坏可用面板救援模式回滚
- x86_64_defconfig + kvm_guest 是内核自带组合,VirtualBox/VMware/裸金属 x86 也能直接用(裸金属需对应硬件驱动,完整 defconfig 已覆盖主流)
