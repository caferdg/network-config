# scripting-routage

## A propos
Script Python permettant de générer les fichiers de configurations Cisco en fonction d'un fichier d'intentions décrivant les interactions entre les routeurs.


## Execution
Pour générer les fichiers de config Cisco :
`python3 conf.py <intentFile> <outputDirPath>`

Exemple : 
`python3 conf.py intent.json ./output`

## Règles
Règles pour le fichier d'intentions :
 - "lp-prefix" doit être une adresse à 112 bits (7 blocs de 16 bits)
 - "ip-prefix" doit être une adresse à 32 bits, **le :: n'est pas toléré ici !**
