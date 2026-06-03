#!/bin/bash
set -xe

if [[ "$installer" == "apt" ]]; then
    if [[ $(cat /etc/os-release) =~ Ubuntu ]] ; then
        apt-get update; apt-get install -y software-properties-common
        add-apt-repository ppa:ansible/ansible
    fi
    apt-get update; apt-get install -y ansible python3-jmespath
elif [[ "$installer" == "dnf" ]]; then
    dnf install -y epel-release || dnf update -y --refresh
    dnf install -y ansible python3-jmespath
fi

cd ansible
ansible-galaxy install -r requirements.yml || true
ansible-playbook $ansible_args playbook.yml -e @vars/local.yml -e initial_setup=true
