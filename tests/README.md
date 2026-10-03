# Testing the package

1. Build the package with an OpenWrt 25.12 x86/64 SDK and this feed (see
   the top README). Before a release lists the router archive, put a
   locally built `sail-<version>-x86_64-unknown-linux-musl-router.tar.gz`
   (top directory `sail-<version>-x86_64-unknown-linux-musl-router/`
   holding `sail`, `LICENSE` and `THIRD_PARTY_LICENSES.md`) in the SDK's
   `dl/` and set its `SAIL_HASH_x86_64-unknown-linux-musl` to `skip`.
2. Copy the `.apk` to a directory as `sail.apk`.
3. Unpack an OpenWrt x86/64 `generic-ext4-combined.img.gz` of the same
   release, and run, with `qemu-system-x86_64` installed:

```sh
python3 tests/qemu.py openwrt-x86-64-generic-ext4-combined.img <dir>
```

It boots the image (no KVM needed), installs the package with its
dependencies, and checks the service. The image is changed: use a copy.
