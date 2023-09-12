#!/bin/bash


if [ -f /var/.firstboot ]; then
	exit 0
fi
logger "Setting up admin user"

adduser --gecos User user
adduser user sudo
echo "user:user" | chpasswd

sed -i "s/\#PermitRootLogin prohibit-password/\#PermitRootLogin prohibit-password\nPermitRootLogin Yes\n/" /etc/ssh/sshd_config
systemctl restart ssh.service

grub-install --uefi-secure-boot --target="x86_64-efi" --no-nvram --removable
grub-install --uefi-secure-boot --target="x86_64-efi" --no-nvram
update-grub
cp -rp /boot/ostree/* /ostree/

touch /var/.firstboot

shutdown -r now
