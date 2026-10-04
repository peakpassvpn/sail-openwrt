# sail for OpenWrt

An OpenWrt package feed for [sail](https://github.com/peakpassvpn/sail): the
router build of a sail release, packaged with a procd service and a UCI
configuration. Nothing is compiled: the package downloads the release
archive for the router's architecture and checks it against the SHA256 the
release lists.

OpenWrt 25.12 and later (apk packages).

**Not installable yet.** No sail release has router archives so far: the
package's version and hashes are placeholders, and building it now fails
at the download. They are set with the first release that has them.

## Use the feed

In an OpenWrt build tree or SDK, add to `feeds.conf`:

```
src-git sail https://github.com/peakpassvpn/sail-openwrt.git
```

then:

```sh
./scripts/feeds update sail
./scripts/feeds install sail
make package/sail/compile
```

The package is in `bin/packages/<arch>/sail/`.

## Architectures

| OpenWrt package architecture | sail release build |
| --- | --- |
| `aarch64_*` | `aarch64-unknown-linux-musl` |
| `arm_cortex-a*` with `vfpv3`, `vfpv3-d16`, `vfpv4` or `neon` | `armv7-unknown-linux-musleabihf` |
| `arm_cortex-a7`, `arm_cortex-a9` (no FPU) | `armv7-unknown-linux-musleabi` |
| `arm_arm1176jzf-s_vfp` | `arm-unknown-linux-musleabi` |
| `mipsel_24kc`, `mipsel_24kc_24kf`, `mipsel_74kc`, `mipsel_mips32` | `mipsel-unknown-linux-musl` (statically linked) |
| `x86_64` | `x86_64-unknown-linux-musl` |
| `i386_pentium4` | `i686-unknown-linux-musl` |

Plain `arm_cortex-a7` and `arm_cortex-a9` are the targets OpenWrt builds
soft-float (no `fpu` feature), so they take the soft-float build, which
also runs on cores with an FPU.

## Configure

`/etc/config/sail`:

```
config sail 'main'
	option enabled '0'
	option config '/etc/sail/config.json'
	option profile 'router'
	option cache_dir '/var/lib/sail'
```

- `config` is a sing-box JSON, Clash YAML or Surge profile, read as it is.
- `profile` is sail's tuning preset: `router` uses the least memory.
  The router build also allocates with musl's own allocator, which holds
  less memory than mimalloc in sail's other builds; multiplexed (mux)
  transfers are slower with it.
- `cache_dir` holds subscriptions and remote rule-sets. `/var` is in RAM,
  so they are fetched again after a reboot; a directory on flash keeps
  them, at the cost of writes.

Enable and start:

```sh
uci set sail.main.enabled=1 && uci commit sail
service sail start
```

The configuration is checked before every start and reload:

- `service sail reload` applies an edited configuration file in place:
  rules, outbounds, DNS and inbounds change without a restart, and only
  the connections of inbounds removed or replaced are closed. A TUN inbound
  added, removed or changed, or changed UCI settings, restart sail. A
  configuration that does not check keeps the running one.
- A start whose configuration does not check logs why (`logread -e sail`)
  and does not start.

sail runs as root, as OpenWrt's VPN and proxy services do: TUN, routes
and nftables need it. `/etc/sail/` is kept across sysupgrade.

## License

Apache-2.0, as sail.
