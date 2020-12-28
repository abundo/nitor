#!/usr/bin/env python3
"""
Install certificate on remote host, copy using ssh
Restart apache2 when done

nitor : to strive, exert oneself, make an effort, persevere.
nitor : to rest, lean, support oneself / trust in, depend upon.
nitor : brilliance, brightness, glow, elegance, splendor.
"""

import os
import sys
import subprocess
import argparse
import datetime


# ----- defaults, start -----

APACHE_SRC_DIR = "/var/lib/nitor"
APACHE_DST_DIR = "/etc/ssl/nitor"

SSH_USER = "nitor"

# ----- defaults, end -----


class Install_Cert:

    def __init__(self):
        pass

    def handle_apache2(self, hostname: str = None, cert_src: str = None, cert_dst: str = None):
        if "/" not in cert_src:
            cert_src = APACHE_SRC_DIR + "/" + cert_src

        if cert_dst is None:
            cert_dst = APACHE_DST_DIR

        cmd = f"scp -i /root/.ssh/nitor {cert_src} {SSH_USER}@{hostname}:{cert_dst}"
        print(cmd)
        ret = subprocess.run(cmd, shell=True)
        if ret.returncode != 0:
            print("Error:", ret)
            return

        # Compare date between the two certs, on remote host
        base_name = os.path.basename(cert_src)
        base_name_noext = os.path.splitext(base_name)[0]
        file_crt = f"{base_name_noext}.crt"
        file_key = f"{base_name_noext}.key"

        cmd = f"ssh -i /root/.ssh/nitor {SSH_USER}@{hostname} stat -c %Y {cert_dst}/{file_crt} {cert_dst}/{file_key}"
        ret = subprocess.run(cmd, shell=True, capture_output=True, universal_newlines=True)
        if ret.returncode != 0:
            print("Error:", ret)
            return
        lines = ret.stdout.split("\n")
        if len(lines) != 3:
            # We did not get two timestamps, both files are not in place on remote host
            return
        try:
            timestamp1 = int(lines[0])
            timestamp2 = int(lines[1])
        except ValueError:
            return
        diff = datetime.datetime.fromtimestamp(timestamp1) - datetime.datetime.fromtimestamp(timestamp2)
        if abs(diff.total_seconds()) > 10:
            # Too large difference, acertmgr has probably not written both files yet
            return

        cmd = f"ssh -t -i /root/.ssh/nitor {SSH_USER}@{hostname} sudo /bin/systemctl reload apache2.service"
        print(cmd)
        ret = subprocess.run(cmd, shell=True)
        if ret.returncode != 0:
            print("Error:", ret)

    def handle_esxi(self):
        """
        Install a certificate in an ESXi hypervisor
        """
        raise RuntimeError("Not implemented")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("cmd", choices=[
        "apache2",
        "esxi",
    ])
    parser.add_argument("--hostname", required=True)
    parser.add_argument("--cert-src", required=True)
    parser.add_argument("--cert-dst")

    args = parser.parse_args()

    install_cert = Install_Cert()

    if args.cmd == "apache2":
        install_cert.handle_apache2(
            hostname=args.hostname,
            cert_src=args.cert_src,
            cert_dst=args.cert_dst,
        )

    elif args.cmd == "esxi":
        install_cert.handle_esxi()

    else:
        print(f"Error: Unknown type {args.cmd}")


if __name__ == "__main__":
    main()
