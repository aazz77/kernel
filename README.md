# x64-debian13-kernel

x86_64 Debian 13 桌面内核编译仓库。基于 Debian 官方 `7.1.8+deb13-amd64` config 精简后用 GitHub Actions 编译，产出可直接 `dpkg -i` 的 `linux-image` / `linux-headers` deb 包。

## 仓库结构

```
.github/workflows/build-kernel.yml   # 编译 workflow (手动触发)
kernel-config/
  config-7.1.8+deb13-amd64           # Debian 官方 config 原件(base)
  slim-patterns.txt                  # 精简清单(想恢复某项功能就删对应行)
  gen-slim-fragment.py               # 由 base + patterns 生成 fragment
  slim-desktop.fragment              # 生成的精简 fragment(已提交)
```

## 用法

1. 把本文件夹推到一个 GitHub 仓库
2. Actions → Build Kernel x64 → Run workflow → 填 version(默认 7.1.8)和 kernel_sign(可选后缀)
3. 在 Release 页下载 `linux-image-*.deb` / `linux-headers-*.deb`
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

## 恢复某项功能

编辑 `slim-patterns.txt` 删掉对应行,然后重新生成 fragment:

```sh
python3 kernel-config/gen-slim-fragment.py
```

例:需要 Waydroid → 删 `ANDROID_BINDER_IPC*`;需要电视卡 → 删 `MEDIA_PCI_SUPPORT`。

## 注意

- **Secure Boot**:模块未签名(DEBIAN 签名密钥已清空)。如果开了 Secure Boot,要么关闭,要么自己 MOK 签名
- config 版本与内核版本不必须一致,workflow 里 `olddefconfig` 会自动消化新选项;换大版本后建议重跑一次 `gen-slim-fragment.py`(换个 base 文件即可)
- GitHub 免费-runner(4 vCPU)构建约 1~2 小时(精简后);timeout 已设 300 分钟
