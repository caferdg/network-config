import json, os, sys

if len(sys.argv) != 3:
    print("Usage: python3 conf.py <intentFile> <outputDir>")
    exit(1)

# IMPORT NETWORK INTENT
intent = sys.argv[1]
outputPath = sys.argv[2]
f = open(intent, "r")
jsonFile = json.load(f)
f.close()
routers = jsonFile["routers"]
autoSys = jsonFile["as"]
nbRouter = len(routers)
nbAs = len(autoSys)

# PREFERENCES
lpPrefix = jsonFile["preferences"]["lp-prefix"] # must be a /112 !!
ripName = jsonFile["preferences"]["ripName"]
ospfProcess = str(jsonFile["preferences"]["ospfPid"])
asInf = dict() # dictionnary containing the ip prefix and the index of each AS
for i in range(nbAs):
    as_ = autoSys[i]
    asInf[as_["id"]] = dict(prefix = as_["ip-prefix"], index = i)

matAdj = [] # Matrice contenant les numeros des sous-reseaux entre chaque routeur, (matrice symetrique)
for k in range(0,nbRouter):
    matAdj.append([])
    for j in range(nbRouter):
        matAdj[k].append(0)

listeSousRes = [] # Liste contenant les compteurs sous-reseaux utilises pour chaque AS
for k in range(0,nbAs):
    listeSousRes.append(0)

matAdjAs = [] # Matrice contenant les prefixes des sous-reseaux entre chaque AS, (matrice symetrique)
for k in range(0,nbAs):
    matAdjAs.append([])
    for j in range(nbAs):
        matAdjAs[k].append("")

for router in routers:

    id = router["id"]
    As = router["as"]
    igp = [a["igp"] for a in autoSys if a["id"]==As][0]
    egp = [a["egp"] for a in autoSys if a["id"]==As][0]
    adj = router["adj"]
    isASBR = False
    egpNeigbors = []

    if not os.path.exists(outputPath):
        os.makedirs(outputPath)
    res = open(f"{outputPath}/i{id}_startup-config.cfg", "w")

    ## CONSTANTS
    res.write(f"version 15.2\nservice timestamps debug datetime msec\nservice timestamps log datetime msec\nhostname R{id}\nboot-start-marker\nboot-end-marker\nno aaa new-model\nno ip icmp rate-limit unreachable\nip cef\nno ip domain lookup\nipv6 unicast-routing\nipv6 cef\nmultilink bundle-name authenticated\nip tcp synwait-time 5\n")
    res.write("!\n!\n!\n!\n!\n")

    ## LOOPBACK
    res.write(f"interface Loopback0\n no ip address\n ipv6 address {lpPrefix}{id}/128\n ipv6 enable\n")
    if(igp == "rip"):
        res.write(f" ipv6 rip {ripName} enable\n")
    if(igp == "ospf"):
        res.write(f" ipv6 ospf {ospfProcess} area 0\n")
    res.write("!\n")
    
    ## PHYSICAL INTERFACES
    for adj in router["adj"]:
        neighbID = adj["neighbor"]
        neighbAs = [router["as"] for router in routers if router["id"]==neighbID][0]
        preferedAs = As # used for choosing the ip prefixes (either As or neighbAs)
        asInd = asInf[As]["index"]
        neighbAsInd = asInf[neighbAs]["index"]

        for link in adj["links"]:

            ## IP GENERATION
            if str(link["protocol-type"]) == "igp": # routeur a l'interieur de l'AS (pas ASBR)
                ip = asInf[As]["prefix"]
            if str(link["protocol-type"]) == "egp": # routeur en bordure d'AS
                isASBR = True
                if matAdjAs[asInd][neighbAsInd] == "" and matAdjAs[neighbAsInd][asInd]=="": # adjacence inter AS pas encore initialise
                    ip = asInf[preferedAs]["prefix"]
                    matAdjAs[asInd][neighbAsInd], matAdjAs[neighbAsInd][asInd] = ip, ip
                else : # adjacence inter AS connue
                    ip = matAdjAs[asInd][neighbAsInd]

            if matAdj[id-1][neighbID-1] == 0 and matAdj[neighbID-1][id-1]==0: # sous reseau pas encore initialise
                listeSousRes[asInf[preferedAs]["index"]] += 1
                matAdj[id-1][neighbID-1], matAdj[neighbID-1][id-1] = listeSousRes[asInf[preferedAs]["index"]], listeSousRes[asInf[preferedAs]["index"]]
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
            res.write(f" ipv6 address {ip}/64\n ipv6 enable\n")

            if str(link["protocol-type"]) == "igp" :
                if igp == "rip":
                    res.write(f" ipv6 rip {ripName} enable\n")
                if igp == "ospf":
                    res.write(f" ipv6 ospf {ospfProcess} area 0\n")
            
            res.write("!\n")
    
    ## EGP
    if egp == "bgp":
        res.write(f"router bgp {As}\n")
        res.write(f" bgp router-id {id}.{id}.{id}.{id}\n")
        res.write(" bgp log-neighbor-changes\n no bgp default ipv4-unicast\n")

        if isASBR :
            for ebgpNeighb in egpNeigbors:
                ipNeighb = ebgpNeighb.split()[0]
                asNeighb = ebgpNeighb.split()[1]
                res.write(f" neighbor {ipNeighb} remote-as {asNeighb}\n")

        for routerID in [router["id"] for router in routers if router["as"]==As]:
            if routerID != id:
                res.write(f" neighbor {lpPrefix}{routerID} remote-as {As}\n")
                res.write(f" neighbor {lpPrefix}{routerID} update-source Loopback0\n")

        res.write(" !\n address-family ipv4\n exit-address-family\n !\n")
        res.write(" address-family ipv6\n")

        if isASBR :
            res.write("  redistribute connected\n")
            if(igp == "rip"):
                res.write(f"  redistribute rip {ripName}\n")
            if(igp == "ospf"):
                res.write(f"  redistribute ospf {ospfProcess}\n")
            res.write("  network " + asInf[As]["prefix"] + ":/48\n")
            for ebgpNeighb in egpNeigbors:
                res.write(f"  neighbor {ebgpNeighb.split()[0]} activate\n")

        for routerID in [router["id"] for router in routers if router["as"]==As]:
            if routerID != id:
                res.write(f"  neighbor {lpPrefix}{routerID} activate\n")
        
        res.write(" exit-address-family\n!\n")

    
    res.write("ip forward-protocol nd\nno ip http server\nno ip http secure-server\n!\n")

    ## IGP
    if(igp == "rip"):
        res.write(f"ipv6 router rip {ripName}\n redistribute connected\n")
    if(igp == "ospf"):
        res.write(f"ipv6 router ospf {ospfProcess}\n router-id {id}.{id}.{id}.{id}\n")
        if isASBR: # ??
            res.write(" redistribute connected\n")

    res.write("!\n")

    res.write("control-plane\nline con 0\n exec-timeout 0 0\n privilege level 15\n logging synchronous\n stopbits 1\nline aux 0\n exec-timeout 0 0\n privilege level 15\n logging synchronous\n stopbits 1\nline vty 0 4\n login\n!\nend")
    
    res.close()
    
print(f"Done, {nbRouter} configuration files generated in {outputPath} !")
