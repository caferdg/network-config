# Network configuration 

## About
Python script that generates Cisco routers' startup-config files according to network intents described in a JSON file. Useful in a network where you have several autonomous systems with different relationships (customers, peers, providers), different IGP (OSPF, RIP).

## Features
 - BGP, OSPFv3, RIPng
 - Auto IP generation following an autonomous system (AS) IP prefix
 - Local preference configuration according to relationships (customer, peer or provider) with the adjacent AS
 - OSPF metric configuration

## Execution
`python3 conf.py <intentFile> <outputDir>`

Example : 
`python3 conf.py intent.json ./output`

## Quick deployment in a GNS project
`python3 deploy.py <confFilesDir> <projectName>`

Example : 
`python3 deploy.py output my-gns-project`

## Rules
Rules for the intent file :
 - `lp-prefix` must be 112 bits (7 blocks of 16 bits)
 - For each autonomous system `ip-prefix` must be 48 bits **:: is forbidden!**

## To do
 - IPv4
