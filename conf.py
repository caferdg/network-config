import json

f = open("conf.json", "r")
jsonFile = json.load(f)
routers = jsonFile["routers"]
f.close()

nbRouter = len(routers)
nbAs = len(jsonFile["as"])
matAdjacence = [] # Matrice contenant les numeros des sous-reseaux entre chaque routeur, (matrice symetrique)
for k in range(0,nbRouter):
    matAdjacence.append([])
    for j in range(0,nbRouter):
        matAdjacence[k].append(0)


for router in routers:

    id = router["id"]
    igp = router["int-protocol"]
    egp = router["border-protocol"]
    adj = router["adj"]

    result = open("i"+ str(id) + "_startup-config.cfg", "w")

    result.write("version 15.2\nservice timestamps debug datetime msec\nservice timestamps log datetime msec\nhostname R"+str(id)+"\nboot-start-marker\nboot-end-marker\nno aaa new-model\nno ip icmp rate-limit unreachable\nip cef\nno ip domain lookup\nipv6 unicast-routing\nipv6 cef\nmultilink bundle-name authenticated\nip tcp synwait-time 5\n")
    result.write("!\n!\n!\n!\n!\n")

    result.write("interface Loopback0\n no ip address\nipv6 address 2001::"+str(id)+"/128\n ipv6 enable\n")

    if(egp == "rip"):
        result.write(" ipv6 rip ripng enable\n")
    else:
        result.write(" ipv6 ospf 1 area 0\n")

    

    for adj in router["adj"]:
        neighbID = adj["neighbor"]

