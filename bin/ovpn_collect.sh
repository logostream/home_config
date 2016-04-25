#!/bin/bash
cd /etc/openvpn
GROUP=stream
USER=stream
HOME=/home/$USER
HOST_ID=$1
mkdir -p $HOME/keys
rm $HOME/keys/*
cp easy-rsa/keys/client_${HOST_ID}_foo.crt easy-rsa/keys/client_${HOST_ID}_foo.key easy-rsa/keys/ca.crt client-templates/client_foo.conf $HOME/keys
chown $GROUP:$USER $HOME/keys/*
