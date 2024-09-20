# Vagrant VM Creation

## Pre-requisites

Setup the required tools on your host machine:
1. Install [VirtualBox](https://www.virtualbox.org/wiki/Downloads)
2. Install [Vagrant](https://www.vagrantup.com/downloads.html)
3. Install [Ansible](https://docs.ansible.com/ansible/latest/installation_guide/intro_installation.html#pipx-install)

## Steps

1. Clone the repository
1. Navigate to the `vagrant` directory
1. Run `vagrant up`

## Troubleshooting

If there is a failure in the ansible steps and you have fixed the issue, re-run the ansible playbook by running `vagrant provision`.

Get rid of the VM by running
```
vagrant halt
vagrant destroy
```