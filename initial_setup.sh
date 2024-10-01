#!/bin/bash
set -xe

if [[ "$installer" == "apt" ]]; then
    if [[ $(cat /etc/os-release) =~ Ubuntu ]] ; then
        add-apt-repository ppa:ansible/ansible
    fi
    apt-get update; apt-get install -y ansible python3-jmespath
elif [[ "$installer" == "dnf" ]]; then
    dnf install -y epel-release || dnf update -y --refresh
    dnf install -y ansible python3-jmespath
fi

ansible-galaxy install -r /ansible/requirements.yml || true
ansible-playbook -i /ansible/hosts -e initial_setup=true $ansible_args /ansible/playbook.yml