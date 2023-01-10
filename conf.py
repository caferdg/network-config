import json

f = open("conf.json", "r")
jsonFile = json.load(f)
routers = jsonFile["routers"]
f.close()

nbRouter = len(routers)
nbAs = len(jsonFile["as"])

matAdj = [] # Matrice contenant les numeros des sous-reseaux entre chaque routeur, (matrice symetrique)
for k in range(0,nbRouter):
    matAdj.append([])
    for j in range(nbRouter):
        matAdj[k].append(0)

listeSousRes = [] # Liste contenant les compteurs sous-reseaux utilises pour chaque AS
for k in range(0,nbAs):
    listeSousRes.append(0)



for router in routers:

    id = router["id"]
    igp = router["int-protocol"]
    egp = router["border-protocol"]
    adj = router["adj"]
    As = router["as"]

    result = open("i"+ str(id) + "_startup-config.cfg", "w")

    result.write("version 15.2\nservice timestamps debug datetime msec\nservice timestamps log datetime msec\nhostname R"+str(id)+"\nboot-start-marker\nboot-end-marker\nno aaa new-model\nno ip icmp rate-limit unreachable\nip cef\nno ip domain lookup\nipv6 unicast-routing\nipv6 cef\nmultilink bundle-name authenticated\nip tcp synwait-time 5\n")
    result.write("!\n!\n!\n!\n!\n")

    result.write("interface Loopback0\n no ip address\n ipv6 address 2001::"+str(id)+"/128\n ipv6 enable\n")

    if(igp == "rip"):
        result.write(" ipv6 rip ripng enable\n")
    else:
        result.write(" ipv6 ospf 1 area 0\n")
    result.write("!\n")
    

    for adj in router["adj"]:
        neighbID = adj["neighbor"]

        for link in adj["links"]:
            if(str(link["protocol-type"]) == "igp"): # routeur a l'interieur de l'AS (pas en bordure)
                ip = "2001:"+str(As)+"00:"+str(As)+"00:"
                if (matAdj[id-1][neighbID-1] == 0 and matAdj[neighbID-1][id-1]==0): # sous reseau pas encore initialise
                    listeSousRes[As-1] += 1
                    matAdj[id-1][neighbID-1], matAdj[neighbID-1][id-1] = listeSousRes[As-1], listeSousRes[As-1]
                    ip += str(matAdj[id-1][neighbID-1]) + "::1"
                else: # sous reseau deja cree
                    ip += str(matAdj[id-1][neighbID-1]) + "::2"
            else: # routeur en bordure d'AS
                print("en bordure")
            result.write("interface " + str(link["interface"]) + "\n")
            result.write(" no ip address\n")
            if str(link["interface"]).startswith("FastEthernet") :
                result.write(" duplex full\n")
            if str(link["interface"]).startswith("GigabitEthernet") :
                result.write(" negotiation auto\n")
            result.write(" ipv6 address " + ip +"/64\n ipv6 enable\n")

            if str(link["protocol-type"]) == "igp" :
                if igp == "rip":
                    result.write(" ipv6 rip ripng enable\n")
                if igp == "ospf":
                    result.write(" ipv6 ospf 1 area 0\n")
            
            result.write("!\n")
                    