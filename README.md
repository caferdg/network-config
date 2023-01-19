# scripting-routage

## A propos
Python script that generates Cisco routers' startup-config files according to network intents described in a json file.


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
 - "lp-prefix" must be 112 bits (7 blocks of 16 bits)
 - For each autonomous system "ip-prefix" must be 48 bits **:: is forbidden!**

## To do
 - telnet 
 - ebgp with a stranger client (ip address, interface, neighbor's as)
 - OSPF metrics
 - BGP policies (local_pref, filters)
