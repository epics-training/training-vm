#!/bin/bash
#
# Run as root
# Adds the necessary configuration into a VM that allows
# connecting through a corporate firewall doing deep packet inspection
#
# Needs the root CA certificate (in PEM format)
# in the current directory as ./corporate_root_ca.crt
cert="corporate_root_ca.crt"
pem_cert="corporate_root_ca.pem.crt"

# Function to add a line to a specific section in a configuration file
# or add it at the end of the file (when no section is specified)
add_line_to_section() {
  local config_file="$1"
  local section_name="$2"
  local new_line="$3"
  local section_found=0

  if [[ "$section_name" == "" ]]; then
    echo "$new_line" >> "$config_file"
  else
    temp_file=$(mktemp)
    
    # Read the configuration file line by line
    while IFS= read -r line; do
      # Check if the line is the beginning of the specified section
      grep -q "^\[\W*$section_name\W*\]" <<< $line 
      if [ $? -eq 0 ]; then
        # Write the section header and the new line to the temporary file
        echo "$line" >> "$temp_file"
        echo "$new_line" >> "$temp_file"
        section_found=1
      else
        # Write the current line to the temporary file
        echo "$line" >> "$temp_file"
      fi
    done < "$config_file"

    if [[ $section_found -eq 0 ]]; then
      echo \[" $section_name "\] >> "$temp_file"
      echo "$new_line" >> "$temp_file"
    fi

    mv "$temp_file" "$config_file"
  fi
}

if [ ! -e $cert ]; then
  echo "No $cert file found"
  exit 1
fi

if ! grep -q -- "-----BEGIN CERTIFICATE-----" $cert; then
  echo "$cert is not a certificate in PEM format"
  exit 1
fi

cp -f $cert /tmp/$cert

if [ -e /etc/debian_version ]; then
  # Debian / Ubuntu
  cfg=/etc/ssl/openssl.cnf
  grep "ssl_conf\W*=\W*ssl_sect" $cfg \
    || add_line_to_section $cfg openssl_init "ssl_conf = ssl_sect"
  grep "system_default\W*=\W*system_default_sect" $cfg \
    || add_line_to_section $cfg ssl_sect "system_default = system_default_sect"
  grep "Options\W*=\W*UnsafeLegacyRenegotiation,UnsafeLegacyServerConnect" $cfg \
    || add_line_to_section $cfg system_default_sect "Options = UnsafeLegacyRenegotiation,UnsafeLegacyServerConnect"
  cp /tmp/$cert /usr/local/share/ca-certificates/$pem_cert
  /usr/sbin/update-ca-certificates
else
  # Rocky / Fedora
  cfg=/etc/crypto-policies/back-ends/opensslcnf.config
  grep "Options\W*=\W*UnsafeLegacyRenegotiation" $cfg \
    || add_line_to_section $cfg "" "Options = UnsafeLegacyRenegotiation"
  cp /tmp/$cert /etc/pki/ca-trust/source/anchors/$pem_cert
  /usr/bin/update-ca-trust
fi
