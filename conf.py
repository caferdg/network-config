import json

# PREFERENCES
lpPrefix = "2003::"
ripName = "ripng"
ospfProcess = str(1)

# IMPORT NETWORK INTENT
f = open("intent.json", "r")
jsonFile = json.load(f)
f.close()
routers = jsonFile["routers"]

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

matAdjAs = [] # Matrice contenant les numeros d'adjacence entre AS
for k in range(0,nbAs):
    matAdjAs.append([])
    for j in range(nbAs):
        matAdjAs[k].append(0)

nbAdjAs = 0 # nombre d'adjacence entre AS

routersInAs = [] # liste des routeurs presents dans chaque AS
for As in jsonFile["as"]:
    routersInAs.append([])
    routersInAs[As-1] = [router["id"] for router in routers if router["as"]==As]

for router in routers:

    id = router["id"]
    igp = router["int-protocol"]
    egp = router["border-protocol"]
    As = router["as"]
    adj = router["adj"]
    isASBR = False
    egpNeigbors = []

    res = open("i"+ str(id) + "_startup-config.cfg", "w")

    ## CONSTANTS
    res.write("version 15.2\nservice timestamps debug datetime msec\nservice timestamps log datetime msec\nhostname R"+str(id)+"\nboot-start-marker\nboot-end-marker\nno aaa new-model\nno ip icmp rate-limit unreachable\nip cef\nno ip domain lookup\nipv6 unicast-routing\nipv6 cef\nmultilink bundle-name authenticated\nip tcp synwait-time 5\n")
    res.write("!\n!\n!\n!\n!\n")

    ## LOOPBACK
    res.write("interface Loopback0\n no ip address\n ipv6 address "+lpPrefix+str(id)+"/128\n ipv6 enable\n")
    if(igp == "rip"):
        res.write(" ipv6 rip "+ripName+" enable\n")
    if(igp == "ospf"):
        res.write(" ipv6 ospf "+ospfProcess+" area 0\n")
    res.write("!\n")
    
    ## PHYSICAL INTERFACES
    for adj in router["adj"]:
        neighbID = adj["neighbor"]
        neighbAs = [router["as"] for router in routers if router["id"]==neighbID][0]

        for link in adj["links"]:

            ## IP GENERATION
            if str(link["protocol-type"]) == "igp": # routeur a l'interieur de l'AS (pas ASBR)
                bloc = As
            if str(link["protocol-type"]) == "egp": # routeur en bordure d'AS
                isASBR = True
                if matAdjAs[As-1][neighbAs-1] == 0 and matAdjAs[neighbAs-1][As-1]==0: # adjacence inter AS pas encore initialise
                    nbAdjAs += 1
                    bloc = nbAs + nbAdjAs
                    matAdjAs[As-1][neighbAs-1], matAdjAs[neighbAs-1][As-1] = bloc, bloc
                    listeSousRes.append(0)
                else : # adjacence inter AS connue
                    bloc = matAdjAs[As-1][neighbAs-1]

            ip = "2001:"+str(bloc)+"00:"+str(bloc)+"00:"

            if matAdj[id-1][neighbID-1] == 0 and matAdj[neighbID-1][id-1]==0: # sous reseau pas encore initialise
                listeSousRes[bloc-1] += 1
                matAdj[id-1][neighbID-1], matAdj[neighbID-1][id-1] = listeSousRes[bloc-1], listeSousRes[bloc-1]
                ip += str(matAdj[id-1][neighbID-1]) + "::1"
                if isASBR and str(link["protocol-type"]) == "egp":
                    egpNeigbors.append(ip[:-1] + "2" + " " + str(neighbAs))
            else: # sous reseau deja cree
                ip += str(matAdj[id-1][neighbID-1]) + "::2"
                if isASBR and str(link["protocol-type"]) == "egp":
                    egpNeigbors.append(ip[:-1] + "1" + " "+ str(neighbAs))

            # INTERFACE
            res.write("interface " + str(link["interface"]) + "\n")
            res.write(" no ip address\n")
            if str(link["interface"]).startswith("FastEthernet") :
                res.write(" duplex full\n")
            if str(link["interface"]).startswith("GigabitEthernet") :
                res.write(" negotiation auto\n")
            res.write(" ipv6 address " + ip +"/64\n ipv6 enable\n")

            if str(link["protocol-type"]) == "igp" :
                if igp == "rip":
                    res.write(" ipv6 rip "+ripName+" enable\n")
                if igp == "ospf":
                    res.write(" ipv6 ospf "+ospfProcess+" area 0\n")
            
            res.write("!\n")
    
    ## EGP
    if egp == "bgp":
        res.write("router bgp " + str(As) + "\n")
        res.write(" bgp router-id "+ str(id)+"."+str(id)+"."+str(id)+"."+str(id) + "\n")
        res.write(" bgp log-neighbor-changes\n no bgp default ipv4-unicast\n")

        if isASBR :
            for ebgpNeighb in egpNeigbors:
                ipNeighb = ebgpNeighb.split()[0]
                asNeighb = ebgpNeighb.split()[1]
                res.write(" neighbor "+ipNeighb +" remote-as "+ asNeighb+"\n")

        for routerID in routersInAs[As-1]:
            if routerID != id:
                res.write(" neighbor "+lpPrefix+ str(routerID) +" remote-as "+ str(As)+"\n")
                res.write(" neighbor "+lpPrefix+ str(routerID) +" update-source Loopback0\n")

        res.write(" !\n address-family ipv4\n exit-address-family\n !\n")
        res.write(" address-family ipv6\n")

        if isASBR :
            if(igp == "rip"):
                res.write("  redistribute rip "+ripName+"\n")
            if(igp == "ospf"):
                res.write("  redistribute ospf "+ospfProcess+"\n")
            res.write("  network 2001:"+str(As)+"00:"+str(As)+"00::/48\n")
            for ebgpNeighb in egpNeigbors:
                res.write("  neighbor " + ebgpNeighb.split()[0] + " activate\n")

        for routerID in routersInAs[As-1]:
            if routerID != id:
                res.write("  neighbor "+lpPrefix+ str(routerID) +" activate\n")
        
        res.write(" exit-address-family\n!\n")

    
    res.write("ip forward-protocol nd\nno ip http server\nno ip http secure-server\n!\n")

    ## IGP
    if(igp == "rip"):
        res.write("ipv6 router rip "+ripName+"\n redistribute connected\n")
    if(igp == "ospf"):
        res.write("ipv6 router ospf "+ospfProcess+"\n router-id "+str(id)+"."+str(id)+"."+str(id)+"."+str(id)+"\n")
        if isASBR: # ??
            res.write(" redistribute connected\n")

    res.write("!\n")

    res.write("control-plane\nline con 0\n exec-timeout 0 0\n privilege level 15\n logging synchronous\n stopbits 1\nline aux 0\n exec-timeout 0 0\n privilege level 15\n logging synchronous\n stopbits 1\nline vty 0 4\n login\n!\nend")
    
    res.close()
