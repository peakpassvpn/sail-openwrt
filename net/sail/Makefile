#
# sail for OpenWrt: the router build of a sail release, as it was
# published, packaged with its service and configuration. Nothing is
# compiled here; the binary is the one whose SHA256 the release lists.
#

include $(TOPDIR)/rules.mk

PKG_NAME:=sail
# Set, with the hashes below, to the first release with router builds.
PKG_VERSION:=0.16.0
PKG_RELEASE:=1

PKG_LICENSE:=Apache-2.0
PKG_LICENSE_FILES:=LICENSE

# The release target for this package architecture. Names with vfp or
# neon have an FPU. Plain arm_cortex-a7 and arm_cortex-a9 are soft-float:
# their targets (mediatek/mt7629, airoha/en7523, bcm53xx) list no fpu
# feature, so OpenWrt builds them with SOFT_FLOAT and -mfloat-abi=soft.
SAIL_TARGET:=
ifneq ($(filter aarch64_%,$(ARCH_PACKAGES)),)
  SAIL_TARGET:=aarch64-unknown-linux-musl
endif
ifneq ($(filter arm_cortex-a%vfpv3 arm_cortex-a%vfpv3-d16 arm_cortex-a%vfpv4 arm_cortex-a%_neon,$(ARCH_PACKAGES)),)
  SAIL_TARGET:=armv7-unknown-linux-musleabihf
endif
ifneq ($(filter arm_cortex-a7 arm_cortex-a9,$(ARCH_PACKAGES)),)
  SAIL_TARGET:=armv7-unknown-linux-musleabi
endif
ifeq ($(ARCH_PACKAGES),arm_arm1176jzf-s_vfp)
  SAIL_TARGET:=arm-unknown-linux-musleabi
endif
ifeq ($(ARCH_PACKAGES),x86_64)
  SAIL_TARGET:=x86_64-unknown-linux-musl
endif
ifeq ($(ARCH_PACKAGES),i386_pentium4)
  SAIL_TARGET:=i686-unknown-linux-musl
endif
ifneq ($(filter mipsel_24kc mipsel_24kc_24kf mipsel_74kc mipsel_mips32,$(ARCH_PACKAGES)),)
  SAIL_TARGET:=mipsel-unknown-linux-musl
endif

# The SHA256 of each target's tarball, as the release's SHA256SUMS lists
# it; filled in for each version.
SAIL_HASH_aarch64-unknown-linux-musl:=skip
SAIL_HASH_armv7-unknown-linux-musleabihf:=skip
SAIL_HASH_armv7-unknown-linux-musleabi:=skip
SAIL_HASH_arm-unknown-linux-musleabi:=skip
SAIL_HASH_x86_64-unknown-linux-musl:=skip
SAIL_HASH_i686-unknown-linux-musl:=skip
SAIL_HASH_mipsel-unknown-linux-musl:=skip

PKG_SOURCE:=sail-$(PKG_VERSION)-$(SAIL_TARGET)-router.tar.gz
PKG_SOURCE_URL:=https://github.com/peakpassvpn/sail/releases/download/v$(PKG_VERSION)/
PKG_HASH:=$(SAIL_HASH_$(SAIL_TARGET))
PKG_BUILD_DIR:=$(BUILD_DIR)/sail-$(PKG_VERSION)-$(SAIL_TARGET)-router

include $(INCLUDE_DIR)/package.mk

define Package/sail
  SECTION:=net
  CATEGORY:=Network
  SUBMENU:=Web Servers/Proxies
  TITLE:=sail, a proxy platform (sing-box, Clash and Surge configurations)
  URL:=https://github.com/peakpassvpn/sail
  DEPENDS:=@(aarch64||arm||x86_64||i386||mipsel) +kmod-tun +ca-bundle
endef

define Package/sail/description
  sail runs sing-box, Clash and Surge configurations as they are: TUN
  and transparent proxying for the LAN, subscriptions, rule-sets, and
  the Clash API for dashboards. This is the release's router build, at
  the router memory profile.
endef

define Package/sail/conffiles
/etc/config/sail
/etc/sail/config.json
endef

# The release is unpacked as it is; there is nothing to build.
define Build/Compile
endef

define Package/sail/install
	$(INSTALL_DIR) $(1)/usr/bin
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/sail $(1)/usr/bin/sail
	$(INSTALL_DIR) $(1)/etc/init.d
	$(INSTALL_BIN) ./files/sail.init $(1)/etc/init.d/sail
	$(INSTALL_DIR) $(1)/etc/config
	$(INSTALL_CONF) ./files/sail.conf $(1)/etc/config/sail
	$(INSTALL_DIR) $(1)/etc/sail
	$(INSTALL_CONF) ./files/config.json $(1)/etc/sail/config.json
	$(INSTALL_DIR) $(1)/lib/upgrade/keep.d
	$(INSTALL_DATA) ./files/sail.keep $(1)/lib/upgrade/keep.d/sail
	$(INSTALL_DIR) $(1)/usr/share/licenses/sail
	$(INSTALL_DATA) $(PKG_BUILD_DIR)/LICENSE $(PKG_BUILD_DIR)/THIRD_PARTY_LICENSES.md \
		$(1)/usr/share/licenses/sail/
endef

$(eval $(call BuildPackage,sail))
