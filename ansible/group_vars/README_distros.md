# What builds Where

In this folder the following two files document which roles and modules build in which of the distros:

- ci.yml - for the CI/CD pipeline using docker (also .github/test_docker.sh can be run locally using podman or docker)
- everything.yml - for building in a VM with vagrant

Here are the reasons for differences:

- bluesky cannot build in CI because that is containers in containers. (there are ways to do this and we can revisit this later)
- the latest p4p released TODAY (2024-10-01 v4.2.0) does build with python 3.12 but still fails on Ubuntu for some reason - to be investigated.
- pvapy - downgrading from 5.4.1 to 5.3.1 makes it build on Rocky. The later version tries to check for boost 1.78.0 and fails. 5.3.1 won't build on distros with python 3.12 and also fails on Ubuntu for boost version reasons.
- areadetector uses a deprecated function in xmllib2 and Fedora's version is too new.
- areadetector also fails on debian because its version of ansible does not support 'search_string' in lineinfile which is used in adcore_prep.yml. Trying to get an new ansible from the ubuntu ppa (as per ansible docs) fails with dependecy conflicts.