#!/usr/bin/env python3
"""Boots OpenWrt x86/64 under qemu, installs the sail package and checks
its service: install, start, a proxied request, reload, a configuration
that does not check, sysupgrade's keep list, removal.

The host serves the package and a test page on 10.0.2.2:8000 (qemu's user
network); the guest installs the package's dependencies from
OPENWRT_MIRROR (default downloads.openwrt.org).

usage: tests/qemu.py <x86-64 ext4 combined image, which is changed> <dir holding sail.apk>
"""
import http.server, os, re, select, subprocess, sys, threading, time

image, served = sys.argv[1], os.path.abspath(sys.argv[2])
MIRROR = os.environ.get("OPENWRT_MIRROR", "https://downloads.openwrt.org")
PROMPT = re.compile(rb"root@OpenWrt:[^\r\n]*# ")
STATUS = re.compile(rb"@@RC:(\d+)")
results = []


def serve():
    with open(os.path.join(served, "hello"), "w") as f:
        f.write("hello through sail\n")

    class Quiet(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *a, **k):
            super().__init__(*a, directory=served, **k)

        def log_message(self, *a):
            pass

    http.server.ThreadingHTTPServer(("127.0.0.1", 8000), Quiet).serve_forever()


threading.Thread(target=serve, daemon=True).start()
qemu = subprocess.Popen(
    ["qemu-system-x86_64", "-m", "256", "-nographic", "-no-reboot",
     "-drive", f"file={image},format=raw,if=virtio",
     "-netdev", "user,id=n0", "-device", "virtio-net,netdev=n0"],
    stdin=subprocess.PIPE, stdout=subprocess.PIPE, bufsize=0)
buf = b""


def expect(pattern, timeout):
    """Reads until pattern; returns (what came before, the match)."""
    global buf
    end = time.time() + timeout
    while True:
        m = pattern.search(buf)
        if m:
            before, buf = buf[: m.start()], buf[m.end():]
            return before, m
        if time.time() > end:
            raise TimeoutError(f"no {pattern.pattern!r} in {timeout}s; last: {buf[-600:]!r}")
        r, _, _ = select.select([qemu.stdout], [], [], 1)
        if r:
            chunk = os.read(qemu.stdout.fileno(), 65536)
            if not chunk:
                raise EOFError(f"qemu ended; last: {buf[-600:]!r}")
            buf += chunk


def run(cmd, timeout=60):
    """Runs cmd in the guest: (exit status, its output)."""
    qemu.stdin.write(f'{cmd}; echo "@@RC:$?"\n'.encode())
    out, m = expect(STATUS, timeout)
    expect(PROMPT, 10)
    text = out.decode(errors="replace").replace("\r", "")
    # Without the echoed command line.
    lines = [l for l in text.split("\n") if 'RC:$?' not in l and l.strip() != cmd.strip()]
    return int(m.group(1)), "\n".join(lines).strip()


def check(name, ok, detail=""):
    results.append((name, bool(ok)))
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + ("" if ok else f"\n      {detail}"), flush=True)


def wait_for(cmd, timeout=20):
    """Runs cmd until it succeeds; whether it did."""
    end = time.time() + timeout
    while time.time() < end:
        if run(cmd)[0] == 0:
            return True
        time.sleep(1)
    return False


try:
    expect(re.compile(rb"Please press Enter to activate this console"), 300)
    time.sleep(2)
    qemu.stdin.write(b"\n")
    expect(PROMPT, 30)
    run("stty -echo 2>/dev/null; export PS1='root@OpenWrt:~# '")

    # qemu's user network hands out 10.0.2.15 by DHCP; the image's lan is a
    # static 192.168.1.1.
    run("uci set network.lan.proto=dhcp; uci delete network.lan.ipaddr; uci commit network; service network restart", 60)
    check("guest network up", wait_for("ping -c1 -W2 10.0.2.2 >/dev/null", 60))
    run(f"sed -i 's#https://downloads.openwrt.org#{MIRROR}#' /etc/apk/repositories.d/distfeeds.list")
    rc, out = run("apk update", 300)
    check("apk update from the mirror", rc == 0, out[-400:])

    rc, out = run("wget -q -O /tmp/sail.apk http://10.0.2.2:8000/sail.apk && apk add --allow-untrusted /tmp/sail.apk", 300)
    check("package installs with its dependencies", rc == 0, out[-600:])
    for path in ["/usr/bin/sail", "/etc/init.d/sail", "/etc/config/sail", "/etc/sail/config.json",
                 "/lib/upgrade/keep.d/sail",
                 "/usr/share/licenses/sail/LICENSE"]:
        check(f"installed {path}", run(f"test -e {path}")[0] == 0)
    rc, out = run("sail -V")
    check("sail runs", rc == 0 and re.fullmatch(r"\d+\.\d+\.\d+\S*", out.strip()), out)
    check("kmod-tun and ca-bundle installed", run("apk info -e kmod-tun ca-bundle")[0] == 0)

    run("service sail start; sleep 2")
    check("disabled by default: start does nothing", run("pidof sail")[0] != 0)

    run("uci set sail.main.enabled=1; uci commit sail; service sail start")
    check("enabled: it starts", wait_for("pidof sail >/dev/null"))
    check("it listens on 7890", wait_for("netstat -ltn | grep -q ':7890 '"))
    pid = run("pidof sail")[1]
    rc, out = run("http_proxy=http://127.0.0.1:7890 wget -q -O - http://10.0.2.2:8000/hello", 30)
    check("HTTP through its mixed inbound", rc == 0 and "hello through sail" in out, out)

    run("service sail reload; sleep 2")
    check("reload with nothing changed keeps the process", run("pidof sail")[1] == pid)

    run("sed -i 's/7890/7891/' /etc/sail/config.json; service sail reload")
    ok = wait_for("netstat -ltn | grep -q ':7891 '")
    check("reload of an edited configuration applies it", ok,
          run("netstat -ltn | grep -E ':789'; logread -e sail | tail -n 5")[1])
    check("by starting sail again", run("pidof sail")[1] not in ("", pid))
    pid = run("pidof sail")[1]

    run("cp /etc/sail/config.json /tmp/good.json; echo '{ not json' > /etc/sail/config.json")
    rc, out = run("service sail reload")
    check("reload of a broken configuration is refused", rc != 0, f"rc={rc} {out}")
    time.sleep(2)
    check("and the running one carries on", run("pidof sail")[1] == pid
          and run("netstat -ltn | grep -q ':7891 '")[0] == 0)
    run("service sail restart; sleep 3")
    check("restart with a broken configuration does not start", run("pidof sail")[0] != 0)
    rc, out = run("logread -e sail | tail -n 3")
    check("and logs why", "config.json" in out, out)
    run("cp /tmp/good.json /etc/sail/config.json; service sail start")
    check("the good configuration starts again", wait_for("pidof sail >/dev/null"))

    rc, out = run("sysupgrade -l | grep -c '^/etc/sail/'")
    check("/etc/sail is kept across sysupgrade", rc == 0 and out.strip() not in ("", "0"), out)

    run("service sail stop")
    rc, out = run("apk del sail", 120)
    check("it uninstalls", rc == 0 and run("test -e /usr/bin/sail")[0] != 0, out)
finally:
    qemu.kill()

failed = [n for n, ok in results if not ok]
print(f"\n{len(results) - len(failed)} passed, {len(failed)} failed")
sys.exit(1 if failed else 0)
