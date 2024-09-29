#!/bin/bash

# Test building in a container
# can be used by CI or locally with docker installed
#
# pass target distro as $1

set -ex
this_dir=$(realpath $(dirname $0))

# use ci.yml to drive the roles and modules built in the CI
cp $this_dir/../ansible/group_vars/ci.yml $this_dir/../ansible/group_vars/local.yml

case "$1" in
    "ubuntu")
        image="ubuntu:24.04"; installer=apt ;;
    "rocky")
        image="rockylinux:9.3"; installer=dnf ;;
    "debian")
        image="debian:bullseye"; installer=apt ;;
    "fedora")
        image="fedora:40"; installer=dnf ;;

    *) echo "Usage: $0 {ubuntu|rocky|debian|fedora}"; exit 1;;
esac

# container mounts
docker="-v /var/run/docker.sock:/var/run/docker.sock -e DOCKER_HOST=unix://"
ansible="-v $this_dir/../ansible:/ansible"
setup="-v $this_dir/../initial_setup.sh:/initial_setup.sh"
# container environment variables
args="-e installer=$installer -e ansible_args=-ein_container=true"

if [[ -z "$(docker ps -a -q -f name=epics-dev)" ]]; then
    docker run --name epics-dev -d $ansible $docker $setup $args $image bash -c "sleep infinity"
else
    echo continuing with existing container epics-dev
fi

docker exec epics-dev bash -c "/initial_setup.sh"

docker rm -f epics-dev
